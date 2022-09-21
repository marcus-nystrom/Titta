# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 10:57:23 2019

@author: Jonathan
"""

# =============================================================================
# Import modules
# =============================================================================
import numpy as np
import pandas as pd


# =============================================================================
# Import Titta
# =============================================================================
def Titta(fname, res=[1920,1080]):
    '''
    Imports data from tsv files produced by Titta.


    Parameters
    ----------
    fname : string
        The file (filepath)
    res : tuple
        The (X,Y) resolution of the screen

    Returns
    -------
    df : pandas.DataFrame
         Gaze data, with columns:
         t : The sample times from the dataset
         L_X : X positions from the left eye
         L_Y : Y positions from the left eye
         R_X : X positions from the right eye
         R_Y : Y positions from the right eye
    '''

    raw_df = pd.read_csv(fname, sep='\t')
    df = pd.DataFrame()

    # Extract required data
    df['time'] = raw_df['system_time_stamp']
    df['L_X']  = raw_df['left_gaze_point_on_display_area_x']  * res[0]
    df['L_Y']  = raw_df['left_gaze_point_on_display_area_y']  * res[1]
    df['R_X']  = raw_df['right_gaze_point_on_display_area_x'] * res[0]
    df['R_Y']  = raw_df['right_gaze_point_on_display_area_y'] * res[1]

    # prep
    df['time'] = df['time'] - df.iloc[0,df.columns.get_loc('time')]
    df['time'] = df['time'] / 1000.0

    return df

# =============================================================================
# Import Tobii TX300
# =============================================================================
def tobii_TX300(fname, res=[1920,1080]):
    '''
    Imports data from Tobii TX300 as returned by Tobii SDK.


    Parameters
    ----------
    fname : string
        The file (filepath)
    res : tuple
        The (X,Y) resolution of the screen

    Returns
    -------
    df : pandas.DataFrame
         Gaze data, with columns:
         t : The sample times from the dataset
         L_X : X positions from the left eye
         L_Y : Y positions from the left eye
         R_X : X positions from the right eye
         R_Y : Y positions from the right eye
    '''

    # Load all data
    raw_df = pd.read_csv(fname, delimiter='\t')
    df = pd.DataFrame()

    # Extract required data
    df['time'] = raw_df['RelTimestamp']
    df['L_X'] = raw_df['LGazePos2dx'] * res[0]
    df['L_Y'] = raw_df['LGazePos2dy'] * res[1]
    df['R_X'] = raw_df['RGazePos2dx'] * res[0]
    df['R_Y'] = raw_df['RGazePos2dy'] * res[1]

    ###
    # sometimes we have weird peaks where one sample is (very) far outside the
    # monitor. Here, count as missing any data that is more than one monitor
    # distance outside the monitor.

    # Left eye
    lMiss1 = (df['L_X'] < -res[0]) | (df['L_X']>2*res[0])
    lMiss2 = (df['L_Y'] < -res[1]) | (df['L_Y']>2*res[1])
    lMiss  = lMiss1 | lMiss2 | (raw_df['LValidity'] > 1)
    df.loc[lMiss,'L_X'] = np.NAN
    df.loc[lMiss,'L_Y'] = np.NAN

    # Right eye
    rMiss1 = (df['R_X'] < -res[0]) | (df['R_X']>2*res[0])
    rMiss2 = (df['R_Y'] < -res[1]) | (df['R_Y']>2*res[1])
    rMiss  = rMiss1 | rMiss2 | (raw_df['RValidity'] > 1)
    df.loc[rMiss,'R_X'] = np.NAN
    df.loc[rMiss,'R_Y'] = np.NAN

    return df