# Import relevant modules
import pandas as pd
import matplotlib.pyplot as plt
from titta import Titta
import time
import h5py

# %%  ET settings
et_name = 'Tobii Pro Spectrum'

# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile'
settings.N_CAL_TARGETS = 5

# %% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
tracker.init()

# %% Record some data
tracker.start_recording(gaze=True,
                            time_sync=True,
                            eye_image=True,
                            notifications=True,
                            external_signal=True,
                            positioning=True)
tracker.send_message('test')
time.sleep(3)
tracker.stop_recording(gaze=True,
                            time_sync=True,
                            eye_image=True,
                            notifications=True,
                            external_signal=True,
                            positioning=True)

tracker.save_data()

# %% Read the gaze stream from the HDF5 container
filename = settings.FILENAME + '.h5'

# Load streams recorded from the eye tracker to pandas data frames
df_gaze = pd.read_hdf(filename, 'gaze')
df_msg = pd.read_hdf(filename, 'msg')

df_calibration_history = pd.read_hdf(filename, 'calibration_history')

df_time_sync = pd.read_hdf(filename, 'time_sync')
df_external_signal = pd.read_hdf(filename, 'external_signal')
df_notification = pd.read_hdf(filename, 'notification')

# Read eye images (if recorded)
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
