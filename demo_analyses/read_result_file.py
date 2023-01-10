# -*- coding: utf-8 -*-
"""

@author: Marcus

Reads HDF5 file generated as part of the eye tracker output.
The HDF5 file contains (in case recorded) information about the eye tracker,
the calibration/validation results,
and streams recorded from the eye tracker.
"""

import h5py
import pandas as pd

# Files need to be loaded in this order
filename = 'testfile.h5'

# Load streams recorded from the eye tracker to pandas data frames
df_gaze = pd.read_hdf(filename, 'gaze')
df_msg = pd.read_hdf(filename, 'msg')
df_calibration_history = pd.read_hdf(filename, 'calibration_history')

# Read (if recorded)
df_time_sync = pd.read_hdf(filename, 'time_sync')
df_external_signal = pd.read_hdf(filename, 'external_signal')

# Read eye images (if recorded)
with h5py.File(filename, "r") as f:
    # Print all root level object names (aka keys)
    # these can be group or dataset names
    print("Keys: %s" % f.keys())

    # Read the eye_image group
    eye_image_group = f['eye_image']

    # Read eye images from group (each image is a HDF dataset)
    # eye_images is a list of 2D arrays (the eye images)
    eye_images = [i[:] for i in eye_image_group.values()] # Gives list of arrays with eye images
