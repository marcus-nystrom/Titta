# -*- coding: utf-8 -*-
"""
Created on Mon March 3 08:39:57 2019

@author: Marcus

Reads pickle file generated as part of the eye tracker output.
The pickle contains (in case recorded) information about the eye tracker,
the calibration/validation results,
synchronization data, eye-tracker data,
messages, and eye images (if recorded).

The columns in 'gaze_data_container' represent (in this order).
    ['device_time_stamp',
    'system_time_stamp',
    'left_gaze_point_on_display_area_x',
    'left_gaze_point_on_display_area_y',
    'left_gaze_point_in_user_coordinate_system_x',
    'left_gaze_point_in_user_coordinate_system_y',
    'left_gaze_point_in_user_coordinate_system_z',
    'left_gaze_origin_in_trackbox_coordinate_system_x',
    'left_gaze_origin_in_trackbox_coordinate_system_y',
    'left_gaze_origin_in_trackbox_coordinate_system_z',
    'left_gaze_origin_in_user_coordinate_system_x',
    'left_gaze_origin_in_user_coordinate_system_y',
    'left_gaze_origin_in_user_coordinate_system_z',
    'left_pupil_diameter',
    'left_pupil_validity',
    'left_gaze_origin_validity',
    'left_gaze_point_validity',
    'right_gaze_point_on_display_area_x',
    'right_gaze_point_on_display_area_y',
    'right_gaze_point_in_user_coordinate_system_x',
    'right_gaze_point_in_user_coordinate_system_y',
    'right_gaze_point_in_user_coordinate_system_z',
    'right_gaze_origin_in_trackbox_coordinate_system_x',
    'right_gaze_origin_in_trackbox_coordinate_system_y',
    'right_gaze_origin_in_trackbox_coordinate_system_z',
    'right_gaze_origin_in_user_coordinate_system_x',
    'right_gaze_origin_in_user_coordinate_system_y',
    'right_gaze_origin_in_user_coordinate_system_z',
    'right_pupil_diameter',
    'right_pupil_validity',
    'right_gaze_origin_validity',
    'right_gaze_point_validity']

For more information about these variables, see Tobii Pro SDK documentation.


"""

from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import moviepy.editor as mpy
import os
import sys

if sys.version_info[0] == 3: # if Python 3:
    from io import BytesIO as StringIO
    import pickle
else: # else Python 2
    from cStringIO import StringIO
    import cPickle as pickle


EYE_IMAGE_SIZE_PIX = (175, 496)
EYE_IMAGE_SIZE_PIX_FULL_FRAME = (512, 640)

# Files need to be loaded in this order
f = open("testfile.pkl", 'rb')
gaze_data_container = pickle.load(f)
msg_container = pickle.load(f)
eye_openness_data_container = pickle.load(f)
external_signal_container = pickle.load(f)
sync_data_container = pickle.load(f)
stream_errors_container = pickle.load(f)
image_data_container = pickle.load(f)
calibration_history = pickle.load(f)
system_info = pickle.load(f)
# settings = pickle.load(f)
# python_version = pickle.load(f)

# And additional stuff if you pickeled something optional during the
# call to 'save_data()'

f.close()


#%% Save eye images to file
list_of_images = []
for i, eye_image in enumerate(image_data_container):

    ''' eye_image is a dict with keys
    device_time_stamp
 	Gets the time stamp according to the eye tracker's internal clock.

 	system_time_stamp
 	Gets the time stamp according to the computer's internal clock.

 	camera_id
 	Gets which camera generated the image.

 	image_type
    Gets the type of eye image as a string.
    Valid values are EYE_IMAGE_TYPE_FULL and EYE_IMAGE_TYPE_CROPPED.

 	image_data
 	Gets the image data sent by the eye tracker in GIF format.
    '''

    # Get time stamps
    print(eye_image['system_time_stamp'], eye_image['device_time_stamp'],
          eye_image['camera_id'])

    # Convert image to numpy array
    temp_im = StringIO(eye_image['image_data'])
    tim = Image.open(temp_im)
    tim.save(os.getcwd() + os.sep + 'images' + os.sep + str(eye_image['system_time_stamp']) + ".gif","GIF")

