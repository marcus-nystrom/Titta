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
import matplotlib.pyplot as plt

plt.close('all')

# %%
def extract_trial_data(df_et_data, df_remote, df_msg, msg_onset, msg_offset):
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

    # Cut out samples belonging to this stimulus
    fix_idx_start = np.searchsorted(df_remote.local_system_time_stamp,
                                    start_time_stamp)
    fix_idx_stop = np.searchsorted(df_remote.local_system_time_stamp,
                                   stop_time_stamp)
    df_stim_remote = df_remote.iloc[fix_idx_start:fix_idx_stop].copy()

    return df_stim, df_stim_remote

# %%

# Read messages and et data all participants (one .pkl-file per participant)
files = (Path.cwd() / 'data').glob('*.h5')

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
    remote_gaze = []
    for i, row in df_msg.iterrows():

        if 'onset' in row.msg:
            onset.append(row.msg)
        if 'offset' in row.msg:
            offset.append(row.msg)
        if 'remotesample' in row.msg:
            remote_gaze.append(row.msg.split('_'))
    trial_msg = zip(onset, offset)

    # Create a datarame of remote gaze samples
    df_remote = pd.DataFrame(remote_gaze, columns=['type', 'pid', 'remote_system_time_stamp', 'local_system_time_stamp',
                                                   'gaze_x', 'gaze_y'])
    df_remote.gaze_x = df_remote.gaze_x.astype(float)
    df_remote.gaze_y = df_remote.gaze_y.astype(float)
    df_remote.remote_system_time_stamp = df_remote.remote_system_time_stamp.astype(int)
    df_remote.local_system_time_stamp = df_remote.local_system_time_stamp.astype(int)

    # Create a folder to put the trials
    path = Path.cwd() / 'trials' / pid
    path.mkdir(parents=True, exist_ok=True)

    # Extract relevant trial data and save in format required by I2MC
    for t in trial_msg:
        df_trial, df_trial_remote = extract_trial_data(df_gaze, df_remote, df_msg, t[0], t[1])

        filename = t[0].split('_', 1)[1] + '.tsv'
        df_trial.to_csv(str(path) + os.sep + filename, sep='\t', index=False)

        filename_remote = t[0].split('_', 1)[1] + '_remote.tsv'
        df_trial_remote.to_csv(str(path) + os.sep + filename_remote, sep='\t', index=False)

        print('Trial ' + filename + " written to folder ", path)

        plt.figure()
        plt.plot(df_trial.system_time_stamp, df_trial.left_gaze_point_on_display_area_x, '.-',label=f'local {pid}')
        for i in df_trial_remote.pid.unique():
            df_temp = df_trial_remote[df_trial_remote.pid==i]
            plt.plot(df_temp.local_system_time_stamp, df_temp.gaze_x, '.-', label=df_temp.pid.iloc[0])
        plt.legend()



