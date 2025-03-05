# Import relevant modules
import pandas as pd
from psychopy import visual, monitors, core
import numpy as np
import matplotlib.pyplot as plt
from titta import Titta, helpers_tobii as helpers
import h5py

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
stimulus_duration = 3

# %%  ET settings
et_name = 'Tobii Pro Spectrum'
# et_name = 'IS4_Large_Peripheral'
# et_name = 'Tobii Pro Nano'

# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile'
settings.N_CAL_TARGETS = 5
settings.DEBUG = False

# Use settings.__dict__ to see all available settings

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
    win_op = visual.Window(monitor = mon_op, fullscr = FULLSCREEN_OP,
                    screen=0, size=SCREEN_RES_OP, units = 'norm', waitBlanking=False)
    '''
    Note that waitBlanking is set to False, because the screens are flipped serially and the screens are not exactly in sync.
    Setting waitBlanking to True can make drawing on the operator screen slow and choppy.
    '''

fixation_point = helpers.MyDot2(win)

images = []
for im_name in im_names:
    images.append(visual.ImageStim(win, image=im_name, units='norm', size=(2, 2)))

#  Calibrate
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

# %% Record some data. Normally only gaze stream is started
# Note that the recording is started a while after
# start_recording() is called (about 150 ms on the Spectrum).
# If you do not want start_recording() to return until data become available, set the argument
# block_until_data_available=True (default is False, currently only implemented for the 'gaze' stream)
# Best practise: start the eye tracker, wait a while, and them start your experiment.
tracker.start_recording(gaze=True,
                        time_sync=True,
                        eye_image=False,
                        notifications=True,
                        external_signal=True,
                        positioning=True)

core.wait(0.5)

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
    sample = tracker.buffer.peek_N('gaze', 1)

    # Get the 10 most recent samples
    # sample = tracker.buffer.peek_N('gaze', 10)

    # Same as peek_N, but clears the buffer
    # sample = tracker.buffer.consume_N('gaze', 10)

    # Consumes from a time range (t0 -> t1)
    # sample = tracker.buffer.consume_time_range('gaze', t0, t1)

    # print(sample['left_gaze_point_on_display_area_x'])
    # print(sample['right_gaze_point_on_display_area_x'])

win.flip()

# Stop streams (if available). Normally only gaze stream is stopped
tracker.stop_recording(gaze=True,
                       time_sync=True,
                       eye_image=False,
                       notifications=True,
                       external_signal=True,
                       positioning=True)

# Close window and save data
win.close()
if dual_screen_setup:
    win_op.close()
tracker.save_data()

# %% Read the gaze stream from the HDF5 container
if not dummy_mode:
    filename = settings.FILENAME + '.h5'

    # Find out what is recorded
    with h5py.File(filename, "r") as f:
        # Print all root level object names (aka keys)
        # these can be group or dataset names
        keys = [key for key in f.keys()]
        print(f'HDF5 keys: {keys}')

        for k in f.attrs.keys():
            print(f"{k} => {f.attrs[k]}")

    # Load streams recorded from the eye tracker to pandas data frames
    df_gaze = pd.read_hdf(filename, 'gaze')
    df_msg = pd.read_hdf(filename, 'msg')
    df_calibration_history = pd.read_hdf(filename, 'calibration_history')
    df_log = pd.read_hdf(filename, 'log')

    # These may not be available
    if "time_sync" in keys:
        df_time_sync = pd.read_hdf(filename, 'time_sync')
    if "external_signal" in keys:
        df_external_signal = pd.read_hdf(filename, 'external_signal')
    if "notification" in keys:
        df_notification = pd.read_hdf(filename, 'notification')

    # Read eye images (if recorded)
    if "eye_image" in keys:
        with h5py.File(filename, "r") as f:
            # Print all root level object names (aka keys)
            # these can be group or dataset names
            print("Keys: %s" % f.keys())

            # Read the eye_image group
            eye_image_group = f.get('eye_image')
            print("Groupe items: %s" % eye_image_group.items())

            # Read eye images from group (each image is a HDF dataset)
            # eye_images is a list of 2D arrays (the eye images)
            eye_images = [i[:] for i in eye_image_group.values()] # Gives list of arrays with eye images

        eye_image_metadata = pd.read_hdf(filename, 'eye_metadata')

    # %% Plot some data

    # plt.close('all')
    # plt.plot(np.diff(df_gaze['system_time_stamp']))

    plt.figure()
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


'''
These are all available fields from the gaze stream:
    (see, https://developer.tobiipro.com/commonconcepts/coordinatesystems.html)
        'device_time_stamp', 'system_time_stamp',
       'left_gaze_point_on_display_area_x',
       'left_gaze_point_on_display_area_y',
       'left_gaze_point_in_user_coordinates_x',
       'left_gaze_point_in_user_coordinates_y',
       'left_gaze_point_in_user_coordinates_z', 'left_gaze_point_valid',
       'left_gaze_point_available', 'left_pupil_diameter', 'left_pupil_valid',
       'left_pupil_available', 'left_gaze_origin_in_user_coordinates_x',
       'left_gaze_origin_in_user_coordinates_y',
       'left_gaze_origin_in_user_coordinates_z',
       'left_gaze_origin_in_track_box_coordinates_x',
       'left_gaze_origin_in_track_box_coordinates_y',
       'left_gaze_origin_in_track_box_coordinates_z', 'left_gaze_origin_valid',
       'left_gaze_origin_available', 'left_eye_openness_diameter',
       'left_eye_openness_valid', 'left_eye_openness_available',
       'right_gaze_point_on_display_area_x',
       'right_gaze_point_on_display_area_y',
       'right_gaze_point_in_user_coordinates_x',
       'right_gaze_point_in_user_coordinates_y',
       'right_gaze_point_in_user_coordinates_z', 'right_gaze_point_valid',
       'right_gaze_point_available', 'right_pupil_diameter',
       'right_pupil_valid', 'right_pupil_available',
       'right_gaze_origin_in_user_coordinates_x',
       'right_gaze_origin_in_user_coordinates_y',
       'right_gaze_origin_in_user_coordinates_z',
       'right_gaze_origin_in_track_box_coordinates_x',
       'right_gaze_origin_in_track_box_coordinates_y',
       'right_gaze_origin_in_track_box_coordinates_z',
       'right_gaze_origin_valid', 'right_gaze_origin_available',
       'right_eye_openness_diameter', 'right_eye_openness_valid',
       'right_eye_openness_available']
'''