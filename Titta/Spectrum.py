# -*- coding: utf-8 -*-
"""
Created on Thu Jun 01 14:26:21 2017

@author: Marcus
"""
import numpy as np

# Default name of et-data file
FILENAME                    = 'test.tsv' 

# Tracking parameters
TRACKER_ADDRESS  = ''   # If none is given, find one on the network
SAMPLING_RATE = 600     # Set sampling rate of tracker

# Parameters for calibration
PACING_INTERVAL = 1.0   # How long ot present the dot until samples are collected
ANIMATE_CALIBRATION = False # Static or animated calibration dots
RECORD_EYE_IMAGES_DURING_CALIBRATION = False
N_CAL_TARGETS = 5  # Valid: 0, 1, 5, 9
N_VAL_TARGETS = 4   # Valid: 4

# List all possible calibration points (in Tobii's coordinate system)
CAL_POS_TOBII = np.array([[0.5, 0.5], [0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0],
                          [0.5, 1.0], [0.5, 0.0], [0.0, 0.5], [1.0, 0.5]])

if N_CAL_TARGETS == 0:
    CAL_POS_TOBII = []
elif N_CAL_TARGETS == 1:
    CAL_POS_TOBII = CAL_POS_TOBII[0, :]
elif N_CAL_TARGETS == 5:
    CAL_POS_TOBII = CAL_POS_TOBII[[0, 1, 2, 3, 4], :]  
    
VAL_POS_TOBII = np.array([[0.2, 0.2], [0.2, 0.8], [0.8, 0.2], [0.8, 0.8]])    
    
# Scale the positions so they look good on the screen
scaling = 0.7
corr = 0.5 - (scaling * 0.5)
CAL_POS_TOBII = CAL_POS_TOBII * scaling + corr
VAL_POS_TOBII = VAL_POS_TOBII * scaling + corr


