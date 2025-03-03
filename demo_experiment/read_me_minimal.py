# -*- coding: utf-8 -*-
"""
Created on Mon Sep  4 09:36:50 2023

@author: Marcus
"""

# Import relevant modules
from psychopy import visual, core
from titta import Titta

# Get default settings for a supported eye tracker, change settings here if wanted (see other demos)
et_name = 'Tobii Pro Spectrum'
settings = Titta.get_defaults(et_name)

# Create an instance of Titta, connect to eye tracker and set settings
tracker = Titta.Connect(settings)
tracker.init()

# Open window (this window will be used for calibration) and calibrate eye tracker
win = visual.Window(size=(1920, 1080))
tracker.calibrate(win)

# Start recording
tracker.start_recording(gaze=True)

# Show your stimuli and log what was shown with eye tracker timestamp
win.flip()
tracker.send_message('shown stimulus 1')
core.wait(1)

# Stop recording
tracker.stop_recording(gaze=True)

# Close window and save data
win.close()
tracker.save_data()
