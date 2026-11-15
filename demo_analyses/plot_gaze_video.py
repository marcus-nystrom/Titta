# -*- coding: utf-8 -*-
"""
Created on Fri Nov  8 00:39:05 2024

@author: Bob
@contributer: Marcus
"""

import os
import pandas as pd
import numpy as np
import import_funcs as imp
import time
from pathlib import Path
try:
    import cv2
except ImportError:
    raise ImportError('OpenCV not found. pip install opencv-python')
else:
    from cv2 import VideoWriter, VideoWriter_fourcc

start = time.time()
verbose = True

opt = {}
# General variables for eye-tracking data
opt['xres']         = 1920.0                # maximum value of horizontal resolution in pixels
opt['yres']         = 1080.0                # maximum value of vertical resolution in pixels
opt['freq']         = 600.0                 # sampling frequency of data (check that this value matches with values actually obtained from measurement!)

# Video codec (FourCC). 'avc1' (H.264) gives small files that play almost
# everywhere, but needs an OpenCV built with an H.264 encoder (e.g. Debian's
# python3-opencv; the pip wheels often have none). If it cannot be opened,
# FALLBACK_CODEC is used instead. 'mp4v' (MPEG-4 Part 2) always works with
# OpenCV, but gives larger files that some players (e.g. browsers) cannot play.
VIDEO_CODEC = 'avc1'
FALLBACK_CODEC = 'mp4v'

# Maximum frame rate of the videos. The videos use the sampling frequency of
# the eye tracker, but at most MAX_VIDEO_FPS (e.g. 600 Hz -> 60 fps, 50 Hz ->
# 50 fps). Each frame shows the latest sample at that moment, so the video
# plays in real time and below MAX_VIDEO_FPS no sample is left out.
MAX_VIDEO_FPS = 60

# Data folder should be structured by one folder for each participant with the eye-tracking data in textfiles in each folder.
dir_path = os.path.dirname(os.path.realpath(__file__))
folders  = {}
folders['data']   = os.path.join(dir_path,'trials')         # folder in which data is stored (each folder in folders.data is considered 1 subject)
folders['output'] = os.path.join(dir_path,'output')         # folder for output (will use structure in folders.data for saving output)
folders['video_gaze'] = os.path.join(dir_path,'video_gaze') # folder for output (will use structure in folders.data for saving output)
folders['stimuli'] = os.path.join(dir_path,'stimuli')       # folder for output (will use structure in folders.data for saving output)

if not os.path.isdir(folders['video_gaze']):
   os.mkdir(folders['video_gaze'])


# %%
def add_transparency_cv2(overlay, image, alpha):
    ## image used in func must be a copy of image! The image from image can be original, original is fastest
    if alpha == 1:
        image_new = overlay
    else:
        image_new = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    return image_new

def open_video_writer(video_file_path, FPS, width, height):
    """Open a VideoWriter with VIDEO_CODEC, or FALLBACK_CODEC if that fails.

    Returns the writer and the codec that was used.
    """
    codecs = [VIDEO_CODEC]
    if FALLBACK_CODEC and FALLBACK_CODEC != VIDEO_CODEC:
        codecs.append(FALLBACK_CODEC)
    for codec in codecs:
        video = VideoWriter(video_file_path, VideoWriter_fourcc(*codec), float(FPS), (width, height))
        if video.isOpened():
            if codec != VIDEO_CODEC and codec not in fallback_reported:
                print(f"    Codec '{VIDEO_CODEC}' is not available in this OpenCV, using '{codec}'")
                fallback_reported.add(codec)
            return video, codec
        video.release()
    raise RuntimeError(f'Cannot write video {video_file_path} with codec(s) ' + ', '.join(codecs))

fallback_reported = set()

