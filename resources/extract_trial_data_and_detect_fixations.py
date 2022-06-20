# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 19:25:01 2021

@author: Marcus
Extract trial data and save it in a format that I2MC accepts to detect fixations.


"""
import pickle
import numpy as np
import pandas as pd
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

# These messages are used in the read_me.py demo
msg_onset = 'stim on: im1.jpeg'  # Replace this with your own message
msg_offset = 'stim off: im1.jpeg'  # Replace this with your own message

I2MC_data_path = Path.cwd() / 'I2MC' / 'example data' / 'participant1'

f = open("testfile.pkl", 'rb')
gaze_data_container = pickle.load(f)
msg_container = pickle.load(f)

# Convert to pandas dataframes
df = pd.DataFrame(gaze_data_container, columns=header)
df_msg = pd.DataFrame(msg_container, columns=['system_time_stamp', 'msg'])

# Extract relevant trial data
df_trial = extract_trial_data(df, df_msg, msg_onset, msg_offset)

# Save data in format required by I2MC
df_trial.to_csv(str(I2MC_data_path / 'trial.tsv'), sep='\t')

# Now run I2MC (you first need to download it and adapt the function to import data
# before this line works)
I2MC_main = str(Path.cwd() / 'I2MC' / 'I2MC.py')
if Path(I2MC_main).is_file():
    exec(open(I2MC_main).read())
else:
    print('It appears that I2MC is not available. please follow the\
 instructions in /resources/I2MC/get_I2MC.txt to download it.')
