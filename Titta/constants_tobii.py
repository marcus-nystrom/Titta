# -*- coding: utf-8 -*-
"""
Created on Thu Jun 01 14:26:21 2017

@author: Marcus
"""
from psychopy import monitors
import numpy as np
import helpers_tobii as helpers

TRACKER_ADDRESS             = 'tet-tcp://169.254.8.13'

# Monitor/geometry 
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = True
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
SAMPLING_RATE = 600 # TODO
TRACKING_MODE = '' # TODO (dark pupil or bright pupil)

# Parameters for calibration
PACING_INTERVAL = 1.0 # How long ot present the dot until samples are collected
DOT_STIM_SIZE = 0.02
CAL_DOT_SIZE = [0.01, 0.03]

# Position of calibration and validation targets (in Tobii coordinate system)
scaling = 0.7
corr = 0.5 - (scaling * 0.5)
CAL_POS_TOBII = np.array([[0.5, 0.5], [0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]) 
CAL_POS_TOBII = CAL_POS_TOBII * scaling + corr
VAL_POS_TOBII = np.array([[0.5, 0.5], [0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0],
                          [0.5, 1.0], [0.5, 0.0], [0.0, 0.5], [1.0, 0.5]])
VAL_POS_TOBII = VAL_POS_TOBII * scaling + corr

cal_temp = CAL_POS_TOBII.copy()
val_temp = VAL_POS_TOBII.copy()


# Parameters for visualtion of validation data
SAMPLE_DOT_SIZE = 0.04 # In normalized units
HEAD_POS_CIRCLE_RADIUS = 0.25 # in normalized units

# Position of calibration and validation targets (in 'norm' coordinate system)
CAL_POS_NORM = helpers.tobii2norm(cal_temp)
VAL_POS_NORM = helpers.tobii2norm(val_temp)

# Combine in array where first two cols are 'norm', and the next two tobii
CAL_POS = np.hstack((CAL_POS_TOBII, CAL_POS_NORM))
VAL_POS = np.hstack((VAL_POS_TOBII, VAL_POS_NORM))

print(CAL_POS_TOBII, CAL_POS_NORM)