def create_gaze_video(data, fix, image_file_path, video_file_path, width, height, FPS, freq):
    do_fix_size = True
    radius = round(30 * height/1080)
    radius_fix = round(8 * height/1080)
    # The fixation dot grows by 1 pixel per fix_slowness samples of the eye
    # tracker (at its sampling frequency), independent of the frame rate
    fix_slowness = round(25 * height/1080)
    alpha = 0.7
    video, codec = open_video_writer(video_file_path, FPS, width, height)
    im_rgb = cv2.imread(image_file_path)

    sample_times = data['time'].to_numpy(dtype=float)
    L_X = np.round(data['L_X'].to_numpy(dtype=float))
    L_Y = np.round(data['L_Y'].to_numpy(dtype=float))
    R_X = np.round(data['R_X'].to_numpy(dtype=float))
    R_Y = np.round(data['R_Y'].to_numpy(dtype=float))

    # One frame every 1000 / FPS ms; each frame shows the latest sample
    frame_times = np.arange(0, sample_times[-1] + 1e-9, 1000 / FPS)
    samples = np.searchsorted(sample_times, frame_times, side='right') - 1

    for t, sample in zip(frame_times, samples):
        image = im_rgb.copy()

        if not np.isnan(L_X[sample]) and not np.isnan(L_Y[sample]):
            image = add_transparency_cv2(cv2.circle(image.copy(), (int(L_X[sample]), int(L_Y[sample])), radius, (0, 0, 255), -1), image, alpha)
        if not np.isnan(R_X[sample]) and not np.isnan(R_Y[sample]):
            image = add_transparency_cv2(cv2.circle(image.copy(), (int(R_X[sample]), int(R_Y[sample])), radius, (255, 0, 0), -1), image, alpha)

        nfix = len(fix['dur'])
        for fixnr in range(nfix):
            if t >= fix['startT'][fixnr] and t <= fix['endT'][fixnr]:
                # Samples since the start of this fixation, so the dot grows
                # at the same speed at any frame rate
                counter = (t - fix['startT'][fixnr]) * freq / 1000 if do_fix_size else 0
                image = add_transparency_cv2(cv2.circle(image.copy(), (round(fix['xpos'][fixnr]), round(fix['ypos'][fixnr])), round(radius_fix+counter/fix_slowness), (0, 255, 0), -1), image, alpha)

        video.write(image)
    print('    Saving video to: ' + video_file_path + ' (' + codec + ')')
    video.release()

# %%

# Get all participant folders
fold = list(os.walk(folders['data']))
all_folders = [f[0] for f in fold[1:]]
number_of_folders = len(all_folders)

# Get all files
all_files = [f[2] for f in fold[1:]]
number_of_files = [len(f) for f in all_files]

# Read files with fixations generated with the I2MC
df_fixations = pd.read_csv(Path.cwd() / 'output' / 'allfixations.txt', sep='\t')

for folder_idx, folder in enumerate(all_folders):
    if verbose:
        print('Processing folder {} of {}'.format(folder_idx + 1, number_of_folders))
    participant = folder.split(os.sep)[-1]

    if number_of_files[folder_idx] == 0:
        if verbose:
            print('  folder is empty, continuing to next folder')
        continue

    for file_idx, file in enumerate(all_files[folder_idx]):
        if verbose:
            print('  Processing file {} of {}'.format(file_idx + 1, number_of_files[folder_idx]))

        # make output folder
        outVideoFold = os.path.join(folders['video_gaze'], participant)
        if not os.path.isdir(outVideoFold):
           os.mkdir(outVideoFold)

        file_name = os.path.join(folder, file)
        stimulus_name = os.path.splitext(file)[0]

        ## IMPORT DATA
        if verbose:
            print('    Loading data from: {}'.format(file_name))
        data = imp.Titta(file_name, [opt['xres'], opt['yres']])

        # check whether we have data, if not, continue to next file
        if len(data['time']) == 0:
            if verbose:
                print('    No data found in file')
            continue

        df_temp = df_fixations[(df_fixations.trial == stimulus_name) & \
                               (df_fixations.participant == participant)].reset_index()

        image_file_path = os.path.join(folders['stimuli'], stimulus_name)
        video_file_path = os.path.join(outVideoFold, stimulus_name +'.mp4')
        fps = min(MAX_VIDEO_FPS, opt['freq'])
        create_gaze_video(data, df_temp, image_file_path, video_file_path, round(opt['xres']), round(opt['yres']), fps, opt['freq'])

print('\n\nI2MC took {}s to finish!'.format(time.time()-start))
