# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 17:51:15 2019

@author: Marcus
"""
from psychopy import visual, event, core
import numpy as np
import tobii_research

# Insert the parent directory (where Titta is) to path
from titta import Titta, helpers_tobii as helpers

 
win = visual.Window(screen=1)

# Parameters
et_name = 'Tobii Pro Spectrum'
dummy_mode = False
    
# Change any of the default dettings?
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile.tsv'

# Connect to eye tracker
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()
tracker.init()

# Start streaming of eye images
tracker.start_recording(gaze_data=True, user_position_guide=True, store_data = False)
core.wait(0.5)
    
if not tracker.get_latest_sample():
    win.close()
    raise ValueError('Eye tracker switched on?')
    
# sample = {}
# sample['left_gaze_origin_in_trackbox_coordinate_system'] = (0.45, 0.48, 0.52)
# sample['right_gaze_origin_in_trackbox_coordinate_system'] = (0.55, 0.52, 0.48)
# sample['right_gaze_origin_in_trackbox_coordinate_system'] = (np.nan, np.nan, np.nan)

# sample['left_pupil_diameter'] = 5
# sample['right_pupil_diameter'] = 5


et_head = helpers.EThead(win)

while 1:
#try:
    sample = tracker.get_latest_sample()
    sample_user_position = tracker.get_latest_user_position_guide_sample()

    latest_valid_bincular_avg, \
    previous_binocular_sample_valid,\
    latest_valid_yaw, \
    latest_valid_roll, \
    offset = et_head.update(sample, sample_user_position)
    # print(latest_valid_yaw, 
    # latest_valid_roll, 
    # latest_valid_bincular_avg)
 
    et_head.draw()
    win.flip()

    k = event.getKeys()
    if 'escape' in k:
        tracker.stop_recording(gaze_data=True, user_position_guide=True)
        win.close()
        break
    
tracker.stop_recording(gaze_data=True, user_position_guide=True, store_data = False)    
win.flip()
win.close()