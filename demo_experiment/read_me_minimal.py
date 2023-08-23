# Import relevant modules
from psychopy import visual, core
from titta import Titta

# Create an instance of titta
et_name = 'Tobii Pro Spectrum'
settings = Titta.get_defaults(et_name)

# Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
tracker.init()

# Window set-up (this color will be used for calibration)
win = visual.Window(size=(1920, 1080))
tracker.calibrate(win)

# Start recording
tracker.start_recording(gaze=True)

# Show your stimuli
win.flip()
core.wait(1)

# Stop recording
tracker.stop_recording(gaze=True)

# Close window and save data
win.close()
tracker.save_data()
