# Import modules
from psychopy import visual, monitors
from psychopy import core, event
import numpy as np
import os, sys

# Insert the parent directory (where Titta is) to path
curdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(curdir) 
sys.path.insert(0,os.path.dirname(curdir)) 
from Titta import Titta, helpers_tobii as helpers

#%% Setup monitor for test

# Monitor/geometry 
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = True
SCREEN_RES                  = [1920, 1080]
SCREEN_WIDTH                = 52.7 # cm
VIEWING_DIST                = 63 #  # distance from eye to center of screen (cm)

mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)

mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)

# Monitor/geometry 
MY_MONITOR                  = 'default' # needs to exists in PsychoPy monitor center
FULLSCREEN_OP                  = False
SCREEN_RES_OP                  = [1680, 1050]
SCREEN_WIDTH                = 52.7 # cm
VIEWING_DIST                = 63 #  # distance from eye to center of screen (cm)

mon_op = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon_op.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon_op.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon_op.setSizePix(SCREEN_RES)

mon_op = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon_op.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon_op.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon_op.setSizePix(SCREEN_RES)



#%%
# Parameters
et_name = 'Spectrum' 
dummy_mode = False
     
# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile.tsv'

# Connect to eye tracker
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()
tracker.init()

# Window set-up (this color will be used for calibration)
win = visual.Window(monitor = mon, fullscr = FULLSCREEN,
                    screen=1, size=SCREEN_RES, units = 'deg')

win_op = visual.Window(monitor = mon_op, fullscr = FULLSCREEN_OP,
                    screen=0, size=SCREEN_RES_OP, units = 'norm')

text = visual.TextStim(win, text='')                    

                                  



# Calibrate 
tracker.calibrate(win, win_op)

# Start recording
tracker.start_recording(gaze_data=True, store_data=True)

# Present something
text.text = 'Recording. Press space to stop'
text.draw()
win.flip()
tracker.send_message('recording started')
        
event.waitKeys()
tracker.send_message('recording stopped')
tracker.stop_recording(gaze_data=True)

# Close window and save data
win.close()
tracker.save_data() 
core.quit()
