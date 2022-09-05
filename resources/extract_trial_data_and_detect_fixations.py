# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 19:25:01 2021

@author: Marcus
Extract trial data and save it in a format that I2MC accepts to detect fixations.

Adapted to handle data recorded from one participant running the read_my.py demo

"""
import pickle
import numpy as np
import pandas as pd
import sys, os
import shutil
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
# header / column names
header = ['device_time_stamp',
         'system_time_stamp',
         'left_gaze_point_on_display_area_x',
         'left_gaze_point_on_display_area_y',
         'left_gaze_point_in_user_coordinate_system_x',
         'left_gaze_point_in_user_coordinate_system_y',
         'left_gaze_point_in_user_coordinate_system_z',
         'left_gaze_origin_in_trackbox_coordinate_system_x',
         'left_gaze_origin_in_trackbox_coordinate_system_y',
         'left_gaze_origin_in_trackbox_coordinate_system_z',
         'left_gaze_origin_in_user_coordinate_system_x',
         'left_gaze_origin_in_user_coordinate_system_y',
         'left_gaze_origin_in_user_coordinate_system_z',
         'left_pupil_diameter',
         'left_pupil_validity',
         'left_gaze_origin_validity',
         'left_gaze_point_validity',
         'right_gaze_point_on_display_area_x',
         'right_gaze_point_on_display_area_y',
         'right_gaze_point_in_user_coordinate_system_x',
         'right_gaze_point_in_user_coordinate_system_y',
         'right_gaze_point_in_user_coordinate_system_z',
         'right_gaze_origin_in_trackbox_coordinate_system_x',
         'right_gaze_origin_in_trackbox_coordinate_system_y',
         'right_gaze_origin_in_trackbox_coordinate_system_z',
         'right_gaze_origin_in_user_coordinate_system_x',
         'right_gaze_origin_in_user_coordinate_system_y',
         'right_gaze_origin_in_user_coordinate_system_z',
         'right_pupil_diameter',
         'right_pupil_validity',
         'right_gaze_origin_validity',
         'right_gaze_point_validity']

# Set this to True is you also want to detect fixations (not only extract trials)
classify_fixations = True

# Check whether I2MC exists
if classify_fixations:

    I2MC_main_path = Path.cwd() / 'I2MC' / 'I2MC_Python-master' / 'example'

    # First remove example data found when downloading I2MC
    example_data_path = I2MC_main_path / 'example_data'
    if example_data_path.is_dir():
        shutil.rmtree(example_data_path)

    # Then create a new one (to be filled with new data)
    I2MC_data_path = I2MC_main_path / 'example_data'/ 'participant1'
    try:
        I2MC_data_path.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("Folder is already there")
    else:
        print("Folder was created")

    I2MC_main = I2MC_main_path / 'I2MC_example.py'
    if not I2MC_main.is_file():
        print('It appears that I2MC is not available. please follow the\
     instructions in /resources/I2MC/get_I2MC.txt to download it.')
        raise FileNotFoundError

# Read messages and et data from pickle
f = open("testfile.pkl", 'rb')
gaze_data_container = pickle.load(f)
msg_container = pickle.load(f)

# Convert to pandas dataframes
df = pd.DataFrame(gaze_data_container, columns=header)
df_msg = pd.DataFrame(msg_container, columns=['system_time_stamp', 'msg'])


# Read message for onset and offset
# Assumption is that messages are on the form
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

# Extract relevant trial data and save in format required by I2MC
for t in trial_msg:
    df_trial = extract_trial_data(df, df_msg, t[0], t[1])

    filename = t[0].split('_')[1] + '.tsv'
    if classify_fixations:
        df_trial.to_csv(str(I2MC_data_path / filename), sep='\t')
    else:
        df_trial.to_csv(filename, sep='\t')

# %%
# Now open and run / 'I2MC' / 'I2MC_Python-master' / 'example / I2MC_example.py'.
# OBS: you first need to adjust the settings to match your
# Experimental setup in 'I2MC_example.py'. Check under '# NECESSARY VARIABLES'
# Also make sure Titta is use when importing data (line 190)
# data = imp.Titta(file_name, [opt['xres'], opt['yres']])





