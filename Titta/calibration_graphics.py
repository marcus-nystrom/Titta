# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 10:19:10 2018

@author: Marcus
"""
import numpy as np

blue = tuple(np.array([37, 97, 163]) / 255.0 * 2 - 1)
blue_active = tuple(np.array([11, 122, 244]) / 255.0 * 2 - 1)
green = tuple(np.array([0, 120, 0]) / 255.0 * 2 - 1)
red = tuple(np.array([150, 0, 0]) / 255.0 * 2 - 1)
yellow = tuple(np.array([255, 255, 0]) / 255.0 * 2 - 1)
yellow_linecolor = tuple(np.array([255, 255, 0]) / 255.0 * 2 - 1)

TEXT_SIZE = 0.04 # Size of text

ET_SAMPLE_RADIUS = 0.1 # in deg

# SIze of calibration dots
TARGET_SIZE=0.6 # in deg
TARGET_SIZE_INNER=TARGET_SIZE / float(5)  # inner diameter of dot

HEAD_POS_CIRCLE_FIXED_COLOR = blue
HEAD_POS_CIRCLE_FIXED_RADIUS = 0.25

HEAD_POS_CIRCLE_MOVING_COLOR = yellow
HEAD_POS_CIRCLE_MOVING_FILLCOLOR = yellow
HEAD_POS_CIRCLE_MOVING_RADIUS = 0.25
HEAD_POS_CIRCLE_MOVING_MIN_RADIUS = 0.05


POS_CAL_BUTTON = (0.5, -0.8)
COLOR_CAL_BUTTON =  green
WIDTH_CAL_BUTTON = 0.30
HEIGHT_CAL_BUTTON = 0.08
CAL_BUTTON = 'space'
CAL_BUTTON_TEXT = 'calibrate (spacebar)'

POS_RECAL_BUTTON = (-0.5, -0.8)
COLOR_RECAL_BUTTON =  red
WIDTH_RECAL_BUTTON = 0.30
HEIGHT_RECAL_BUTTON = 0.08
RECAL_BUTTON = 'c'
RECAL_BUTTON_TEXT = 'calibrate (c)'

POS_REVAL_BUTTON = (-0.21, -0.8)
COLOR_REVAL_BUTTON =  red
WIDTH_REVAL_BUTTON = 0.30
HEIGHT_REVAL_BUTTON = 0.08
REVAL_BUTTON = 'v'
REVAL_BUTTON_TEXT = 'validate (v)'

# Button for showing eye images
POS_SETUP_BUTTON = (-0.5, -0.8)
COLOR_SETUP_BUTTON = blue
WIDTH_SETUP_BUTTON = 0.30
HEIGHT_SETUP_BUTTON = 0.08
SETUP_BUTTON = 'e'
SETUP_BUTTON_TEXT = 'eye images (e)'

POS_ACCEPT_BUTTON = (0.5, -0.8)
COLOR_ACCEPT_BUTTON = green
WIDTH_ACCEPT_BUTTON = 0.30
HEIGHT_ACCEPT_BUTTON = 0.08
ACCEPT_BUTTON = 'space'
ACCEPT_BUTTON_TEXT = 'accept (spacebar)'

POS_BACK_BUTTON = (-0.5, -0.8)
COLOR_BACK_BUTTON = blue
WIDTH_BACK_BUTTON = 0.30
HEIGHT_BACK_BUTTON = 0.08
BACK_BUTTON = 'b'
BACK_BUTTON_TEXT = 'basic (b)'

POS_GAZE_BUTTON = (0.8, 0.8)
COLOR_GAZE_BUTTON = blue
WIDTH_GAZE_BUTTON = 0.25
HEIGHT_GAZE_BUTTON = 0.08
GAZE_BUTTON = 'g'
GAZE_BUTTON_TEXT = 'show gaze (g)'

POS_CAL_IMAGE_BUTTON = (-0.8, 0.8)
COLOR_CAL_IMAGE_BUTTON = (0.2, 0.2, 0.2)
WIDTH_CAL_IMAGE_BUTTON = 0.25
HEIGHT_CAL_IMAGE_BUTTON = 0.08
CAL_IMAGE_BUTTON = 's'
CAL_IMAGE_BUTTON_TEXT = 'Show calibration (s)'

SETUP_DOT_OUTER_DIAMETER = 0.03 # Height unit
SETUP_DOT_INNER_DIAMETER = 0.005        

# Parameters for eye images
EYE_IMAGE_SIZE = (0.5, 0.25)
EYE_IMAGE_SIZE_PIX = (175, 496)
EYE_IMAGE_SIZE_PIX_FULL_FRAME = (512, 640)
EYE_IMAGE_POS_L = (0.5, -0.4)
EYE_IMAGE_POS_R = (-0.5, -0.4)

# Parameters for tracking monitor (norm units)
EYE_SIZE = 0.03
EYE_COLOR_VALID = green
EYE_COLOR_INVALID = red
TRACKING_MONITOR_SIZE = [0.5, 0.5]
TRACKING_MONITOR_POS = [0, 0.4]
TRACKING_MONITOR_COLOR = [0.2, 0.2, 0.2]
 


