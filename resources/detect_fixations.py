# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 19:25:01 2021

@author: Marcus
Run this to start fixation detection. Read the comments and error messages
carefully.

You need to run 'extract_trial_data.py' before running this file

"""
import shutil
# from distutils.dir_util import copy_tree
from pathlib import Path

I2MC_main_path = Path.cwd() / 'I2MC' / 'I2MC_Python-master' / 'example'

I2MC_main = I2MC_main_path / 'I2MC_example.py'
if not I2MC_main.is_file():
    print('It appears that I2MC is not available. please follow the\
 instructions in /resources/I2MC/get_I2MC.txt to download it.')
    raise FileNotFoundError

# First remove example data found when downloading I2MC
example_data_path = I2MC_main_path / 'example_data'
if example_data_path.is_dir():
    shutil.rmtree(example_data_path)
    print('Removed old data')


# Move trial data you extracted to the right folder I2MC
shutil.copytree(str(Path.cwd() / 'trials'), str(example_data_path))
print('Copied data to ' + str(example_data_path))
# %% Run I2MC
# Now open and run / 'I2MC' / 'I2MC_Python-master' / 'example / I2MC_example.py'.
# OBS: you first need to adjust the settings to match your
# Experimental setup in 'I2MC_example.py'. Check under '# NECESSARY VARIABLES'
# Also make sure Titta is use when importing data (line 190)
# data = imp.Titta(file_name, [opt['xres'], opt['yres']])





