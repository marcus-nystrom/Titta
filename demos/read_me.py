# Import relevant modules
import pickle
import pandas as pd
from psychopy import visual, monitors
import numpy as np
import matplotlib.pyplot as plt
from titta import Titta, helpers_tobii as helpers


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
im_names = ['im1.jpeg', 'im2.jpeg', 'im3.jpeg']
stimulus_duration = 3

# %%  ET settings
et_name = 'Tobii Pro Spectrum'
# et_name = 'IS4_Large_Peripheral'
# et_name = 'Tobii Pro Nano'

dummy_mode = False
bimonocular_calibration = False

# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile.tsv'
settings.N_CAL_TARGETS = 5

# %% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()
tracker.init()

# Window set-up (this color will be used for calibration)
win = visual.Window(monitor=mon, fullscr=FULLSCREEN,
                    screen=1, size=SCREEN_RES, units='deg')

fixation_point = helpers.MyDot2(win)

images = []
for im_name in im_names:
    images.append(visual.ImageStim(win, image=im_name, units='norm', size=(2, 2)))

#  Calibratse
if bimonocular_calibration:
    tracker.calibrate(win, eye='left', calibration_number='first')
    tracker.calibrate(win, eye='right', calibration_number='second')
else:
    tracker.calibrate(win)

# %% Record some data
tracker.start_recording(gaze_data=True, store_data=True)

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
    for i in range(stimulus_duration * monitor_refresh_rate):
        image.draw()
        t = win.flip()
        if i == 0:
            tracker.send_message(''.join(['onset_', im_name]))
		
    tracker.send_message(''.join(['offset_', im_name]))

win.flip()
tracker.stop_recording(gaze_data=True)

# Close window and save data
win.close()
tracker.save_data(mon)  # Also save screen geometry from the monitor object

# %% Open some parts of the pickle and write et-data and messages to tsv-files.
f = open(settings.FILENAME[:-4] + '.pkl', 'rb')
gaze_data = pickle.load(f)
msg_data = pickle.load(f)
eye_openness_data = pickle.load(f)

#  Save data and messages
df_msg = pd.DataFrame(msg_data,  columns=['system_time_stamp', 'msg'])
df_msg.to_csv(settings.FILENAME[:-4] + '_msg.tsv', sep='\t')

df = pd.DataFrame(gaze_data, columns=tracker.header)
df_eye_openness = pd.DataFrame(eye_openness_data,  columns=['device_time_stamp',
                                                            'system_time_stamp',
                                                            'left_eye_validity',
                                                            'left_eye_openness_value',
                                                            'right_eye_validity',
                                                            'right_eye_openness_value'])

# Add the eye openness signal to the dataframe containing gaze data
df_etdata = pd.merge(df, df_eye_openness, on=['system_time_stamp'])
df_etdata.to_csv(settings.FILENAME[:-4] + '.tsv', sep='\t')

# Plot some data (e.g., the horizontal data from the left eye)
t = (df_etdata['system_time_stamp'] - df_etdata['system_time_stamp'][0]) / 1000
plt.plot(t, df_etdata['left_gaze_point_on_display_area_x'])
plt.plot(t, df_etdata['left_gaze_point_on_display_area_y'])
plt.xlabel('Time (ms)')
plt.ylabel('x/y coordinate (normalized units)')
plt.legend(['x', 'y'])
# plt.show()

plt.figure()
plt.plot(t, df_etdata['left_eye_openness_value'])
plt.plot(t, df_etdata['right_eye_openness_value'])
plt.xlabel('Time (ms)')
plt.ylabel('Eye openness (mm)')
plt.legend(['left', 'right'])
plt.show()
