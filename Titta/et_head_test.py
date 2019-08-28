# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 17:51:15 2019

@author: Marcus
"""
5
from psychopy import visual, event
import helpers_tobii as helpers
import numpy as np


sample = {}
sample['left_gaze_origin_in_trackbox_coordinate_system'] = (0.45, 0.48, 0.52)
sample['right_gaze_origin_in_trackbox_coordinate_system'] = (0.55, 0.52, 0.48)
sample['right_gaze_origin_in_trackbox_coordinate_system'] = (np.nan, np.nan, np.nan)

sample['left_pupil_diameter'] = 5
sample['right_pupil_diameter'] = 5

win = visual.Window()
et_head = helpers.EThead(win)

#try:
latest_valid_yaw = 0 
latest_valid_roll = 0
latest_valid_bincular_avg = (0.5, 0.5, 0.5)

latest_valid_yaw, 
latest_valid_roll, 
latest_valid_bincular_avg = et_head.update(sample,
latest_valid_bincular_avg,                                           
latest_valid_yaw, 
latest_valid_roll, 
)
#except:
#win.close()
 
et_head.draw()

event.waitKeys()

win.flip()
win.close()