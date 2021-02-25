# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 10:57:23 2019

@author: Jonathan
"""

# =============================================================================
# =============================================================================
# #  FIXATION DETECTION USING THE IDENTIFICATION BY 2-MEANS CLUSTERING (I2MC) ALGORITHM
#
# Translated to python from Matlab by Jonathan van Leeuwen, 2019 - www.github.com/jonathanvanleeuwen/I2MC
#
# =============================================================================
# =============================================================================
# Description:
# The I2MC algorithm was designed to accomplish fixation detection in data
# across a wide range of noise levels and when periods of data loss may
# occur.
# 
# Cite as:
# Hessels, R.S., Niehorster, D.C., Kemner, C., & Hooge, I.T.C. (2016).
# Noise-robust fixation detection in eye-movement data - Identification by 
# 2-means clustering (I2MC). Behavior Research Methods.
# 
# For more information, questions, or to check whether we have updated to a
# better version, e-mail: royhessels@gmail.com / dcnieho@gmail.com. I2MC is
# available from www.github.com/royhessels/I2MC
# 
# Most parts of the I2MC algorithm are licensed under the Creative Commons
# Attribution 4.0 (CC BY 4.0) license. Some functions are under MIT 
# license, and some may be under other licenses.
# 
# Quick start guide for adopting this script for your own data:
# 1) Build an import function specific for your data (see importTobiiTX300
# for an example). 
# 
# 2) Change line 175 to use your new import function. The format should be:
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
# Tested on Python 3.5

# =============================================================================
# TODO
# =============================================================================
# List not inclusive 

# Make sure that looping through files works accuratly
# Make sure the plot code works


# Functions to make List not inclusive 
    #- FolderFromFolder
    #- FileFromFolder

# =============================================================================
# Initialize
# =============================================================================
import os
import sys
import numpy as np
dir_path = os.path.dirname(os.path.realpath(__file__))
funcPath = dir_path+os.sep+'functions'
sys.path.append(funcPath)
import import_funcs as imp
import I2MC_funcs
import plot_funcs as plot
import matplotlib.pyplot as plt
import time 
start = time.time()

# =============================================================================
# NECESSARY VARIABLES
# =============================================================================
opt = {}
# General variables for eye-tracking data
opt['xres'] = 1920.0 # maximum value of horizontal resolution in pixels
opt['yres'] = 1080.0 # maximum value of vertical resolution in pixels
opt['missingx'] = -opt['xres'] # missing value for horizontal position in eye-tracking data (example data uses -xres). used throughout functions as signal for data loss
opt['missingy'] = -opt['yres'] # missing value for vertical position in eye-tracking data (example data uses -yres). used throughout functions as signal for data loss
opt['freq'] = 600.0 # sampling frequency of data (check that this value matches with values actually obtained from measurement!)

# Variables for the calculation of visual angle
# These values are used to calculate noise measures (RMS and BCEA) of
# fixations. The may be left as is, but don't use the noise measures then.
# If either or both are empty, the noise measures are provided in pixels
# instead of degrees.
opt['scrSz'] = [50.9174, 28.6411] # screen size in cm
opt['disttoscreen'] = 65.0 # distance to screen in cm.

# Folders
# Data folder should be structured by one folder for each participant with
# the eye-tracking data in textfiles in each folder.
folders = {}
folders['data'] = 'example data' # folder in which data is stored (each folder in folders.data is considered 1 subject)
folders['output'] = 'output' # folder for output (will use structure in folders.data for saving output)

# Plot results
opt['plotData'] = True; # if set to True, plot of fixation detection for each trial will be saved as png-file in output folder.
# the figures works best for short trials (up to around 20 seconds)

# =============================================================================
# OPTIONAL VARIABLES
# =============================================================================
# The settings below may be used to adopt the default settings of the
# algorithm. Do this only if you know what you're doing.

# # STEFFEN INTERPOLATION
opt['windowtimeInterp'] = 0.1 # max duration (s) of missing values for interpolation to occur
opt['edgeSampInterp'] = 2 # amount of data (number of samples) at edges needed for interpolation
opt['maxdisp'] = opt['xres']*0.2*np.sqrt(2) # maximum displacement during missing for interpolation to be possible

# # K-MEANS CLUSTERING
opt['windowtime'] = 0.2 # time window (s) over which to calculate 2-means clustering (choose value so that max. 1 saccade can occur)
opt['steptime'] = 0.02 # time window shift (s) for each iteration. Use zero for sample by sample processing
opt['maxerrors'] = 100.0 # maximum number of errors allowed in k-means clustering procedure before proceeding to next file
opt['downsamples'] = [2.0, 5.0, 10.0]
opt['downsampFilter'] = 0 # use chebychev filter when downsampling? 1: yes, 0: no. requires signal processing toolbox. is what matlab's downsampling functions do, but could cause trouble (ringing) with the hard edges in eye-movement data

# # FIXATION DETERMINATION
opt['cutoffstd'] = 2.0 # number of standard deviations above mean k-means weights will be used as fixation cutoff
opt['onoffsetThresh'] = 3.0 # number of MAD away from median fixation duration. Will be used to walk forward at fixation starts and backward at fixation ends to refine their placement and stop algorithm from eating into saccades
opt['maxMergeDist'] = 30.0 # maximum Euclidean distance in pixels between fixations for merging
opt['maxMergeTime'] = 30.0 # maximum time in ms between fixations for merging
opt['minFixDur'] = 40.0 # minimum fixation duration after merging, fixations with shorter duration are removed from output

# Save file
sep = '\t' # The value separator

# =============================================================================
# SETUP directory handeling
# =============================================================================
# Check if output directory exists, if not create it
if not os.path.isdir(folders['output']):
   os.mkdir(folders['output'])
   
# Get all participant folders
fold = list(os.walk(folders['data']))
allFolders = [f[0] for f in fold[1:]]
nfold = len(allFolders)

# Get all files
allFiles = [f[2] for f in fold[1:]]
nfiles = [len(f) for f in allFiles]

# Write the final fixation output file 
fixFile = folders['output']+os.sep+'allfixations.txt'
fixFileHeader = 'FixStart{sep}FixEnd{sep}FixDur{sep}XPos{sep}YPos{sep}FlankedByDataLoss{sep}Fraction Interpolated{sep}WeightCutoff{sep}RMSxy{sep}BCEA{sep}FixRangeX{sep}FixRangeY{sep}Participant{sep}Trial\n'.format(sep=sep)
for it in range(1,101):
    if os.path.isfile(fixFile) and it < 100:
        fixFile = folders['output']+os.sep+'allfixations_{}.txt'.format(it)
    else:
        print('Writing fixations to: "{}"'.format(fixFile))
        with open(fixFile, 'w+') as f:
            f.write(fixFileHeader)
        break
    
# =============================================================================
# START ALGORITHM -- FIX THIS LATER
# =============================================================================
for foldIdx, folder in enumerate(allFolders):
    # make output folder
    outFold = folders['output']+os.sep+(folder.split(os.sep)[-1])
    if not os.path.isdir(outFold):
       os.mkdir(outFold)

    if nfiles[foldIdx] == 0:
        print('folder is empty, continuing to next folder')
        continue
    
    for fileIdx, file in enumerate(allFiles[foldIdx]):
        # Get current file name
        fName = folder+os.sep+file
        ## IMPORT DATA
        print('\n\n\nImporting and processing: "{}"'.format(fName))
        data = {}
        data['time'], data['L_X'], data['L_Y'], data['R_X'], data['R_Y'] = imp.importSpectrum(fName, 1, [opt['xres'], opt['yres']], opt['missingx'], opt['missingy'])
        
        # check whether we have data, if not, continue to next file
        if len(data['time']) == 0: 
            print('Empty file encountered, continuing to next file ')
            continue
        
        # RUN FIXATION DETECTION
        fix,_,_ = I2MC_funcs.I2MC(data,opt)
        
        if fix != False:
            ## PLOT RESULTS
            if opt['plotData']:
                # pre-allocate name for saving file
                saveFile = outFold + os.sep+  os.path.splitext(file)[0]+'.png'
                f = I2MC_funcs.plotResults(data,fix,[opt['xres'], opt['yres']])
                # save figure and close
                print('Saving image to: '+saveFile)
                f.savefig(saveFile)
                plt.close(f)
                
            # Write data to string 
            fixInfo = ''
            for t in range(len(fix['start'])):            
                fixInfo += '{:0.3f}{sep}{:0.3f}{sep}{:0.3f}{sep}{:0.3f}{sep}{:0.3f}{sep}'\
                '{:0.3f}{sep}{:0.3f}{sep}{:0.3f}{sep}{:0.3f}{sep}{:0.3f}{sep}{:0.3f}{sep}'\
                '{:0.3f}{sep}{}{sep}{}\n'.format(\
                fix['startT'][t], fix['endT'][t], fix['dur'][t], fix['xpos'][t],\
                fix['ypos'][t], fix['flankdataloss'][t], fix['fracinterped'][t],\
                fix['cutoff'], fix['RMSxy'][t], fix['BCEA'][t],\
                fix['fixRangeX'][t], fix['fixRangeY'][t],\
                folder.split(os.sep)[-1], os.path.splitext(file)[0], sep=sep)
                
            # Write string to file
            with open(fixFile, 'a+') as f:
                f.write(fixInfo)

print('\n\nI2MC took {}s to finish!'.format(time.time()-start))