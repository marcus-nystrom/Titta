# -*- coding: utf-8 -*-
# =============================================================================
# =============================================================================
# #  FIXATION DETECTION USING THE IDENTIFICATION BY 2-MEANS CLUSTERING (I2MC) ALGORITHM
#
# Translated to python from Matlab by Jonathan van Leeuwen, Diederick Niehorster
# 2019--2022 - https://github.com/dcnieho/I2MC_Python
#
# =============================================================================
# =============================================================================
# Description:
# The I2MC algorithm was designed to accomplish fixation detection in data
# across a wide range of noise levels and when periods of data loss may
# occur.
#
# Cite as:
# Hessels, R.S., Niehorster, D.C., Kemner, C., & Hooge, I.T.C., (2017).
# Noise-robust fixation detection in eye-movement data - Identification by
# 2-means clustering (I2MC). Behavior Research Methods, 49(5):1802-1823.
#
# For more information, questions, or to check whether we have updated to a
# better version, see https://github.com/dcnieho/I2MC_Python. I2MC can be
# installed using pip install I2MC
#
# Most parts of the I2MC algorithm are licensed under the Creative Commons
# Attribution 4.0 (CC BY 4.0) license. Some functions are under MIT
# license, and some may be under other licenses.
#
# Quick start guide for adopting this script for your own data:
# 1) Build an import function specific for your data (see importTobiiTX300
# for an example).
#
# 2) Change the line calling the data import function under the comment
# "IMPORT DATA" to use your new import function. The format should be:
#
# data['time'] for the timestamp
# data['L_X'] & data['L_Y'] for left gaze coordinates
# data['R_X'] & data['R_Y'] for right gaze coordinates
# data['average_X'] & data['average_Y'] for average gaze coordinates
#
# You may provide coordinates from both eyes, only the left, only the
# right, or only the average.
# Gaze coordinates should be in pixels, timestamps should be in milliseconds
#
# 3) Adjust the variables in the "necessary variables" section to match your
#    data
# 4) Run the algorithm
#
#
# Tested on Python 3.8

# =============================================================================
# Initialize
# =============================================================================
import os
import sys
import pandas as pd
import numpy as np
import import_funcs as imp
try:
    import I2MC
    import I2MC.plot
except ImportError:
    raise ImportError('I2MC not found. pip install I2MC')
import matplotlib.pyplot as plt
import time
try:
    import cv2
except ImportError:
    print("Could not import OpenCV for video processing, creation of gaze videos is disabled")
    use_cv2 = False
else:
    from cv2 import VideoWriter, VideoWriter_fourcc
    use_cv2 = True

start = time.time()


# =============================================================================
# NECESSARY FUNCTIONS
# =============================================================================

# %%
def add_transparency_cv2(overlay, image, alpha):
    ## image used in func must be a copy of image! The image from image can be original, original is fastest
    if alpha == 1:
        image_new = overlay
    else:
        image_new = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    return image_new

def create_gaze_video(data, fix, image_file_path, video_file_path, width, height, FPS):
    counter = 0
    radius = round(30 * height/1080)
    radius_fix = round(8 * height/1080)
    fix_slowness = round(25 * height/1080)
    alpha = 0.7
    fourcc = VideoWriter_fourcc(*'avc1')

    video = VideoWriter(video_file_path, fourcc, float(FPS), (width, height))
    im_rgb = cv2.imread(image_file_path)

    for sample in data.index:
        nfix = len(fix['dur'])
        fixlist = np.full((nfix), False)
        image = im_rgb.copy()

        L_X = np.round(data['L_X'][sample])
        L_Y = np.round(data['L_Y'][sample])
        R_X = np.round(data['R_X'][sample])
        R_Y = np.round(data['R_Y'][sample])
        t = int(np.round(data['time'][sample]))

        if not np.isnan(L_X) and not np.isnan(L_Y):
            image = add_transparency_cv2(cv2.circle(image.copy(), (int(L_X), int(L_Y)), radius, (0, 0, 255), -1), image, alpha)
        if not np.isnan(R_X) and not np.isnan(R_Y):
            image = add_transparency_cv2(cv2.circle(image.copy(), (int(R_X), int(R_Y)), radius, (255, 0, 0), -1), image, alpha)

        for fixnr in range(nfix):
            if t >= fix['startT'][fixnr] and t <= fix['endT'][fixnr]:
                fixlist[fixnr] = True
                image = add_transparency_cv2(cv2.circle(image.copy(), (round(fix['xpos'][fixnr]), round(fix['ypos'][fixnr])), round(radius_fix+counter/fix_slowness), (0, 255, 0), -1), image, alpha)
            else:
                fixlist[fixnr] = False

        if do_fix_size and True in fixlist:
            counter += 1
        else:
            counter = 0

        video.write(image)
    print('    Saving video to: ' + video_file_path)
    video.release()

