# -*- coding: utf-8 -*-
"""
Created on Thu Jun 01 14:26:21 2017

@author: Marcus
"""
from psychopy import monitors
import numpy as np
import helpers_tobii as helpers


FILENAME                    = 'test.tsv' # Name of et-data
METHOD_TO_WRITE_DATA        = 2 # 1 -write to file, 2- write to list
TRACKER_ADDRESS             = ''

# Monitor/geometry 
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = False
SCREEN_RES                  = [1920, 1080]
SCREEN_WIDTH                = 53 # cm
SCREEN_HEIGHT               = 30 # cm
VIEWING_DIST                = 63#  # distance from eye to center of screen (cm)
#UNITS                       = 'norm'

# Convert from Tobii coordinate system (normalized) to psychopy in deg. (centered)
mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)     # Width of screen (cm)
mon.setDistance(VIEWING_DIST)  # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)

# Tracking parameters
SAMPLING_RATE = 90 # 
TRACKING_MODE = '' # TODO (dark pupil or bright pupil)

# Parameters for calibration
PACING_INTERVAL = 1.0 # How long ot present the dot until samples are collected
ANIMATE_CALIBRATION = False
#CAL_POS_TOBII = np.array([[0.5, 0.5], [0.1, 0.1], [0.1, 0.9], [0.9, 0.1], [0.9, 0.9]])
#VAL_POS_TOBII = np.array([[0.2, 0.2], [0.2, 0.8], [0.8, 0.2], [0.8, 0.8]])

scaling = 0.7
corr = 0.5 - (scaling * 0.5)
CAL_POS_TOBII = np.array([[0.5, 0.5], [0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]) 
CAL_POS_TOBII = CAL_POS_TOBII * scaling + corr
VAL_POS_TOBII = np.array([[0.5, 0.5], [0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0],
                          [0.5, 1.0], [0.5, 0.0], [0.0, 0.5], [1.0, 0.5]])
VAL_POS_TOBII = np.array([[0.2, 0.2], [0.2, 0.8], [0.8, 0.2], [0.8, 0.8]])
VAL_POS_TOBII = VAL_POS_TOBII * scaling + corr

cal_temp = CAL_POS_TOBII.copy()
val_temp = VAL_POS_TOBII.copy()

# Parameters for visualtion of validation data
#SAMPLE_DOT_SIZE = 0.04 # In normalized units
#HEAD_POS_CIRCLE_RADIUS = 0.25 # in normalized units

# Position of calibration and validation targets (in 'deg' coordinate system)
CAL_POS_DEG = helpers.tobii2deg(cal_temp, mon, SCREEN_HEIGHT)
VAL_POS_DEG = helpers.tobii2deg(val_temp, mon, SCREEN_HEIGHT)

# Combine in array where first two cols are 'deg', and the next two tobii
CAL_POS = np.hstack((CAL_POS_TOBII, CAL_POS_DEG))
VAL_POS = np.hstack((VAL_POS_TOBII, VAL_POS_DEG))

