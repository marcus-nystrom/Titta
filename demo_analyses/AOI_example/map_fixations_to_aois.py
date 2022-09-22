# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:06:43 2022

@author: Marcus
"""

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import os

# %%
# Read files with fixations generated with the I2MC
df_fixations = pd.read_csv('allfixations.txt', sep='\t')

# List aoi images and save into dict
image_aois = {}

aoi_folder = Path.cwd() / 'AOIs'
for p in aoi_folder.rglob("*"):
    print(p)
    if p.is_file():

        trial_name = str(p).split(os.sep)[-2]
        aoi_name = p.stem

        # Read binary AOI image
        temp_im = plt.imread(p)

        # If an RGB image, use only R-band.
        if len(temp_im.shape) > 2:
            temp_im = temp_im[:, :, 0]

        # Add AOIs to dictionary
        if trial_name in image_aois:
            image_aois[trial_name].update({aoi_name:temp_im})
        else:
            image_aois[trial_name] = {}
            image_aois[trial_name][aoi_name] = temp_im

        # Nested_dict[dict][key] = 'value'

# %% Map fixations to AOIs
aoi_hits = []

# For each fixation
trial_old = 'dummy_trial_name'
for i, row in df_fixations.iterrows():

    trial = row.trial
    if trial != trial_old:
        trial_fixation_no = 1
        trial_old = trial

    participant = row.participant

    # Find AOIs for this trial
    aois = image_aois[trial]

    # Position and duration of fixation
    x, y = row.xpos, row.ypos
    dur = row.dur

    # fixation hits an AOI?
    hit = False
    for key in aois:
        if aois[key][int(y), int(x)] == temp_im.max():
            aoi_hits.append([row.participant, row.trial, trial_fixation_no, x, y, dur, key])
            hit = True

    # if not hit
    if not hit:
        aoi_hits.append([participant, trial, trial_fixation_no, x, y, dur, 'WS']) # WS (white space) for miss

    trial_fixation_no += 1

# Save AOI data as csv
df = pd.DataFrame(aoi_hits, columns=['participant', 'trial', 'fixation_number',
                                     'xpos', 'ypos',
                                'dur', 'AOI_name'])
df.to_csv('fixation_aoi_hits.csv', index=False)









