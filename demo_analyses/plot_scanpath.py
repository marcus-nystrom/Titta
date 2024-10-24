# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:06:43 2022

@author: Marcus
@contributer: Bob
"""

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import os
import time

try:
    import cv2
except ImportError:
    print("Could not import OpenCV for image processing, using PsychoPy instead")
    from psychopy import visual, core
    use_cv2 = False
else:
    use_cv2 = True

start = time.time()

# %%

def make_scanpath(image_name, fixations, imres, scale_with_duration=True):
    '''


    Args:
        image (str): name to image (full path)
        fixations (dataframe): with fixations for the images with columns 'xpos' (pixels), 'ypos' (pixels), 'dur' (ms)
        imres (tuple) resoluiton of image in pixels
        scale_with_duration (bool, optional): Scale fixations with durations (otherwise all fixations will have the same size)

    Returns:
        None.

    '''

    win = visual.Window(fullscr=True, screen=1, units='pix', size=imres)

    dot = visual.Circle(win, radius=50, lineColor='red', fillColor='red',
                        opacity=0.5)
    line = visual.Line(win, start=(-0.5, -0.5), end=(0.5, 0.5),
                        lineWidth=3, lineColor='red', opacity=0.5)

    im = visual.ImageStim(win, image=str(image_name), size=(imres[0], imres[1]))
    im.draw()

    start_pos_old = (None, None)
    for i, row in fixations.iterrows():
        dot.pos = (row.xpos - imres[0]/2, imres[1]/2 - row.ypos)



        if i == 0:
            dot.fillColor = 'green'
            dot.lineColor = 'green'
        elif i == len(fixations)-1:
            dot.fillColor = 'red'
            dot.lineColor = 'red'
            line.lineColor = 'red'

        else:
            dot.fillColor = 'blue'
            dot.lineColor = 'blue'
            line.lineColor = 'blue'


        line.end = dot.pos

        if i > 0:
            if i < 2:
                line.lineColor = 'green'

            line.start = start_pos_old
            line.draw()

        dot.opacity=0.5


        if scale_with_duration:
            dot.radius = row.dur/10

        dot.draw()
            # print(row.xpos, row.ypos, dot.radius)

        start_pos_old = line.end


    win.flip()
    core.wait(1)

    win.getMovieFrame()

    # Make a new dir to save plots if it does not already exists
    path = Path.cwd() / 'scanpaths' / str(fixations.participant[0])
    Path(path).mkdir(parents=True, exist_ok=True)

    # Save the results
    fname =  path / ('scanpath_' + str(image_name).split(os.sep)[-1])
    win.saveMovieFrames(fname)
    win.close()

# %%

# %%

def add_transparency_cv2(overlay, image, alpha):
    ## image used in func must be a copy of image! The image from image can be original, original is fastest
    if alpha == 1:
        image_new = overlay
    else:
        image_new = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    return image_new

# %%

def make_scanpath_cv2(image_name, fixations, imres, scale_with_duration=True):
    '''


    Args:
        image (str): name to image (full path)
        fixations (dataframe): with fixations for the images with columns 'xpos' (pixels), 'ypos' (pixels), 'dur' (ms)
        imres (tuple) resoluiton of image in pixels
        scale_with_duration (bool, optional): Scale fixations with durations (otherwise all fixations will have the same size)

    Returns:
        None.

    '''
    alpha = 0.5
    dot_radius = 50
    thickness = 2

    im_rgb = cv2.imread(str(image_name))
    image = im_rgb.copy()
    start_pos_old = (None, None)
    for i, row in fixations.iterrows():

        dot_pos = (round(row.xpos), round(row.ypos))

        if i == 0:
            dotColor = (0, 255, 0)
        elif i == len(fixations)-1:
            dotColor = (0, 0, 255)
            lineColor = (0, 0, 255)
        else:
            dotColor = (255, 0, 0)
            lineColor = (255, 0, 0)

        line_end = dot_pos

        if i > 0:
            if i < 2:
                lineColor = (0, 0, 255)

            line_start = start_pos_old
            image = add_transparency_cv2(cv2.line(image.copy(), line_start, line_end, lineColor, thickness), image, alpha)

        if scale_with_duration:
            dot_radius = round(row.dur/10)

        image = add_transparency_cv2(cv2.circle(image.copy(), (dot_pos[0], dot_pos[1]), dot_radius, dotColor, -1), image, alpha)

        start_pos_old = line_end

    # Make a new dir to save plots if it does not already exists
    path = Path.cwd() / 'scanpaths' / str(fixations.participant[0])
    Path(path).mkdir(parents=True, exist_ok=True)

    # Save the results
    fname =  path / ('scanpath_' + str(image_name).split(os.sep)[-1])
    cv2.imwrite(str(fname), image)

# %%

imres = (1920, 1080)

# Read files with fixations generated with the I2MC
df_fixations = pd.read_csv(Path.cwd() / 'output' / 'allfixations.txt', sep='\t')

# Read the images into a psychopy object
image_names = list((Path.cwd() / 'stimuli').rglob('*.jpeg'))

img = []
participants = df_fixations.participant.unique()

for participant in list(participants):
    for image_name in image_names:
        df_temp = df_fixations[(df_fixations.trial == str(image_name).split(os.sep)[-1]) & \
                               (df_fixations.participant == participant)].reset_index()

        if len(df_temp) == 0:
            print(f"Warning: no data exist for {participant} and {str(image_name).split(os.sep)[-1]}")
            continue

        if use_cv2:
            make_scanpath_cv2(image_name, df_temp, imres)
        else:
            make_scanpath(image_name, df_temp, imres)


print('\n\nPlotting scanpaths took {}s to finish!'.format(time.time()-start))