# %%

# =============================================================================
# NECESSARY VARIABLES
# =============================================================================
opt = {}
# General variables for eye-tracking data
opt['xres']         = 1920.0                # maximum value of horizontal resolution in pixels
opt['yres']         = 1080.0                # maximum value of vertical resolution in pixels
opt['missingx']     = -opt['xres']          # missing value for horizontal position in eye-tracking data (example data uses -xres). used throughout the algorithm as signal for data loss
opt['missingy']     = -opt['yres']          # missing value for vertical position in eye-tracking data (example data uses -yres). used throughout algorithm as signal for data loss
opt['freq']         = 600.0                 # sampling frequency of data (check that this value matches with values actually obtained from measurement!)

# Variables for the calculation of visual angle
# These values are used to calculate noise measures (RMS and BCEA) of
# fixations. The may be left as is, but don't use the noise measures then.
# If either or both are empty, the noise measures are provided in pixels
# instead of degrees.
opt['scrSz']        = [52.7, 30]    # screen size in cm
opt['disttoscreen'] = 63.0                  # distance to screen in cm.

# Folders
# Data folder should be structured by one folder for each participant with
# the eye-tracking data in textfiles in each folder.
dir_path = os.path.dirname(os.path.realpath(__file__))
folders  = {}
folders['data']   = os.path.join(dir_path,'trials')   # folder in which data is stored (each folder in folders.data is considered 1 subject)
folders['output'] = os.path.join(dir_path,'output')         # folder for output (will use structure in folders.data for saving output)
folders['video_gaze'] = os.path.join(dir_path,'video_gaze')         # folder for output (will use structure in folders.data for saving output)
folders['stimuli'] = os.path.join(dir_path,'stimuli')         # folder for output (will use structure in folders.data for saving output)

# Options of example script
log_level    = 1    # 0: no output, 1: output from this script only, 2: provide some output on command line regarding I2MC internal progress
do_plot_data = True # if set to True, plot of fixation detection for each trial will be saved as png-file in output folder.
do_plot_video = True # if set to True, plot videos of raw gaze with fixations
do_fix_size = True  # if set to True, blow up the fixation dot for the duration of the fixation
# the figures works best for short trials (up to around 20 seconds)

# =============================================================================
# OPTIONAL VARIABLES
# =============================================================================
# The settings below may be used to adopt the default settings of the
# algorithm. Do this only if you know what you're doing.

# # STEFFEN INTERPOLATION
opt['windowtimeInterp']     = 0.1                           # max duration (s) of missing values for interpolation to occur
opt['edgeSampInterp']       = 2                             # amount of data (number of samples) at edges needed for interpolation
opt['maxdisp']              = opt['xres']*0.2*np.sqrt(2)    # maximum displacement during missing for interpolation to be possible

# # K-MEANS CLUSTERING
opt['windowtime']           = 0.2                           # time window (s) over which to calculate 2-means clustering (choose value so that max. 1 saccade can occur)
opt['steptime']             = 0.02                          # time window shift (s) for each iteration. Use zero for sample by sample processing
opt['maxerrors']            = 100                           # maximum number of errors allowed in k-means clustering procedure before proceeding to next file
opt['downsamples']          = [2, 5, 10]
opt['downsampFilter']       = True                         # use chebychev filter when downsampling? Its what matlab's downsampling functions do, but could cause trouble (ringing) with the hard edges in eye-movement data

# # FIXATION DETERMINATION
opt['cutoffstd']            = 2.0                           # number of standard deviations above mean k-means weights will be used as fixation cutoff
opt['onoffsetThresh']       = 3.0                           # number of MAD away from median fixation duration. Will be used to walk forward at fixation starts and backward at fixation ends to refine their placement and stop algorithm from eating into saccades
opt['maxMergeDist']         = 30.0                          # maximum Euclidean distance in pixels between fixations for merging
opt['maxMergeTime']         = 30.0                          # maximum time in ms between fixations for merging
opt['minFixDur']            = 40.0                          # minimum fixation duration after merging, fixations with shorter duration are removed from output
opt['chebyOrder']           = 8

