# -*- coding: utf-8 -*-
"""
Make one heatmap video per stimulus (trial), averaged over all participants.

Every frame shows where the participants looked around that moment of the
trial. The method is the same as in plot_heatmap.py: each gaze point is a 2D
Gaussian (sigma in degrees of visual angle) weighted by how long it lasted,
and every participant contributes equally.

Two sources (SOURCE):

'samples' (default)
    The raw gaze samples in the folder 'trials' (from extract_trial_data.py),
    mean of both eyes. The heatmap changes in every frame and follows the
    eyes, including saccades.
'fixations'
    The fixations in output/allfixations.txt. A fixation does not move, so
    the heatmap only changes when a participant moves to a next fixation.

Two modes (MODE):

'window' (default)
    Each frame shows the fixations in the last WINDOW_MS before that moment.
    A participant adds the fraction of the window spent on each fixation, so
    the map shows where the group looked "just now".
'cumulative'
    Each frame shows everything from the start of the trial up to that moment,
    like plot_heatmap.py with TIME_WINDOW_MS set to that moment.

The colour scale is fixed per video (the maximum over all frames), so colours
can be compared between frames. Time and number of participants are shown in
the top-left corner.

Input:  the trial data in 'trials' (SOURCE = 'samples') or
        output/allfixations.txt (SOURCE = 'fixations'; for the list of
        stimuli and participants it is always used), and the stimulus images
        in the folder 'stimuli'.
Output: one mp4 per stimulus in the folder 'heatmap_videos'.

Requirements: numpy, pandas, Pillow, matplotlib (colormap only), OpenCV
"""

import math
import os
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

# One BLAS thread per process. The matrices per frame are small, and several
# stimuli run in parallel (N_WORKERS); with the default of one BLAS thread per
# CPU thread the threads mostly wait for each other (e.g. 163 s instead of
# 10 s for 11 stimuli on 28 CPU threads). Must be set before numpy is
# imported; a value set on the command line is kept.
for _variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(_variable, '1')

import numpy as np  # noqa: E402
import pandas as pd
from PIL import Image

try:
    import cv2
except ImportError:
    raise ImportError('OpenCV not found. pip install opencv-python')

# File with fixations generated with the I2MC (detect_fixations.py)
FIXATION_FILE = Path('output') / 'allfixations.txt'

# Folder with the trial data, one folder per participant
# (extract_trial_data.py)
TRIALS_FOLDER = Path('trials')

# 'samples': raw gaze samples, the heatmap changes in every frame;
# 'fixations': fixations, the heatmap changes from fixation to fixation
SOURCE = 'samples'

# Screen resolution of the gaze data in pixels (as opt['xres'], opt['yres']
# in detect_fixations.py), used to convert Titta's normalised coordinates
SCREEN_RES = (1920, 1080)

# Folder with the stimulus images; file names must match the 'trial' column
STIMULUS_FOLDER = Path('stimuli')

OUTPUT_FOLDER = Path('heatmap_videos')

# 'window': gaze in the last WINDOW_MS; 'cumulative': all gaze so far.
# With SOURCE = 'samples' a short window (e.g. 100 ms) follows the eyes
# closely; a longer one (e.g. 500 ms) gives a calmer picture.
MODE = 'window'
WINDOW_MS = 100

# Frames per second of the video. The video plays in real time.
FPS = 30

# Video codec (FourCC). 'avc1' (H.264) gives small files that play almost
# everywhere, but needs an OpenCV built with an H.264 encoder (e.g. Debian's
# python3-opencv; the pip wheels often have none). If it cannot be opened,
# FALLBACK_CODEC is used instead. 'mp4v' (MPEG-4 Part 2) always works with
# OpenCV, but gives larger files that some players (e.g. browsers) cannot play.
VIDEO_CODEC = 'avc1'
FALLBACK_CODEC = 'mp4v'

# Size of the video relative to the stimulus image, e.g. 0.5 for half the
# width and height (four times fewer pixels, much faster)
OUTPUT_SCALE = 1.0

# Width (standard deviation) of the Gaussian around each fixation, in degrees
# of visual angle. Use the same screen geometry as in detect_fixations.py.
SIGMA_DEG = 1.0
SCREEN_WIDTH_CM = 52.7
SCREEN_WIDTH_PX = 1920
VIEWING_DISTANCE_CM = 63.0

COLORMAP = 'jet'        # any matplotlib colormap, e.g. 'jet', 'viridis', 'inferno'
MAX_ALPHA = 0.6         # opacity of the hottest part of the overlay (0-1)
THRESHOLD = 0.05        # parts below this fraction of the maximum are not drawn

