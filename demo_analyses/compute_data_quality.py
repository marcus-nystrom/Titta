# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 15:29:39 2022

@author: Marcus
"""

import pickle
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import errno
import os

# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 15:29:39 2022

@author: Marcus
"""

# Folder where the trails should be
trial_folder = Path.cwd() / 'trials'

#%% Compute data quality from pickle

# Find unique participant pickle files (one per participant)
files = Path.cwd().glob('*.pkl')

# Go through all files and compute data quality
data_quality = []
for fn in files:

    f = open(fn, 'rb')
    pid = fn.name.split('.')[0]
    gaze_data_container = pickle.load(f)
    msg_container = pickle.load(f)
    eye_openness_data_container = pickle.load(f)
    external_signal_container = pickle.load(f)
    sync_data_container = pickle.load(f)
    stream_errors_container = pickle.load(f)
    image_data_container = pickle.load(f)
    calibration_history = pickle.load(f)
    system_info = pickle.load(f)
    # settings = pickle.load(f)
    # python_version = pickle.load(f)
    f.close()

    # Go through all calibrations and select 'used' ones.
    # 'Used' means that it was the selected calibration
    # (several calibration can be made and the best one can
    # be selected)
    # All data quality values here are recorded during the
    # validation procedure following directly after the calibration.
    for c in calibration_history:
        # if this calibration was 'used'?
        if c[-1] == 'used':
            data_quality.append([pid] + c[:-1])

    # Also compute precision and data loss from individual trials


df = pd.DataFrame(data_quality, columns=['pid',
                                         'accuracy_left_eye (deg)',
                                         'accuracy_right_eye (deg)',
                                         'RMS_S2S_left_eye (deg)',
                                         'RMS_S2S_right_eye (deg)',
                                         'SD_left_eye (deg)',
                                         'SD_right_eye (deg)',
                                         'Prop_data_loss_left_eye',
                                         'Prop_ data_loss_right_eye'])
df.to_csv('data_quality_validation.csv')
print('Data quality values written to data_quality_validation.csv')


# %% Compute data loss per participant and trial.

# A requirement to run this analysis is that data already have been divided
# into trials (by running extract_trial_data.py). Check if that have been done
if  not trial_folder.exists():
    raise FileNotFoundError(
        errno.ENOENT, os.strerror(errno.ENOENT) + '. ***OBS! You must first run extract_trial_data.py***', trial_folder)

# Go through all trials and compute data loss for each trial
data_loss_trials = []
trials = trial_folder.rglob('*.tsv')
for trial in trials:
    pid = str(trial).split(os.sep)[-2]

    df_trial = pd.read_csv(trial, sep='\t')
    trial_name = '.'.join(str(trial).split(os.sep)[-1].split('.')[:2])

    # Check that no samples are missing (based on the expected number of samples)
    expected_number_of_samples = (df_trial.system_time_stamp.iloc[-1] - df_trial.system_time_stamp.iloc[0]) / 1000 / 1000 * system_info['sampling_frequency']
    recorded_number_of_samples = len(df_trial.system_time_stamp)
    percent_valid_samples = expected_number_of_samples/recorded_number_of_samples*100
    if percent_valid_samples < 99:
        print(f'WARNING: Trial is missing {100 - percent_valid_samples}% of the samples.')
    prop_missing_data = 1 - expected_number_of_samples/recorded_number_of_samples

    # Compute precision
    for eye in  ['left', 'right']:
        n_samples = len(df_trial)
        n_valid_samples = np.nansum(df_trial[eye + '_gaze_point_validity'])
        prop_invalid_samples = 1 - n_valid_samples / n_samples
        data_loss_trials.append([pid, trial_name, eye, n_samples,
                                 n_valid_samples, prop_invalid_samples, 0])

df_trial = pd.DataFrame(data_loss_trials, columns=['pid', 'trial',
                                                      'eye',
                                                      'n_trial_samples',
                                                      'n_valid_trial_samples',
                                                      'prop_invalid_samples',
                                                      'prop_missing_data'])
df_trial.to_csv('data_loss_per_trial.csv')
print('Data loss values written to data_loss_per_trial.csv')