# Change parameters according to the recommendations on Github
if opt['freq'] == 120:
    opt['downsamples']          = [2, 3, 5]
    opt['chebyOrder']           = 7

if opt['freq'] < 120:
    opt['downsamples']          = [2, 3]
    opt['downsampFilter']       = False


# =============================================================================
# SETUP directory handling
# =============================================================================
# Check if output directory exists, if not create it
if not os.path.isdir(folders['output']):
   os.mkdir(folders['output'])

# Check if output directory exists, if not create it
if not os.path.isdir(folders['video_gaze']):
   os.mkdir(folders['video_gaze'])

# Get all participant folders
fold = list(os.walk(folders['data']))
all_folders = [f[0] for f in fold[1:]]
number_of_folders = len(all_folders)

# Get all files
all_files = [f[2] for f in fold[1:]]
number_of_files = [len(f) for f in all_files]

# Write the final fixation output file
fix_file = os.path.join(folders['output'], 'allfixations.txt')
for it in range(1,101):
    if os.path.isfile(fix_file) and it < 100:
        fix_file = os.path.join(folders['output'], 'allfixations_{}.txt'.format(it))
    else:
        if log_level>0:
            print('Fixations will be stored to: "{}"'.format(fix_file))
        break

# =============================================================================
# START ALGORITHM
# =============================================================================
for folder_idx, folder in enumerate(all_folders):
    if log_level>0:
        print('Processing folder {} of {}'.format(folder_idx + 1, number_of_folders))

    # make output folder
    if do_plot_data:
        outFold = os.path.join(folders['output'], (folder.split(os.sep)[-1]))
        if not os.path.isdir(outFold):
           os.mkdir(outFold)

    # make output folder
    if do_plot_video:
        outVideoFold = os.path.join(folders['video_gaze'], (folder.split(os.sep)[-1]))
        if not os.path.isdir(outVideoFold):
           os.mkdir(outVideoFold)

    if number_of_files[folder_idx] == 0:
        if log_level>0:
            print('  folder is empty, continuing to next folder')
        continue

    for file_idx, file in enumerate(all_files[folder_idx]):
        if log_level>0:
            print('  Processing file {} of {}'.format(file_idx + 1, number_of_files[folder_idx]))

        # Get current file name
        file_name = os.path.join(folder, file)
        ## IMPORT DATA
        if log_level>0:
            print('    Loading data from: {}'.format(file_name))
        data = imp.Titta(file_name, [opt['xres'], opt['yres']])

        # check whether we have data, if not, continue to next file
        if len(data['time']) == 0:
            if log_level>0:
                print('    No data found in file')
            continue

        # RUN FIXATION DETECTION
        if log_level>0:
            print('    Running fixation classification...')
        try:
            fix,_,_ = I2MC.I2MC(data,opt,log_level==2,logging_offset="      ")
        except Exception as e:
            print('    Error in file {}: {}'.format(file_name, e))
            continue

        if not fix:
            if log_level>0:
                print('    Fixation classification did not succeed with file {}'.format(file_name))
            continue

        if fix != False:
            ## PLOT RESULTS
            if do_plot_data:
                # pre-allocate name for saving file
                save_file = os.path.join(outFold, os.path.splitext(file)[0]+'.png')
                f = I2MC.plot.data_and_fixations(data, fix, fix_as_line=True, res=[opt['xres'], opt['yres']])
                # save figure and close
                if log_level>0:
                    print('    Saving image to: ' + save_file)
                f.savefig(save_file)
                plt.close(f)

            # Write data to file
            fix['participant'] = folder.split(os.sep)[-1]
            fix['trial'] = os.path.splitext(file)[0]
            fix_df = pd.DataFrame(fix)
            fix_df.to_csv(fix_file, mode='a', header=not os.path.exists(fix_file),
                          na_rep='nan', sep='\t', index=False, float_format='%.3f')
            if do_plot_video and use_cv2:
                image_file_path = os.path.join(folders['stimuli'], os.path.splitext(file)[0])
                video_file_path = os.path.join(outVideoFold, os.path.splitext(file)[0]+'.mp4')
                create_gaze_video(data, fix, image_file_path, video_file_path, round(opt['xres']), round(opt['yres']), round(opt['freq']))

print('\n\nI2MC took {}s to finish!'.format(time.time()-start))