# Number of stimuli processed in parallel. None = all CPU threads,
# 1 = no parallel processing. When running from Spyder/Jupyter on Windows,
# parallel processing may not work; then set N_WORKERS = 1.
N_WORKERS = None


def deg_to_px(deg):
    """Convert degrees of visual angle to pixels (at the screen centre)."""
    size_cm = 2 * VIEWING_DISTANCE_CM * math.tan(math.radians(deg) / 2)
    return size_cm * SCREEN_WIDTH_PX / SCREEN_WIDTH_CM


def frame_weights(start, end, participant, n_participants, t, mode, window_ms):
    """Weight of every gaze point (fixation or sample) in the frame at time t (ms).

    A sample is a gaze point that lasts one sample interval.
    window:     the part of the point in [t - window_ms, t], as a fraction
                of window_ms, so each participant adds at most 1
    cumulative: the part of the point in [0, t], normalised so that each
                participant who has looked somewhere adds exactly 1
    Divided by the number of participants, so the map is a mean over them.
    """
    t0 = t - window_ms if mode == 'window' else 0.0
    w = np.clip(np.minimum(end, t) - np.maximum(start, t0), 0, None)
    if mode == 'window':
        w = w / window_ms
    else:
        totals = np.bincount(participant, weights=w)
        w = np.divide(w, totals[participant], out=np.zeros_like(w),
                      where=totals[participant] > 0)
    return w / n_participants


