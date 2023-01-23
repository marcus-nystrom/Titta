# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 19:25:01 2021

@author: Marcus
Extract trial data and save it in a format that I2MC accepts to detect fixations.

Adapted to handle data recorded from the read_my.py demo. Each .pkl-file
contains data from one participant

"""
import h5py
import numpy as np
import pandas as pd
import os
from pathlib import Path

# %%
def extract_trial_data(df_et_data, df_msg, msg_onset, msg_offset):
    ''' Extracts data from one trial associated with the
    stimulus name.

    Args:
        df_et_data - Pandas dataframe with sample et-data (output from Titta)
        df_msg - Pandas dataframe containing messages (assume stimname is 'my_im.png')
        msg_onset (str) - message sent at stimulus onset
        msg_offset (str) - message sent at stimulus onset


    Returns:
        df - dataframe with data from one trial

    '''

    # Find timestamps for data belonging to this stimulus
    start_idx = np.where(df_msg.msg == msg_onset)[0][0]
    stop_idx = np.where(df_msg.msg == msg_offset)[0][0]

    start_time_stamp = df_msg.system_time_stamp[start_idx]
    stop_time_stamp = df_msg.system_time_stamp[stop_idx]

    # print(start_idx, stop_idx, start_time_stamp, stop_time_stamp)
    #
    # Cut out samples belonging to this stimulus
    fix_idx_start = np.searchsorted(df_et_data.system_time_stamp,
                                    start_time_stamp)
    fix_idx_stop = np.searchsorted(df_et_data.system_time_stamp,
                                   stop_time_stamp)
    df_stim = df_et_data.iloc[fix_idx_start:fix_idx_stop].copy()

    return df_stim

# %%

# Read messages and et data all participants (one .pkl-file per participant)
files = Path.cwd().glob('*.h5')

for f in files:

    pid = str(f).split(os.sep)[-1][:-3]

    # Convert to pandas dataframes
    df_gaze = pd.read_hdf(f, 'gaze')
    df_msg= pd.read_hdf(f, 'msg')

    # Read message for onset and offset
    # Assumption is that messages are on the form (must be unique)
    # 'onset_stimulusname' for the onset of a stimulus and
    # 'offset_stimulusname'for the offset of a stimulus
    onset = []
    offset = []
    for i, row in df_msg.iterrows():

        if 'onset' in row.msg:
            onset.append(row.msg)
        if 'offset' in row.msg:
            offset.append(row.msg)
    trial_msg = zip(onset, offset)

    # Create a folder to put the trials
    path = Path.cwd() / 'trials' / pid
    try:
        path.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("Folder is already there")
    else:
        print("Folder was created")

    # Extract relevant trial data and save in format required by I2MC
    for t in trial_msg:
        df_trial = extract_trial_data(df_gaze, df_msg, t[0], t[1])
        df_trial.reset_index(inplace=True)

        filename = t[0].split('_')[1] + '.tsv'
        df_trial.to_csv(str(path) + os.sep + filename, sep='\t')

        print('Trial ' + filename + " written to folder ", path)

