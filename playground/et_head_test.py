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
tracker.start_recording(gaze=True, positioning=True)
core.wait(1)
et_head = helpers.EThead(win)

while 1:
#try:
    sample = tracker.buffer.peek_N('gaze', 1)
    sample_user_position = tracker.buffer.peek_N('positioning', 1)
    latest_valid_bincular_avg, \
    previous_binocular_sample_valid,\
    latest_valid_yaw, \
    latest_valid_roll, \
    offset = et_head.update(sample, sample_user_position)

    et_head.draw()
    win.flip()

    k = event.getKeys()
    if 'escape' in k:
        tracker.stop_recording(gaze=True, positioning=True)
        win.close()
        break

tracker.stop_recording(gaze=True, positioning=True)
win.flip()
win.close()