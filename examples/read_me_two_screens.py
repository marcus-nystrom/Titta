# Import modules
import cPickle as pickle
import pandas as pd
from psychopy import visual, monitors
from psychopy import core, event
import numpy as np
import os, sys

# Insert the parent directory (where Titta is) to path
curdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(curdir)
sys.path.insert(0, os.sep.join([os.path.dirname(curdir)])) 
from titta import Titta, helpers_tobii as helpers

#%% Monitor/geometry participant screen
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = True
SCREEN_RES                  = [1920, 1080]
SCREEN_WIDTH                = 52.7 # cm
VIEWING_DIST                = 63 #  # distance from eye to center of screen (cm)

mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)

# Monitor/geometry operator screen
MY_MONITOR_OP                  = 'default' # needs to exists in PsychoPy monitor center
FULLSCREEN_OP                  = True
SCREEN_RES_OP                  = [1920, 1080]
SCREEN_WIDTH_OP                = 52.7 # cm
VIEWING_DIST_OP                = 63 #  # distance from eye to center of screen (cm)

mon_op = monitors.Monitor(MY_MONITOR_OP)  # Defined in defaults file
mon_op.setWidth(SCREEN_WIDTH_OP)          # Width of screen (cm)
mon_op.setDistance(VIEWING_DIST_OP)       # Distance eye / monitor (cm)
mon_op.setSizePix(SCREEN_RES_OP)

# Window set-up (this color will be used for calibration)
win = visual.Window(monitor = mon, fullscr = FULLSCREEN,
                    screen=1, size=SCREEN_RES, units = 'deg')

win_op = visual.Window(monitor = mon_op, fullscr = FULLSCREEN_OP,
                    screen=0, size=SCREEN_RES_OP, units = 'norm')

fixation_point = helpers.MyDot2(win)
image = visual.ImageStim(image=, units='norm', size = (2, 2))

#%% ET settings
et_name = 'Tobii Pro Spectrum' 
# et_name = 'Tobii4C' 

dummy_mode = False
bimonocular_calibration = False
     
# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile.tsv'

#%% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()
tracker.init()
   
# Calibrate 
if bimonocular_calibration:
    tracker.calibrate(win, win_operator=win_op, eye='left', calibration_number = 'first')
    tracker.calibrate(win, win_operator=win_op, eye='right', calibration_number = 'second')
else:
    tracker.calibrate(win, win_operator=win_op)

#%% Record some data
tracker.start_recording(gaze_data=True, store_data=True)

# Present fixation dot and wait for one second
fixation_point.draw()
t = win.flip()
tracker.send_message('fixation target onset')
core.wait(1)
tracker.send_message('fixation target offset')

image.draw()
t = win.flip()
tracker.send_message('image onset')
core.wait(3)
tracker.send_message('image offset')

win.flip()

tracker.stop_recording(gaze_data=True)

# Close window and save data
win.close()
win_op.close()
tracker.save_data() 

#%% Open pickle and write et-data and messages to tsv-files.
f = open(settings.FILENAME[:-4] + '.pkl', 'rb')
gaze_data = pickle.load(f)
msg_data = pickle.load(f)

# Save data and messages 
df = pd.DataFrame(gaze_data, columns=tracker.header)
df.to_csv(settings.FILENAME[:-4] + '.tsv', sep='\t')
df_msg = pd.DataFrame(msg_data,  columns = ['system_time_stamp', 'msg'])
df_msg.to_csv(self.filename[:-4] + '_msg.tsv', sep='\t')            

core.quit()
