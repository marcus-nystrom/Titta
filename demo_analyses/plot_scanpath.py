# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:06:43 2022

@author: Marcus
"""

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import os
from psychopy import visual, core


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


# %%

imres = (1920, 1080)

# Read files with fixations generated with the I2MC
df_fixations = pd.read_csv(Path.cwd() / 'output' / 'allfixations.txt', sep='\t')

# Read the images into a psychopy object
image_names = list((Path.cwd() / 'stimuli').rglob('*.jpeg'))

win = visual.Window(fullscr=True, screen=1, units='pix', size=imres)

img = []
participants = df_fixations.participant.unique()

for participant in list(participants):
    for image_name in image_names:
        df_temp = df_fixations[(df_fixations.trial == str(image_name).split(os.sep)[-1]) & \
                               (df_fixations.participant == participant)].reset_index()

        if len(df_temp) == 0:
            print(f"Warning: no data exist for {participant} and {str(image_name).split(os.sep)[-1]}")
            continue

        make_scanpath(image_name, df_temp, imres)


win.close()
