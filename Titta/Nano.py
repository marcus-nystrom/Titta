# -*- coding: utf-8 -*-
"""
Created on Thu Jun 01 14:26:21 2017

@author: Marcus
"""
from psychopy import monitors
import numpy as np
from helpers_tobii import tobii2deg

FILENAME                    = 'test.tsv' # Name of et-data
METHOD_TO_WRITE_DATA        = 2 # 1 -write to file, 2- write to list
TRACKER_ADDRESS             = ''


# Monitor/geometry 
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = True
SCREEN_RES                  = [1920, 1080]
SCREEN_WIDTH                = 52.7 # cm
SCREEN_HEIGHT               = 29.5 # cm
VIEWING_DIST                = 63 #  # distance from eye to center of screen (cm)
#UNITS                       = 'norm'

# Convert from Tobii coordinate system (normalized) to psychopy in deg. (centered)
mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)     # Width of screen (cm)
mon.setDistance(VIEWING_DIST)  # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)

# Tracking parameters
SAMPLING_RATE = 60 # 
TRACKING_MODE = '' # only one tracking mode for Nano

# Parameters for calibration
PACING_INTERVAL = 1.0 # How long to present the dot until samples are collected. What unit? Mismatching description Tobii.py file.
#DOT_STIM_SIZE = 0.2
#CAL_DOT_SIZE = [0.1, 0.6]
ANIMATE_CALIBRATION = False
RECORD_EYE_IMAGES_DURING_CALIBRATION = False
#CAL_POS_TOBII = np.array([[0.5, 0.5], [0.1, 0.1], [0.1, 0.9], [0.9, 0.1], [0.9, 0.9]])
#VAL_POS_TOBII = np.array([[0.2, 0.2], [0.2, 0.8], [0.8, 0.2], [0.8, 0.8]])

scaling = 0.7
corr = 0.5 - (scaling * 0.5)
CAL_POS_TOBII = np.array([[0.5, 0.5], [0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]) 
CAL_POS_TOBII = CAL_POS_TOBII * scaling + corr
#VAL_POS_TOBII = np.array([[0.5, 0.5], [0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0],
#                          [0.5, 1.0], [0.5, 0.0], [0.0, 0.5], [1.0, 0.5]])
VAL_POS_TOBII = np.array([[0.2, 0.2], [0.2, 0.8], [0.8, 0.2], [0.8, 0.8]])
VAL_POS_TOBII = VAL_POS_TOBII * scaling + corr


CAL_POS_TOBII_temp = CAL_POS_TOBII[:]
VAL_POS_TOBII_temp = VAL_POS_TOBII[:]
# Convert to deg.
CAL_POS_DEG = tobii2deg(CAL_POS_TOBII_temp, mon, SCREEN_HEIGHT)
VAL_POS_DEG = tobii2deg(VAL_POS_TOBII_temp, mon, SCREEN_HEIGHT)

# Dont' know why have have to enter this info again. BUG?
CAL_POS_TOBII = np.array([[0.5, 0.5], [0.1, 0.1], [0.1, 0.9], [0.9, 0.1], [0.9, 0.9]])
VAL_POS_TOBII = np.array([[0.2, 0.2], [0.2, 0.8], [0.8, 0.2], [0.8, 0.8]])
CAL_POS_TOBII = np.array([[0.5, 0.5], [0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]) 
CAL_POS_TOBII = CAL_POS_TOBII * scaling + corr
VAL_POS_TOBII = np.array([[0.2, 0.2], [0.2, 0.8], [0.8, 0.2], [0.8, 0.8]])
VAL_POS_TOBII = VAL_POS_TOBII * scaling + corr

# Combine in array where first two cols are deg, and the next two tobii
CAL_POS = np.hstack((CAL_POS_TOBII, CAL_POS_DEG))
VAL_POS = np.hstack((VAL_POS_TOBII, VAL_POS_DEG))

#print(CAL_POS_TOBII)
#print(CAL_POS)

