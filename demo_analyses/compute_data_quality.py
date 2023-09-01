# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 15:29:39 2022

@author: Marcus
"""
import numpy as np
from pathlib import Path
import pandas as pd
import errno
import os
import json

# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 15:29:39 2022

@author: Marcus
"""


# Folder where the trails should be
trial_folder = Path.cwd() / 'trials'

#%% Compute data quality from pickle

files = (Path.cwd() / 'data').glob('*.h5')

data_quality = []
info = []
for f in files:

    print(f)

    # Load info about tracker
    fh = open(str(f)[:-3] + '.json')
    info.append(json.load(fh))

    pid = str(f).split(os.sep)[-1][:-3]

    # Convert to pandas dataframes
    calibration_history = pd.read_hdf(f, 'calibration_history')

    # Go through all calibrations and select 'used' ones.
    # 'Used' means that it was the selected calibration
    # (several calibration can be made and the best one can
    # be selected)
    # All data quality values here are recorded during the
    # validation procedure following directly after the calibration.
    for i, row in calibration_history.iterrows():
        # if this calibration was 'used'?
        if row['Calibration used'] == 'used':
            data_quality.append([pid] + list(row.to_numpy()[:-1]))

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

    if len(df_trial) == 0:
        print('Warning: trial with no data')
        continue

    trial_name = '.'.join(str(trial).split(os.sep)[-1].split('.')[:2])

    # Check that no samples are missing (based on the expected number of samples)
    expected_number_of_samples = (df_trial.system_time_stamp.iloc[-1] - df_trial.system_time_stamp.iloc[0]) / 1000 / 1000 * info[0]['sampling_frequency']
    recorded_number_of_samples = len(df_trial.system_time_stamp)
    percent_valid_samples = recorded_number_of_samples/expected_number_of_samples*100
    if percent_valid_samples < 99:
        print(f'WARNING: Trial is missing {100 - percent_valid_samples}% of the samples.')
    prop_missing_data = 1 - recorded_number_of_samples/expected_number_of_samples
    if np.abs(prop_missing_data) < 0.001:
        prop_missing_data = 0

    # Compute precision
    for eye in  ['left', 'right']:
        n_samples = len(df_trial)
        n_valid_samples = np.nansum(df_trial[eye + '_gaze_point_valid'])
        prop_invalid_samples = 1 - n_valid_samples / n_samples
        data_loss_trials.append([pid, trial_name, eye, n_samples,
                                 n_valid_samples, prop_invalid_samples, prop_missing_data])

df_trial = pd.DataFrame(data_loss_trials, columns=['pid', 'trial',
                                                      'eye',
                                                      'n_trial_samples',
                                                      'n_valid_trial_samples',
                                                      'prop_invalid_samples',
                                                      'prop_missing_data'])
df_trial.to_csv('data_loss_per_trial.csv')
print('Data loss values written to data_loss_per_trial.csv')
