# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:06:43 2022

@author: Marcus
"""

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import os

# Read files with fixations generated with the I2MC
df_fixations = pd.read_csv('allfixations.txt', sep='\t')


aoi_hits = []

# For each trial, check whether the fixations land on an AOI
trials = df_fixations.trial.unique()

for trial in trials:

    # Extract trial data
    df_trial = df_fixations[df_fixations.trial == trial]
    df_trial.reset_index(inplace=True)

    # Read the binary AOI images into a dict
    trial_aois = (Path.cwd() / 'AOIs' / trial).glob('*.png')
    image_aois = {}
    for t in trial_aois:
        image_aois[str(t).split(os.sep)[-1]] = plt.imread(t)[:, :, 0].astype('int')

    # Go through each fixation in this trial and check whether it lands on
    # an AOI
    for i, row in df_trial.iterrows():
        x, y = row.xpos, row.ypos
        dur = row.dur

        # hit?
        hit = False
        for key in image_aois:
            if image_aois[key][int(y), int(x)] == 0:  # 0 means black
                aoi_hits.append([trial, i, x, y, dur, key])
                hit = True

        # if not hit
        if not hit:
            aoi_hits.append([trial, i, x, y, dur, 'WS']) # WS (white space) for miss

# Save AOI data as csv
pd.DataFrame(aoi_hits, columns=['trial', 'fixation_number', 'xpos', 'ypos',
                                'dur', 'AOI_name']).to_csv('fixation_aoi_hits.tsv', sep='\t')









