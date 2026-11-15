# -*- coding: utf-8 -*-
"""
Plot one fixation heatmap per stimulus (trial), averaged over all participants.

For every participant, each fixation on the stimulus is drawn as a 2D Gaussian
(sigma in degrees of visual angle) weighted by its duration. The map of each
participant is normalised to a sum of 1, so every participant contributes
equally, no matter how many or how long their fixations are. The maps of all
participants are then averaged and drawn on top of the stimulus.

Input:  output/allfixations.txt (from detect_fixations.py) and the stimulus
        images in the folder 'stimuli'.
Output: one png per stimulus in the folder 'heatmaps'.

Requirements: numpy, pandas, Pillow, matplotlib (colormap only)
"""

import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from matplotlib import colormaps

# File with fixations generated with the I2MC (detect_fixations.py)
FIXATION_FILE = Path('output') / 'allfixations.txt'

# Folder with the stimulus images; file names must match the 'trial' column
STIMULUS_FOLDER = Path('stimuli')

OUTPUT_FOLDER = Path('heatmaps')

# True: every participant contributes equally (map per participant sums to 1).
# False: all fixations are pooled, so participants with more fixation time
# (e.g. less data loss) weigh more.
NORMALISE_PER_PARTICIPANT = True

# Only use the first part of each trial, in ms (e.g. 2000). Fixations that
# start after this time are left out, and fixations that continue past it only
# count with the part before it. None = use the whole trial.
TIME_WINDOW_MS = None

# Number of stimuli processed in parallel. None = all CPU threads,
# 1 = no parallel processing. When running from Spyder/Jupyter on Windows,
# parallel processing may not work; then set N_WORKERS = 1.
N_WORKERS = None

# Width (standard deviation) of the Gaussian around each fixation, in degrees
# of visual angle. The screen geometry converts it to pixels; use the same
# values as in detect_fixations.py.
SIGMA_DEG = 1.0
SCREEN_WIDTH_CM = 52.7
SCREEN_WIDTH_PX = 1920
VIEWING_DISTANCE_CM = 63.0

COLORMAP = 'jet'        # any matplotlib colormap, e.g. 'jet', 'viridis', 'inferno'
MAX_ALPHA = 0.6         # opacity of the hottest part of the overlay (0-1)
THRESHOLD = 0.05        # parts below this fraction of the maximum are not drawn

def deg_to_px(deg):
    """Convert degrees of visual angle to pixels (at the screen centre)."""
    size_cm = 2 * VIEWING_DISTANCE_CM * math.tan(math.radians(deg) / 2)
    return size_cm * SCREEN_WIDTH_PX / SCREEN_WIDTH_CM


def fixation_weights(fix, time_window_ms=None, normalise=True):
    """Return x, y, weight of the fixations to use and the number of participants.

    The weight is the fixation duration in ms; with a time window only the part
    of a fixation before the end of the window counts. With normalise=True the
    weights of each participant sum to 1.
    """
    fix = fix.dropna(subset=['xpos', 'ypos'])
    if time_window_ms is None:
        w = fix['dur'].to_numpy(dtype=float)
    else:
        end = np.minimum(fix['endT'].to_numpy(dtype=float), time_window_ms)
        w = np.clip(end - fix['startT'].to_numpy(dtype=float), 0, None)

    keep = w > 0
    fix, w = fix[keep], w[keep]
    if normalise:
        totals = pd.Series(w, index=fix.index).groupby(fix['participant']).transform('sum')
        w = w / totals.to_numpy()

    x = fix['xpos'].to_numpy(dtype=float)
    y = fix['ypos'].to_numpy(dtype=float)
    return x, y, w, fix['participant'].nunique()


