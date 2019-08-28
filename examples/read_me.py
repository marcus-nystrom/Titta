# Import modules
from psychopy import visual, monitors
from psychopy import core, event, gui
import numpy as np
import os, sys
import tobii_research

# Insert the parent directory (where Titta is) to path
curdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(curdir)
sys.path.insert(0,os.path.dirname(curdir)) 
from Titta import Titta, helpers_tobii as helpers


# Parameters
et_name = 'Spectrum'
dummy_mode = False
    
# Change any of the default dettings?
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile.tsv'

# Connect to eye tracker
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()
tracker.init()

# Window set-up (this color will be used for calibration)
win = visual.Window(monitor = settings.mon, fullscr = settings.FULLSCREEN,
                    screen=1, size=settings.SCREEN_RES, units = 'deg')
print(win.size)

text = visual.TextStim(win, text='')                    

                                  




# Calibrate 
tracker.calibrate(win)

# Start recording
tracker.start_recording(gaze_data=True, store_data=True)

# Present something
text.text = 'Recording. Press space to stop'
text.draw()
win.flip()
tracker.send_message('recording started')
        
event.waitKeys(['space'])
tracker.send_message('recording stopped')
tracker.stop_recording(gaze_data=True)

# Close window and save data
win.close()
tracker.save_data() 
core.quit()
