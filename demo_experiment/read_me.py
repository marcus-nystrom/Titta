# Import relevant modules
import pandas as pd
from psychopy import visual, monitors
import numpy as np
import matplotlib.pyplot as plt
from titta import Titta, helpers_tobii as helpers

dummy_mode = False
bimonocular_calibration = False
dual_screen_setup = False

# %%  Monitor/geometry
MY_MONITOR = 'testMonitor'  # needs to exists in PsychoPy monitor center
FULLSCREEN = True
SCREEN_RES = [1920, 1080]
SCREEN_WIDTH = 52.7  # cm
VIEWING_DIST = 63  # distance from eye to center of screen (cm)

monitor_refresh_rate = 60  # frames per second (fps)
mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)

if dual_screen_setup:
    # Monitor/geometry operator screen
    MY_MONITOR_OP                  = 'default' # needs to exists in PsychoPy monitor center
    FULLSCREEN_OP                  = False
    SCREEN_RES_OP                  = [1920, 1080]
    SCREEN_WIDTH_OP                = 52.7 # cm
    VIEWING_DIST_OP                = 63 #  # distance from eye to center of screen (cm)

    mon_op = monitors.Monitor(MY_MONITOR_OP)  # Defined in defaults file
    mon_op.setWidth(SCREEN_WIDTH_OP)          # Width of screen (cm)
    mon_op.setDistance(VIEWING_DIST_OP)       # Distance eye / monitor (cm)
    mon_op.setSizePix(SCREEN_RES_OP)


im_names = ['im1.jpeg', 'im2.jpeg', 'im3.jpeg']
stimulus_duration = 0.1

# %%  ET settings
et_name = 'Tobii Pro Spectrum'
# et_name = 'IS4_Large_Peripheral'
# et_name = 'Tobii Pro Nano'

# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile.tsv'
settings.N_CAL_TARGETS = 5

# Example of how to change the graphics; here, the color of the 'start calibration' button
# settings.graphics.COLOR_CAL_BUTTON = 'green'
# settings.graphics.TEXT_COLOR = 'green'

# %% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()
tracker.init()

# Window set-up (this color will be used for calibration)
win = visual.Window(monitor=mon, fullscr=FULLSCREEN,
                    screen=1, size=SCREEN_RES, units='deg')
if dual_screen_setup:
    win_op = visual.Window(monitor = mon_op, fullscr = FULLSCREEN,
                    screen=0, size=SCREEN_RES, units = 'norm')

fixation_point = helpers.MyDot2(win)

images = []
for im_name in im_names:
    images.append(visual.ImageStim(win, image=im_name, units='norm', size=(2, 2)))

#  Calibratse
if bimonocular_calibration:
    if dual_screen_setup:
        tracker.calibrate(win, win_operator=win_op, eye='left', calibration_number = 'first')
        tracker.calibrate(win, win_operator=win_op, eye='right', calibration_number = 'second')
    else:
        tracker.calibrate(win, eye='left', calibration_number='first')
        tracker.calibrate(win, eye='right', calibration_number='second')
else:
    if dual_screen_setup:
        tracker.calibrate(win, win_operator=win_op)
    else:
        tracker.calibrate(win)

# %% Record some data
tracker.start_recording(gaze=True)

# Present fixation dot and wait for one second
for i in range(monitor_refresh_rate):
    fixation_point.draw()
    t = win.flip()
    if i == 0:
        tracker.send_message('fix on')

tracker.send_message('fix off')

# Wait exactly 3 * fps frames (3 s)
np.random.shuffle(images)
for image in images:
    im_name = image.image
    for i in range(int(stimulus_duration * monitor_refresh_rate)):
        image.draw()
        t = win.flip()
        if i == 0:
            tracker.send_message(''.join(['onset_', im_name]))

    tracker.send_message(''.join(['offset_', im_name]))

    # Exaple of how to get the most recent gaze sample
    sample = tracker.buffer.peekN('gaze', 1)

    # Get the 10 most recent samples
    # sample = tracker.buffer.peekN('gaze', 10)

    # print(sample['left_gaze_on_display_area_x'])
    # print(sample['right_gaze_on_display_area_x'])

win.flip()
tracker.stop_recording(gaze=True)

# Close window and save data
win.close()
if dual_screen_setup:
    win_op.close()
tracker.save_data()  # Also save screen geometry from the monitor object

# %% Read the gaze stream from the HDF5 container
filename = settings.FILENAME[:-4] + '.h5'
df_gaze = pd.read_hdf(filename, 'gaze')

# %%
# Plot some data (e.g., the horizontal data from the left eye)
plt.close('all')
t = (df_gaze['system_time_stamp'] - df_gaze['system_time_stamp'][0]) / 1000
plt.plot(t, df_gaze['left_gaze_point_on_display_area_x'])
plt.plot(t, df_gaze['left_gaze_point_on_display_area_y'])
plt.xlabel('Time (ms)')
plt.ylabel('x/y coordinate (normalized units)')
plt.legend(['x', 'y'])

plt.figure()
plt.plot(t, df_gaze['left_eye_openness_diameter'])
plt.plot(t, df_gaze['right_eye_openness_diameter'])
plt.xlabel('Time (ms)')
plt.ylabel('Eye openness (mm)')
plt.legend(['left', 'right'])
plt.show()