def gaussian_heatmap(x, y, w, width, height, sigma_px):
    """Sum of 2D Gaussians (height x width), one per fixation, weighted by w."""
    # A 2D Gaussian is the product of a Gaussian in x and one in y, so the sum
    # of all fixations is a single matrix product: (H x N) @ (N x W).
    # Pixel centres are at +0.5 (pixel (0, 0) covers 0 <= x < 1).
    gx = np.exp(-0.5 * ((np.arange(width) + 0.5)[None, :] - x[:, None]) ** 2 / sigma_px ** 2)
    gy = np.exp(-0.5 * ((np.arange(height) + 0.5)[:, None] - y[None, :]) ** 2 / sigma_px ** 2)
    norm = 2 * math.pi * sigma_px ** 2
    return (gy * (w / norm)[None, :]) @ gx


def overlay_gaussian(stimulus, heat, cmap_name, max_alpha, threshold):
    """Draw the heatmap on the stimulus with a soft edge; return RGB image."""
    peak = heat.max()
    if peak <= 0:
        return stimulus.convert('RGB')
    h = heat / peak

    rgba = colormaps[cmap_name](h)                    # float RGBA, 0-1
    # Transparent below the threshold, fading in to max_alpha just above it
    rgba[..., 3] = np.clip((h - threshold) / threshold, 0, 1) * max_alpha
    overlay = Image.fromarray((rgba * 255).round().astype(np.uint8), 'RGBA')

    base = stimulus.convert('RGBA')
    return Image.alpha_composite(base, overlay).convert('RGB')


def process_stimulus(trial, fix, stimulus_path, out_path, normalise,
                     time_window_ms, sigma_px):
    """Make and save the heatmap of one stimulus. Returns n participants."""
    with Image.open(stimulus_path) as stimulus:
        stimulus.load()
    width, height = stimulus.size

    x, y, w, n = fixation_weights(fix, time_window_ms, normalise)
    if n == 0:
        return trial, 0, None

    heat = gaussian_heatmap(x, y, w, width, height, sigma_px)
    image = overlay_gaussian(stimulus, heat, COLORMAP, MAX_ALPHA, THRESHOLD)

    out_path = out_path.with_name(f'{out_path.stem}_n{n}.png')
    image.save(out_path)
    return trial, n, out_path


def main():
    start_time = time.perf_counter()

    normalise = NORMALISE_PER_PARTICIPANT

    df = pd.read_csv(FIXATION_FILE, sep='\t')
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    sigma_px = deg_to_px(SIGMA_DEG)
    print('Each participant weighs equally' if normalise else 'All fixations pooled')
    print(f'Gaussian sigma: {SIGMA_DEG} deg = {sigma_px:.1f} px')

    suffix = '' if TIME_WINDOW_MS is None else f'_{TIME_WINDOW_MS}ms'

    jobs = []
    for trial, fix in df.groupby('trial', sort=True):
        stimulus_path = STIMULUS_FOLDER / trial
        if not stimulus_path.is_file():
            print(f'Warning: stimulus {stimulus_path} not found, skipped')
            continue
        out_path = OUTPUT_FOLDER / f'heatmap_{Path(trial).stem}{suffix}.png'
        jobs.append((trial, fix, stimulus_path, out_path))

    n_workers = N_WORKERS if N_WORKERS is not None else (os.cpu_count() or 1)
    n_workers = max(1, min(n_workers, len(jobs)))
    print(f'Processing {len(jobs)} stimuli with {n_workers} worker(s)')

    args = list(zip(*jobs)) if jobs else [[]] * 4
    fixed = [[normalise] * len(jobs),
             [TIME_WINDOW_MS] * len(jobs), [sigma_px] * len(jobs)]

    if n_workers > 1:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            results = list(executor.map(process_stimulus, *args, *fixed))
    else:
        results = list(map(process_stimulus, *args, *fixed))

    for i, (trial, n, path) in enumerate(results):
        if path is None:
            print(f'{i + 1}/{len(results)} {trial}: no fixations, skipped')
        else:
            print(f'{i + 1}/{len(results)} {trial}: n = {n}, saved {path}')

    elapsed = time.perf_counter() - start_time
    minutes, seconds = divmod(elapsed, 60)
    print(f'Total time: {int(minutes)} min {seconds:.1f} s')


if __name__ == '__main__':
    main()