def heat_frame(x, y, w, width, height, sigma_px, step):
    """Sum of the Gaussians of the points with a weight > 0, as height x width.

    The points are spread over a grid of every step-th pixel (bilinear, each
    point over its four nearest grid points), the grid is smoothed with the
    Gaussian (two small matrix products) and scaled up smoothly to full size.
    The Gaussian is much wider than step (about 10 grid points per sigma), so
    this looks the same as summing the Gaussians at every pixel, and the time
    per frame does not depend on the number of points (thousands of samples).
    The grid extends 4 sigma beyond the image, so gaze just outside the image
    still counts with its tail.
    """
    active = np.flatnonzero(w)
    if len(active) == 0:
        return np.zeros((height, width), dtype=np.float32)

    margin = int(math.ceil(4 * sigma_px / step)) + 1
    cw = -(-width // step) + 2 * margin
    ch = -(-height // step) + 2 * margin

    # Grid coordinates: grid point i has its centre at (i - margin + 0.5) * step
    gx = x[active] / step - 0.5 + margin
    gy = y[active] / step - 0.5 + margin
    wa = w[active]
    inside = (gx >= 0) & (gx < cw - 1) & (gy >= 0) & (gy < ch - 1)
    gx, gy, wa = gx[inside], gy[inside], wa[inside]
    ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - ix, gy - iy
    grid = np.zeros((ch, cw))
    for dy, wy in ((0, 1 - fy), (1, fy)):
        for dx, wx in ((0, 1 - fx), (1, fx)):
            np.add.at(grid, (iy + dy, ix + dx), wa * wy * wx)

    # Smooth with the Gaussian: Ky @ grid @ Kx (separable)
    d = np.arange(-(max(cw, ch)), max(cw, ch) + 1) * step
    k = np.exp(-0.5 * d ** 2 / sigma_px ** 2)
    c = max(cw, ch)
    kx = k[c + np.arange(cw)[:, None] - np.arange(cw)[None, :]]
    ky = k[c + np.arange(ch)[:, None] - np.arange(ch)[None, :]]
    smooth = (ky @ grid @ kx / (2 * math.pi * sigma_px ** 2)).astype(np.float32)

    # Scale up the part over the image plus one grid point on each side, so
    # the interpolation near the edges does not depend on cv2.resize borders
    iw, ih = -(-width // step), -(-height // step)
    part = smooth[margin - 1:margin + ih + 1, margin - 1:margin + iw + 1]
    if step == 1:
        return part[1:1 + height, 1:1 + width]
    full = cv2.resize(part, (part.shape[1] * step, part.shape[0] * step),
                      interpolation=cv2.INTER_LINEAR)
    return full[step:step + height, step:step + width]


def exact_heat(x, y, w, width, height, sigma_px):
    """Reference: the Gaussians summed at every pixel (slow; for testing)."""
    a = np.flatnonzero(w)
    gx = np.exp(-0.5 * ((np.arange(width) + 0.5)[None, :] - x[a][:, None]) ** 2 / sigma_px ** 2)
    gy = np.exp(-0.5 * ((np.arange(height) + 0.5)[:, None] - y[a][None, :]) ** 2 / sigma_px ** 2)
    return (gy * (w[a] / (2 * math.pi * sigma_px ** 2))[None, :]) @ gx


def load_samples(trials_folder, trial, participants, screen_res):
    """Raw gaze samples of one stimulus, as a DataFrame like the fixation file.

    Each sample becomes a point from its time to the next sample time, at the
    mean position of both eyes (or the one valid eye).
    """
    import import_funcs as imp
    parts = []
    for participant in participants:
        path = Path(trials_folder) / str(participant) / f'{trial}.tsv'
        if not path.is_file():
            continue
        data = imp.Titta(str(path), list(screen_res))
        if len(data) == 0:
            continue
        t = data['time'].to_numpy(dtype=float)
        dt = np.median(np.diff(t)) if len(t) > 1 else 0.0
        with warnings.catch_warnings():
            # Samples without any valid eye give NaN (and a warning); they
            # are dropped later
            warnings.simplefilter('ignore', category=RuntimeWarning)
            x = np.nanmean(data[['L_X', 'R_X']].to_numpy(dtype=float), axis=1)
            y = np.nanmean(data[['L_Y', 'R_Y']].to_numpy(dtype=float), axis=1)
        parts.append(pd.DataFrame({'participant': participant, 'startT': t,
                                   'endT': t + dt, 'xpos': x, 'ypos': y}))
    if not parts:
        return pd.DataFrame(columns=['participant', 'startT', 'endT', 'xpos', 'ypos'])
    return pd.concat(parts, ignore_index=True)


def colour_lut(cmap_name):
    """Colormap as 256 x 3 uint8 RGB lookup table."""
    from matplotlib import colormaps
    return (colormaps[cmap_name](np.linspace(0, 1, 256))[:, :3] * 255).round().astype(np.uint8)


def draw_frame(base, heat, vmax, lut, max_alpha, threshold):
    """Blend the heatmap over the stimulus (RGB uint8) with a soft edge.

    Only pixels above the threshold change, so only those are computed.
    """
    frame = base.copy()
    if vmax <= 0:
        return frame
    h = heat / vmax
    mask = h > threshold
    if not mask.any():
        return frame
    hm = np.minimum(h[mask], 1)
    colour = lut[(hm * 255).astype(np.uint8)].astype(np.float32)
    alpha = (np.clip((hm - threshold) / threshold, 0, 1) * max_alpha)[:, None]
    frame[mask] = (frame[mask] * (1 - alpha) + colour * alpha).round().astype(np.uint8)
    return frame


def put_label(frame_bgr, text):
    """Write text with a dark background in the top-left corner."""
    scale = max(frame_bgr.shape[0] / 1080, 0.4)
    font, thick = cv2.FONT_HERSHEY_SIMPLEX, max(1, round(2 * scale))
    (tw, th), base = cv2.getTextSize(text, font, scale, thick)
    pad = round(10 * scale)
    cv2.rectangle(frame_bgr, (0, 0), (tw + 2 * pad, th + base + 2 * pad), (0, 0, 0), -1)
    cv2.putText(frame_bgr, text, (pad, pad + th), font, scale, (255, 255, 255),
                thick, cv2.LINE_AA)


def make_video(trial, fix, stimulus_path, out_path, settings):
    """Make and save the heatmap video of one stimulus. Returns n participants."""
    (source, trials_folder, screen_res, mode, window_ms, fps, scale, sigma_px,
     cmap, max_alpha, threshold, codecs) = settings

    if source == 'samples':
        fix = load_samples(trials_folder, trial, fix['participant'].unique(), screen_res)
    # Points without a position (e.g. both eyes lost) do not count; that
    # participant then simply adds less to the frame
    fix = fix.dropna(subset=['xpos', 'ypos', 'startT', 'endT'])
    if len(fix) == 0:
        return trial, 0, None, None

    with Image.open(stimulus_path) as img:
        stimulus = img.convert('RGB')
    width, height = round(stimulus.width * scale), round(stimulus.height * scale)
    if (width, height) != stimulus.size:
        stimulus = stimulus.resize((width, height), Image.LANCZOS)
    width -= width % 2          # most video codecs need even sizes
    height -= height % 2
    base = np.ascontiguousarray(np.asarray(stimulus, dtype=np.uint8)[:height, :width])

    codes, participants = pd.factorize(fix['participant'])
    n = len(participants)
    start = fix['startT'].to_numpy(dtype=float)
    end = fix['endT'].to_numpy(dtype=float)
    x = fix['xpos'].to_numpy(dtype=float) * scale
    y = fix['ypos'].to_numpy(dtype=float) * scale
    sigma = sigma_px * scale

    duration = end.max()
    times = np.arange(0, duration + 1000 / fps, 1000 / fps)

    # Grid of the heatmap: about 10 points per sigma
    step = max(1, int(sigma // 10))

    def heat_at(t):
        w = frame_weights(start, end, codes, n, t, mode, window_ms)
        return heat_frame(x, y, w, width, height, sigma, step)

    # Pass 1: maximum over all frames, for a fixed colour scale
    vmax = max(float(heat_at(t).max()) for t in times)

    # Pass 2: the video
    lut = colour_lut(cmap)
    for codec in codecs:
        writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*codec),
                                 float(fps), (width, height))
        if writer.isOpened():
            break
        writer.release()
    else:
        raise RuntimeError(f'Cannot write video {out_path} with codec(s) '
                           + ', '.join(codecs))
    for t in times:
        rgb = draw_frame(base, heat_at(t), vmax, lut, max_alpha, threshold)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        put_label(bgr, f'{trial}  t = {t / 1000:5.2f} s  n = {n}')
        writer.write(bgr)
    writer.release()
    return trial, n, out_path, codec


def main():
    start_time = time.perf_counter()

    if MODE not in ('window', 'cumulative'):
        raise ValueError(f"MODE must be 'window' or 'cumulative', not {MODE!r}")
    if SOURCE not in ('samples', 'fixations'):
        raise ValueError(f"SOURCE must be 'samples' or 'fixations', not {SOURCE!r}")
    if SOURCE == 'samples' and not TRIALS_FOLDER.is_dir():
        raise FileNotFoundError(f"No folder {TRIALS_FOLDER} (run extract_trial_data.py), "
                                "or set SOURCE = 'fixations'")

    df = pd.read_csv(FIXATION_FILE, sep='\t')
    for column in ('startT', 'endT'):
        if column not in df.columns:
            raise ValueError(f'No column {column!r} in {FIXATION_FILE}')
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    sigma_px = deg_to_px(SIGMA_DEG)
    print(f'Source: {SOURCE}, mode: {MODE}'
          + (f' ({WINDOW_MS} ms)' if MODE == 'window' else ''))
    print(f'Gaussian sigma: {SIGMA_DEG} deg = {sigma_px:.1f} px, '
          f'{FPS} fps, scale {OUTPUT_SCALE}')

    suffix = SOURCE + '_' + (f'window{WINDOW_MS}ms' if MODE == 'window' else 'cumulative')
    jobs = []
    for trial, fix in df.groupby('trial', sort=True):
        stimulus_path = STIMULUS_FOLDER / trial
        if not stimulus_path.is_file():
            print(f'Warning: stimulus {stimulus_path} not found, skipped')
            continue
        n = fix['participant'].nunique()
        out_path = OUTPUT_FOLDER / f'heatmap_video_{Path(trial).stem}_{suffix}_n{n}.mp4'
        jobs.append((trial, fix, stimulus_path, out_path))

    n_workers = N_WORKERS if N_WORKERS is not None else (os.cpu_count() or 1)
    n_workers = max(1, min(n_workers, len(jobs)))
    print(f'Processing {len(jobs)} stimuli with {n_workers} worker(s)')

    codecs = [VIDEO_CODEC] + ([FALLBACK_CODEC] if FALLBACK_CODEC
                              and FALLBACK_CODEC != VIDEO_CODEC else [])
    settings = (SOURCE, TRIALS_FOLDER, SCREEN_RES, MODE, WINDOW_MS, FPS,
                OUTPUT_SCALE, sigma_px, COLORMAP, MAX_ALPHA, THRESHOLD, codecs)
    args = list(zip(*jobs)) if jobs else [[]] * 4
    if n_workers > 1:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            results = list(executor.map(make_video, *args, [settings] * len(jobs)))
    else:
        results = list(map(make_video, *args, [settings] * len(jobs)))

    fallback_used = False
    for i, (trial, n, path, codec) in enumerate(results):
        if path is None:
            print(f'{i + 1}/{len(results)} {trial}: no gaze data, skipped')
        else:
            print(f'{i + 1}/{len(results)} {trial}: n = {n}, saved {path} ({codec})')
            fallback_used |= codec != VIDEO_CODEC
    if fallback_used:
        print(f'Note: codec {VIDEO_CODEC!r} is not available in this OpenCV, '
              f'used {FALLBACK_CODEC!r} instead')

    elapsed = time.perf_counter() - start_time
    minutes, seconds = divmod(elapsed, 60)
    print(f'Total time: {int(minutes)} min {seconds:.1f} s')


if __name__ == '__main__':
    main()
