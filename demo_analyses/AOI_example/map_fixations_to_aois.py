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


def find_aoi_files(aoi_folder):
    """Return dict trial_name -> sorted list of AOI image paths."""
    aoi_files = {}
    for p in sorted(aoi_folder.rglob('*')):
        if p.is_file() and p.suffix.lower() == '.png':
            aoi_files.setdefault(p.parent.name, []).append(p)
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

    if executor is not None:
        executor.shutdown()

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

    elapsed = time.perf_counter() - start_time
    minutes, seconds = divmod(elapsed, 60)
    print(f'Total time: {int(minutes)} min {seconds:.1f} s')


if __name__ == '__main__':
    main()
