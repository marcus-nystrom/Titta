# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:06:43 2022

@author: Marcus

Rewritten to process one trial (stimulus) at a time:
- the AOI images of a trial are read from disk exactly once,
- all fixations of all participants on that trial are then mapped to these
  AOIs in one vectorized lookup,
- only the AOIs of one trial (per worker) are kept in memory.
Optionally, several trials are processed in parallel (N_WORKERS).
"""

import os
import re
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from PIL import Image

# File with fixations generated with the I2MC
FIXATION_FILE = 'allfixations.txt'

# Folder with one subfolder per stimulus, containing the AOI images (png)
AOI_FOLDER = 'AOIs'

OUTPUT_FILE = 'fixation_aoi_hits.csv'

# Number of trials processed in parallel. None = use all CPU threads
# (os.cpu_count()). Set to a number to override, e.g. 16; 1 = no parallel
# processing. Memory use is roughly N_WORKERS x (AOIs of one trial).
# Note: when running from Spyder/Jupyter on Windows, parallel processing may
# not work; then set N_WORKERS = 1 or run the script from a terminal
# (python map_fixations_to_aois.py).
N_WORKERS = None

# Which pixels belong to an AOI. None = only pixels with the maximum value of
# the image (pure white), as in the original script. Set to a number from 0 to
# 255 to count every pixel brighter than this value as AOI, e.g. 127 to include
# grey anti-aliased edge pixels. For 16-bit images the value is scaled.
AOI_THRESHOLD = None

# Cumulative plots: for each trial, the percentage of participants who have
# fixated each AOI at least once, as a function of time since trial start
# (based on the 'startT' column of the fixation file). One png per trial.
PLOT_CUMULATIVE = True
CUMULATIVE_FOLDER = 'cumulative_plots'

# File format and resolution of the plots. 'png' uses PLOT_DPI; 'svg' and
# 'pdf' are vector formats that stay sharp at any size.
PLOT_FORMAT = 'png'
PLOT_DPI = 300

# Length of the time axis of the cumulative plots, in seconds.
# None: per trial up to the end of the last fixation of any participant on
#       that trial, so all data are shown.
# A number, e.g. 10: the same axis (0-10 s) for all plots, so plots of
#       different trials can be compared. First fixations after this time are
#       not shown; the lines end at this time.
CUMULATIVE_TIME_S = None

# Where the line of an AOI ends:
# 'edge':          if the AOI has a first fixation after the end of the time
#                  axis, the straight line towards it continues to the edge
#                  of the plot (at the interpolated value); otherwise the line
#                  ends at the last first fixation
# 'last_fixation': the line always ends at the last first fixation within
#                  the time axis
CUMULATIVE_CUT = 'edge'

# Number of fixations on an AOI before a participant counts as "has fixated
# the AOI" in the cumulative plots. 1 (default): at the first fixation on the
# AOI. 2: only at the second fixation on that AOI, etc. Every fixation that
# hits the AOI counts, also consecutive fixations within the AOI.
CUMULATIVE_MIN_FIXATIONS = 1

# Time to first fixation per participant, trial and AOI (used for the plots)
FIRST_FIXATION_FILE = 'aoi_first_fixation.csv'

# The lines are black; the AOIs differ by marker colour (fixed order). With
# more than 8 AOIs in a trial the colours repeat with another marker shape,
# so each AOI stays unique.
AOI_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100',
              '#e87ba4', '#008300', '#6250d6', '#e34948']
AOI_MARKERS = ['o', 's', '^', 'D', 'v']


def natural_key(text):
    """Sort key that orders numbers by value: aoi2 before aoi10.

    aoi1, aoi2, aoi10 and aoi01, aoi02, aoi10 are both sorted correctly;
    text is compared case-insensitively.
    """
    parts = re.split(r'(\d+)', text.lower())
    key = tuple((0, int(p), '') if p.isdigit() else (1, 0, p) for p in parts if p)
    return key, text


def find_aoi_files(aoi_folder):
    """Return dict trial_name -> list of AOI image paths in natural order."""
    aoi_files = {}
    for p in aoi_folder.rglob('*'):
        if p.is_file() and p.suffix.lower() == '.png':
            aoi_files.setdefault(p.parent.name, []).append(p)
    for paths in aoi_files.values():
        paths.sort(key=lambda p: natural_key(p.stem))
    return aoi_files


def read_aoi_mask(path, threshold=None):
    """Read a binary AOI image and return a boolean mask (True = inside AOI)."""
    with Image.open(path) as img:
        if img.mode == 'P':
            img = img.convert('RGBA')
        im = np.asarray(img)

    # If an RGB image, use only R-band.
    if im.ndim > 2:
        im = im[:, :, 0]

    if im.max() == im.min():
        print(f'Warning: {path} contains only one colour, AOI ignored')
        return np.zeros(im.shape, dtype=bool)

    if threshold is None:
        return im == im.max()

    # Express the threshold on the 0-255 scale of an 8-bit image
    if im.dtype == bool:
        return im.copy()
    if np.issubdtype(im.dtype, np.integer):
        scale = np.iinfo(im.dtype).max / 255
    else:
        scale = 1 / 255
    return im > threshold * scale


def map_trial(aoi_paths, x, y, threshold=None):
    """Map all fixations of one trial to its AOIs.

    Returns (hit_fixations, hit_aois, n_outside): for each hit the index of the
    fixation (into x/y) and the AOI name, plus the number of fixations outside
    the image.
    """
    # Same pixel convention as before: pixel (row, col) = (int(y), int(x))
    col = np.floor(np.asarray(x, dtype=float))
    row = np.floor(np.asarray(y, dtype=float))

    hit_fixations = []
    hit_aois = []
    outside = np.ones(len(col), dtype=bool)
    for path in aoi_paths:
        mask = read_aoi_mask(path, threshold)
        height, width = mask.shape

        # NaN coordinates compare as False, so they count as outside
        inside = (col >= 0) & (col < width) & (row >= 0) & (row < height)
        outside &= ~inside

        idx = np.flatnonzero(inside)
        hits = idx[mask[row[idx].astype(np.intp), col[idx].astype(np.intp)]]

        hit_fixations.append(hits)
        hit_aois.extend([path.stem] * len(hits))

    return np.concatenate(hit_fixations), hit_aois, int(outside.sum())


def first_fixations(out, df, n=1):
    """Return the first fixation of each participant on each AOI of a trial.

    out: the AOI hits (output of the mapping, one row per hit, index = row in df)
    df:  the fixations, with the column 'startT' (ms since trial start)
    n:   if larger than 1, also add the number and start time of the n-th
         fixation on the AOI (NaN if the participant fixated the AOI less
         than n times)
    """
    hits = out[out['AOI_name'] != 'WS'].copy()
    hits['startT'] = df.loc[hits.index, 'startT'].to_numpy()
    hits = hits.sort_values('startT', kind='stable')
    keys = ['participant', 'trial', 'AOI_name']
    rank = hits.groupby(keys, sort=False).cumcount() + 1

    first = hits[rank == 1].rename(columns={
        'startT': 'time_to_first_fixation',
        'fixation_number': 'first_fixation_number'})
    first = first[keys + ['first_fixation_number', 'time_to_first_fixation']]
    if n > 1:
        nth = hits[rank == n].rename(columns={
            'startT': f'time_to_fixation_{n}',
            'fixation_number': f'fixation_{n}_number'})
        nth = nth[keys + [f'fixation_{n}_number', f'time_to_fixation_{n}']]
        first = first.merge(nth, on=keys, how='left')
        first[f'fixation_{n}_number'] = first[f'fixation_{n}_number'].astype('Int64')

    first = first.sort_values('time_to_first_fixation', kind='stable')
    order = first['AOI_name'].map(natural_key)
    first = first.iloc[sorted(range(len(first)),
                              key=lambda i: (first['trial'].iat[i], order.iat[i]))]
    return first.reset_index(drop=True)


def plot_cumulative(trial, aoi_names, first_times, n_participants, t_end, out_path,
                    cut='edge', min_fixations=1):
    """Plot the percentage of participants that has fixated each AOI over time.

    trial:          trial (stimulus) name, used as title
    aoi_names:      all AOIs of this trial (AOIs never fixated stay at 0 %)
    first_times:    dict AOI name -> times (ms) of the first fixation (or the
                    min_fixations-th fixation) on that
                    AOI, one value per participant who fixated it
    n_participants: number of participants with fixations on this trial
    t_end:          end of the time axis (ms), e.g. end of the last fixation;
                    first fixations after t_end are not shown
    cut:            'edge' or 'last_fixation', see CUMULATIVE_CUT
    min_fixations:  only used in the labels, see CUMULATIVE_MIN_FIXATIONS
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    from matplotlib.lines import Line2D

    t_end_s = t_end / 1000
    fig, ax = plt.subplots(figsize=(10, 6))
    handles = []

    for i, aoi in enumerate(aoi_names):
        color = AOI_COLORS[i % len(AOI_COLORS)]
        marker = AOI_MARKERS[(i // len(AOI_COLORS)) % len(AOI_MARKERS)]
        t = np.sort(np.asarray(first_times.get(aoi, []), dtype=float)) / 1000
        pct = 100 * np.arange(1, len(t) + 1) / n_participants
        # Cut the curve at the end of the time axis; the straight line to a
        # first fixation after t_end ends at the interpolated value at t_end
        y_end = np.interp(t_end_s, np.concatenate([[0], t]),
                          np.concatenate([[0], pct]))
        shown = t <= t_end_s
        later = not shown.all()
        t, pct = t[shown], pct[shown]

        # Start at 0 % at trial start and connect the first fixations of the
        # participants with straight lines (an estimate of the underlying
        # cumulative curve). The line ends at the last first fixation, or with
        # cut='edge' continues to the edge if a later first fixation follows.
        if later and cut == 'edge':
            x = np.concatenate([[0], t, [t_end_s]])
            y = np.concatenate([[0], pct, [y_end]])
        else:
            x = np.concatenate([[0], t])
            y = np.concatenate([[0], pct])
        n_total = len(first_times.get(aoi, []))
        times_text = '' if min_fixations == 1 else f' {min_fixations}x'
        if n_total == 0:
            label = f'{aoi} (not fixated{times_text})'
        elif len(t) == 0:
            label = f'{aoi} (not fixated{times_text} within {t_end_s:g} s)'
        else:
            label = aoi
        ax.plot(x, y, color='black', linewidth=0.8, zorder=2, clip_on=False)
        marker_style = dict(marker=marker, markersize=6, markerfacecolor=color,
                            markeredgecolor='black', markeredgewidth=0.6)
        ax.plot(t, pct, linestyle='none', zorder=3, clip_on=False, **marker_style)
        handles.append(Line2D([], [], color='black', linewidth=0.8,
                              label=label, **marker_style))

    ax.set_xlim(0, t_end_s)
    ax.set_ylim(0, 100)
    ax.set_xlabel('Time since trial start (s)')
    if min_fixations == 1:
        ax.set_ylabel('Participants who fixated the AOI (%)')
        title = f'{trial}: participants who have fixated each AOI'
    else:
        ax.set_ylabel(f'Participants with {min_fixations} or more fixations on the AOI (%)')
        title = f'{trial}: participants with {min_fixations} or more fixations on each AOI'
    ax.set_title(f'{title} (n = {n_participants})',
                 pad=12)
    ax.grid(True, color='#d9d9d9', linewidth=0.6, linestyle=':')
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.legend(handles=handles, title='AOI', loc='center left', bbox_to_anchor=(1.01, 0.5),
              frameon=False)

    fig.tight_layout()
    fig.savefig(out_path, dpi=PLOT_DPI)
    plt.close(fig)
    return out_path


def main():
    start_time = time.perf_counter()

    df_fixations = pd.read_csv(FIXATION_FILE, sep='\t')
    aoi_files = find_aoi_files(Path.cwd() / AOI_FOLDER)

    # Only fixations on trials that have AOIs
    df = df_fixations[df_fixations['trial'].isin(aoi_files)].reset_index(drop=True)
    df['fixation_number'] = df.groupby(['participant', 'trial'], sort=False).cumcount() + 1

    trial_rows = df.groupby('trial', sort=False).indices
    trials = list(trial_rows)
    xpos = df['xpos'].to_numpy()
    ypos = df['ypos'].to_numpy()
    args = ([aoi_files[t] for t in trials],
            [xpos[trial_rows[t]] for t in trials],
            [ypos[trial_rows[t]] for t in trials],
            [AOI_THRESHOLD] * len(trials))

    n_workers = N_WORKERS if N_WORKERS is not None else (os.cpu_count() or 1)
    n_workers = max(1, min(n_workers, len(trials)))
    print(f'Processing {len(trials)} trials with {n_workers} worker(s)')
    if AOI_THRESHOLD is None:
        print('AOI pixels: maximum value only (pure white)')
    else:
        print(f'AOI pixels: value > {AOI_THRESHOLD}')

    if n_workers > 1:
        executor = ProcessPoolExecutor(max_workers=n_workers)
        results = executor.map(map_trial, *args, chunksize=4)
    else:
        executor = None
        results = map(map_trial, *args)

    hit_rows = []
    hit_aois = []
    n_outside = 0
    for i, (trial, (fix_idx, aoi_names, n_out)) in enumerate(zip(trials, results)):
        print(f'{i + 1}/{len(trials)} {trial}')
        hit_rows.append(trial_rows[trial][fix_idx])
        hit_aois.extend(aoi_names)
        n_outside += n_out

    if n_outside:
        print(f'{n_outside} fixations outside of screen. Counted as WS')

    # Fixations that hit no AOI are WS (white space)
    hit_rows = np.concatenate(hit_rows) if hit_rows else np.array([], dtype=np.intp)
    ws_rows = np.setdiff1d(np.arange(len(df)), hit_rows)

    aoi_per_row = pd.DataFrame({
        'row': np.concatenate([hit_rows, ws_rows]),
        'AOI_name': hit_aois + ['WS'] * len(ws_rows),
    })
    # Keep the original fixation order (stable sort keeps AOI order within a fixation)
    aoi_per_row = aoi_per_row.sort_values('row', kind='stable')

    out = df.loc[aoi_per_row['row'], ['participant', 'trial', 'fixation_number',
                                      'xpos', 'ypos', 'dur']]
    out['AOI_name'] = aoi_per_row['AOI_name'].to_numpy()

    # Save AOI data as csv
    out.to_csv(OUTPUT_FILE, index=False)
    print(f'Saved {len(out)} rows to {OUTPUT_FILE}')

    if PLOT_CUMULATIVE:
        if 'startT' not in df.columns:
            print("Warning: no column 'startT' in the fixation file, "
                  'no time to first fixation and no cumulative plots')
        else:
            n_min = int(CUMULATIVE_MIN_FIXATIONS)
            if n_min < 1:
                raise ValueError('CUMULATIVE_MIN_FIXATIONS must be 1 or more')
            first = first_fixations(out, df, n_min)
            first.to_csv(FIRST_FIXATION_FILE, index=False)
            print(f'Saved {len(first)} rows to {FIRST_FIXATION_FILE}')

            folder = Path(CUMULATIVE_FOLDER)
            folder.mkdir(parents=True, exist_ok=True)
            n_per_trial = df.groupby('trial')['participant'].nunique()
            end_col = 'endT' if 'endT' in df.columns else 'startT'
            if CUMULATIVE_TIME_S is None:
                t_end = df.groupby('trial')[end_col].max()
            else:
                t_end = pd.Series(1000.0 * CUMULATIVE_TIME_S, index=trials)
            time_col = ('time_to_first_fixation' if n_min == 1
                        else f'time_to_fixation_{n_min}')
            times = {key: g[time_col].dropna().to_numpy()
                     for key, g in first.groupby(['trial', 'AOI_name'])}

            if CUMULATIVE_CUT not in ('edge', 'last_fixation'):
                raise ValueError("CUMULATIVE_CUT must be 'edge' or 'last_fixation', "
                                 f'not {CUMULATIVE_CUT!r}')
            plot_args = ([], [], [], [], [], [], [], [])
            for t in trials:
                names = [p.stem for p in aoi_files[t]]
                for lst, value in zip(plot_args, (
                        t, names,
                        {a: times.get((t, a), []) for a in names},
                        int(n_per_trial[t]), float(t_end[t]),
                        folder / f'cumulative_{Path(t).stem}.{PLOT_FORMAT}',
                        CUMULATIVE_CUT, n_min)):
                    lst.append(value)

            if executor is not None:
                paths = executor.map(plot_cumulative, *plot_args, chunksize=4)
            else:
                paths = map(plot_cumulative, *plot_args)
            for i, path in enumerate(paths):
                print(f'{i + 1}/{len(trials)} saved {path}')

    if executor is not None:
        executor.shutdown()

    elapsed = time.perf_counter() - start_time
    minutes, seconds = divmod(elapsed, 60)
    print(f'Total time: {int(minutes)} min {seconds:.1f} s')


if __name__ == '__main__':
    main()
