# -*- coding: utf-8 -*-
"""
Created on Thu Jun 01 14:11:57 2017

@author: Marcus
"""

from psychopy import visual, core, event
import time
import pandas as pd
import h5py
import os
from pathlib import Path
from titta import helpers_tobii as helpers
from threading import Thread
import numpy as np
import sys

sample_list = ['device_time_stamp', 'system_time_stamp',
       'left_gaze_on_display_area_x',
       'left_gaze_on_display_area_y',
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
       'right_gaze_on_display_area_x',
       'right_gaze_on_display_area_y',
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

class Buffer(Thread):
    """
    Create that simulates a data buffer
    """
    def __init__(self, win):

        self.win = win

        # Mouse object
        self.mouse = event.Mouse(win)
        self.mouse.setPos([0,0])
        self.mouse.setVisible(0)

        self.__stop = True
        self.sample = {}

        # Initiate an empty sample dict
        for l in sample_list:
            self.sample[l] = [0]

        self._start_sample_buffer()

    #%%
    def peek_N(self, stream, N):
        ''' Consume all samples and empty buffer'''
        return self.sample

    #%%
    def consume_N(self, stream, N):
        ''' Get samples in buffer while emptying the buffer '''

        temp = self.sample
        self.sample = {}
        return temp

    #%%
    def _start_sample_buffer(self, sample_buffer_length=sys.maxsize):

        Thread.__init__(self)

        # Initialize the ring buffer
        self.__stop = False
        self.start()


    #%%
    def run(self):
        # Called by the e.g., et.start()
        # Continously read data into a ringbuffer
        while True:
            if self.__stop:
                break

            # Add sample to dict
            self._add_sample_to_buffer()
            time.sleep(0.01)

    #%%
    def _add_sample_to_buffer(self):
        ''' Simulates gaze position with mouse
        '''
        x, y = self.mouse.getPos()

        # Convert mouse position in current psychopy units to Tobii's
        # norm coordinate system (currently supports 'norm' and 'deg')

        if self.win.units == 'norm':
            xy = helpers.norm2tobii(np.array([x, y],ndmin=2))
        elif self.win.units == 'deg':
            xy = helpers.deg2tobii(np.array([x, y],ndmin=2), self.win.monitor)
        elif self.win.units == 'pix':
            xy = helpers.pix2tobii(np.array([x, y],ndmin=2), self.win.monitor)
        else:
            raise IOError ('Invalid unit of PsychoPy screen: Titta in dummy mode currently \
                           supports "norm", "pix", and "deg".')
        for key in self.sample.keys():
            if '_x' in key:
                self.sample[key].append(xy[0, 0])
            elif '_y':
                self.sample[key].append(xy[0, 1])
            else:
                self.sample[key].append(np.random.rand())

    #%%
    def _stop_sample_buffer(self):
        self.__stop = True
##########################
##########################
##########################
##########################

# %%
class Connect(object):
    """
    Create a class that simplifies life for people wanting to use the SDK
    """
    def __init__(self):

        # clock
        self.clock = core.Clock()

        # Dict to store samples

    def init(self):
        ''' Connect to eye tracker
        and apply settings
        '''
        print('init')


    #%% Init calibration
    def calibrate(self, win, eye='both', calibration_number='first'):
        ''' Master function for setup and calibration
        '''
        self.buffer = Buffer(win)

        # Window and instruction text for calibration
        instruction_text = visual.TextStim(win,text='',wrapWidth = 1,
                                           height = 0.05, units='norm')

        self.instruction_text = instruction_text

        self.win = win

        self.instruction_text.text = 'Calibration Dummy mode'
        self.instruction_text.draw()
        self.win.flip()
        core.wait(2)

    #%%
    def get_system_time_stamp(self):
        ''' Get system time stamp
        '''

        print('time_stamp')

    #%%
    def start_recording(self,   gaze=False,
                                time_sync=False,
                                eye_image=False,
                                notifications=False,
                                external_signal=False,
                                positioning=False):
        print('start_recording')



    #%%
    def send_message(self, msg, ts=None):
        print(msg)


    #%%
    def stop_recording(self,    gaze=False,
                                time_sync=False,
                                eye_image=False,
                                notifications=False,
                                external_signal=False,
                                positioning=False):
        print('stop_recording')

    #%%
    def set_dummy_mode(self):
        print('dummy mode')

    #%%
    def calibration_history(self):
        print('calibration_history')
        return None
    #%%
    def system_info(self):
        ''' Returns information about system in dict
        '''

        info = {}
        info['serial_number']  = 'dummy'
        info['address']  = 'dummy'
        info['model']  = 'dummy'
        info['name']  = 'dummy'
        info['firmware_version'] = 'dummy'
        info['runtime_version'] = 'dummy'
        info['tracking_mode']  = 'dummy'
        info['sampling_frequency']  = 'dummy'
        info['track_box']  = 'dummy'
        info['display_area']  = 'dummy'
        info['python_version'] = '.'.join([str(sys.version_info[0]),
                                           str(sys.version_info[1]),
                                           str(sys.version_info[2])])
        info['psychopy_version'] = 'dummy'
        info['TittaPy_version'] = 'dummy'
        info['titta_version'] = 'dummy'

    #%%
    def set_sample_rate(self, Fs):
        '''Sets the sample rate
        '''
        print('set sample rate')
    #%%
    def get_sample_rate(self):
        '''Gets the sample rate
        '''
        print('get sample rate')
        return 0

    #%%
    def save_data(self, *argv, filename=None, append_version=True):
        ''' Saves the data to HDF5 container
        If you want to read the data, see the 'resources' folder
        '''

        print('save data')




