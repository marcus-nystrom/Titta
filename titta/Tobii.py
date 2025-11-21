# -*- coding: utf-8 -*-
"""
Created on Thu Jun 01 14:11:57 2017

@author: Marcus

    """
import pandas as pd
import copy
import sys
import warnings
import json
import pickle
from pathlib import Path
import os
import numpy as np
import h5py
import time
import importlib
import TittaPy_v2 as TittaPy
import titta
from titta import helpers_tobii as helpers

# Suppress FutureWarning
warnings.simplefilter(action='ignore', category=FutureWarning)

# test if psychopy available
HAS_PSYCHOPY = False
try:
    import psychopy
    from psychopy import visual, core, event
except:
    pass
else:
    HAS_PSYCHOPY = True


#%%
class myTobii(object):
    """
    A Class to communicate with Tobii eye trackers
    """

    def __init__(self, settings):
        '''
        Constructs an instance of the Titta interface, with specified settings
        acquited through the call (Titta.get_defaults)
        '''

        self.settings = settings

        # Remove empty spaces (if any are given)
        self.settings.TRACKER_ADDRESS = self.settings.TRACKER_ADDRESS.replace(" ", "")

        # ensure right SDK version is loaded
        global TittaPy
        SDKVersion = int(TittaPy.__name__[-1])
        if self.settings.TittaPySDKVersion != SDKVersion:
            # set global TittaPy to correct version
            TittaPy = importlib.import_module('TittaPy_v'+str(self.settings.TittaPySDKVersion))


    #%%
    def init(self):
        ''' Apply settings and check capabilities
        '''

        # Assert that path given to store data exists
        if self.settings.DATA_STORAGE_PATH.strip():
            assert Path(self.settings.DATA_STORAGE_PATH).is_dir(), "Data path for storage given in Titta.py does not exit"

        # Start the eye tracker logger
        TittaPy.start_logging()

        # Update the number of calibration point (if changed by the user)
        if self.settings.N_CAL_TARGETS == 13:
            self.settings.CAL_POS_TOBII = self.settings.CAL_TARGETS[:]
        elif self.settings.N_CAL_TARGETS == 9:
            self.settings.CAL_POS_TOBII = self.settings.CAL_TARGETS[[0, 1, 2, 5, 6, 7, 10, 11, 12]]
        elif self.settings.N_CAL_TARGETS == 5:
            self.settings.CAL_POS_TOBII = self.settings.CAL_TARGETS[[0, 2, 6, 10, 12]]
        elif self.settings.N_CAL_TARGETS == 3:
            self.settings.CAL_POS_TOBII = self.settings.CAL_TARGETS[[0, 6, 12]]
        elif self.settings.N_CAL_TARGETS == 1:
            self.settings.CAL_POS_TOBII = self.settings.CAL_TARGETS[[6]]
        elif self.settings.N_CAL_TARGETS == 0:
            self.settings.CAL_POS_TOBII = np.array([])
        else:
            raise ValueError('Unvalid number of calibration points')

        # If no tracker address is given, find one automatically
        if len(self.settings.TRACKER_ADDRESS) == 0:

            # Sometimes you have to try a few times before it finds and eye tracker
            tracker_found = False
            k = 0
            while not tracker_found and k < 3:

                # if the tracker doesn't connect, try four times to reconnect
                ets = TittaPy.find_all_eye_trackers()
                for et in ets:

                    # Check if the desired eye tracker is found
                    if et['model'] == self.settings.eye_tracker_name:
                        self.settings.TRACKER_ADDRESS = et['address']
                        tracker_found = True
                        break

                time.sleep(1)
                k += 1

            if not tracker_found:
                raise Exception('The desired eye tracker not found. \
                                These are available: ' + ' '.join([str(m['model']) for m in ets]))

        if self.settings.PACING_INTERVAL < 0.8:
            raise Exception('Calibration pacing interval must be \
                            larger or equal to 0.8 s')

        # Initiate the EyeTracker class with a specific address
        self.buffer = TittaPy.EyeTracker(self.settings.TRACKER_ADDRESS)

        # Always include eye openness data in gaze stream
        if TittaPy.capability.has_eye_openness_data in self.buffer.capabilities:

            # Workaround since Tobii Pro Fusion reports to support eye openness
            # signals at 250 Hz when it if fact does not
            if not (self.settings.eye_tracker_name == 'Tobii Pro Fusion' and self.settings.SAMPLING_RATE == 250):
                self.buffer.set_include_eye_openness_in_gaze(True)

        # Store timestamped messages in a list
        self.msg_container = []

        self.user_position_guide_data = None
        self.all_validation_results = []

        self.clock = core.Clock()

        # Only the tobii pro spectrum and the tobii pro fusion can record eye images
        # Never record eye images for other models, override defaults
        if not self.buffer.has_stream('eye_image'):
            if self.settings.RECORD_EYE_IMAGES_DURING_CALIBRATION:
                print('Warning: This eye tracker does not support eye images')
                self.settings.RECORD_EYE_IMAGES_DURING_CALIBRATION = False

        # Check and set sampling frequency if not correct
        Fs = self.get_sample_rate()
        if Fs != self.settings.SAMPLING_RATE:
            self.set_sample_rate(self.settings.SAMPLING_RATE)

        # Assert that the selected tracking mode is supported (human, primate)
        assert np.any([tracking_mode == self.settings.TRACKING_MODE \
                        for tracking_mode in self.buffer.supported_modes]), \
            "The given tracking mode is not supported. \
            Supported modes are: {}".format(self.buffer.supported_modes)

        try:
            print('Current tracking mode: {}'.format(self.buffer.tracking_mode))
            self.buffer.tracking_mode = self.settings.TRACKING_MODE
        except NameError:
            print('Tracking mode not found: {}'.format(self.settings.TRACKING_MODE))

        # Modify location and number of eye images for fusion
        if self.settings.eye_tracker_name == 'Tobii Pro Fusion':
            # Parameters for eye images (default values are for Spectrum)
            self.settings.graphics.EYE_IMAGE_SIZE = (0.25, 0.25)
            self.settings.graphics.EYE_IMAGE_POS_R = (0.55, -0.4)
            self.settings.graphics.EYE_IMAGE_POS_L = (-0.25, -0.4)
            self.settings.graphics.EYE_IMAGE_POS_R_1 = (0.25, -0.4) # Used for the two additional fusion images
            self.settings.graphics.EYE_IMAGE_POS_L_1 = (-0.55, -0.4)

           #%%
    def _create_calibration_buttons(self):
        '''Creates click buttons that are used during calibration
        If another window object, win_operator, is given, the experiment
        will be run in dual screen mode.

        '''

        # Find out ratio aspect of the stimulus screen
        screen_res = self.win.size
        ratio = screen_res[0] / float(screen_res[1])

        # Shown during setup to check gaze in corners
        self.POS_CAL_CHECK_DOTS = [[-0.45 * ratio, -0.45], [0.45 * ratio, -0.45],
                              [-0.45 * ratio, 0.45], [0.45 * ratio, 0.45]]

        # Text object to draw text (on buttons)
        instruction_text = visual.TextStim(self.win,text='',wrapWidth = 1,
                                           height = self.settings.graphics.TEXT_SIZE,
                                           color = self.settings.graphics.TEXT_COLOR,
                                           units='norm')
        self.instruction_text = instruction_text
        instruction_text_op = visual.TextStim(self.win_temp,text='',wrapWidth = 1,
                                              height = self.settings.graphics.TEXT_SIZE,
                                              color = self.settings.graphics.TEXT_COLOR,
                                              units='norm')
        self.instruction_text_op = instruction_text_op


        # Setup stimuli for drawing calibration / validation targets
        if self.settings.CAL_TARGET is None:
            self.cal_dot = helpers.MyDot2(units='pix',
                                          outer_diameter=self.settings.graphics.TARGET_SIZE,
                                          inner_diameter=self.settings.graphics.TARGET_SIZE_INNER)
        else:
            if not isinstance(self.settings.CAL_TARGET, helpers.TargetBase):
                raise ValueError('Provided target should be an instance of a class derived from helpers_tobii.TargetBase')
            self.cal_dot = self.settings.CAL_TARGET
        self.cal_dot.create_for_win(self.win)


        # Click buttons
        self.calibrate_button = visual.Rect(self.win_temp, width= self.settings.graphics.WIDTH_CAL_BUTTON,
                                            height=self.settings.graphics.HEIGHT_CAL_BUTTON,
                                        units='norm', fillColor=self.settings.graphics.COLOR_CAL_BUTTON,
                                        pos=self.settings.graphics.POS_CAL_BUTTON)
        self.calibrate_button_text = visual.TextStim(self.win_temp, text=self.settings.graphics.CAL_BUTTON_TEXT,
                                                     height=self.settings.graphics.TEXT_SIZE,
                                                     color = self.settings.graphics.TEXT_COLOR,
                                                     units='norm',
                                                     pos=self.settings.graphics.POS_CAL_BUTTON)

        self.recalibrate_button = visual.Rect(self.win_temp, width= self.settings.graphics.WIDTH_RECAL_BUTTON,
                                            height=self.settings.graphics.HEIGHT_RECAL_BUTTON,
                                        units='norm', fillColor=self.settings.graphics.COLOR_RECAL_BUTTON,
                                        pos=self.settings.graphics.POS_RECAL_BUTTON)
        self.recalibrate_button_text = visual.TextStim(self.win_temp, text=self.settings.graphics.RECAL_BUTTON_TEXT,
                                                     height=self.settings.graphics.TEXT_SIZE,
                                                     color = self.settings.graphics.TEXT_COLOR,
                                                     units='norm',
                                                     pos=self.settings.graphics.POS_RECAL_BUTTON)

        self.revalidate_button = visual.Rect(self.win_temp, width= self.settings.graphics.WIDTH_REVAL_BUTTON,
                                            height=self.settings.graphics.HEIGHT_REVAL_BUTTON,
                                        units='norm', fillColor=self.settings.graphics.COLOR_REVAL_BUTTON,
                                        pos=self.settings.graphics.POS_REVAL_BUTTON)
        self.revalidate_button_text = visual.TextStim(self.win_temp, text=self.settings.graphics.REVAL_BUTTON_TEXT,
                                                     height=self.settings.graphics.TEXT_SIZE,
                                                     color = self.settings.graphics.TEXT_COLOR,
                                                     units='norm',
                                                     pos=self.settings.graphics.POS_REVAL_BUTTON)

        self.setup_button = visual.Rect(self.win_temp, width= self.settings.graphics.WIDTH_SETUP_BUTTON,
                                        height=self.settings.graphics.HEIGHT_SETUP_BUTTON,
                                        units='norm', fillColor=self.settings.graphics.COLOR_SETUP_BUTTON,
                                        pos=self.settings.graphics.POS_SETUP_BUTTON)
        self.setup_button_text = visual.TextStim(self.win_temp, text=self.settings.graphics.SETUP_BUTTON_TEXT,
                                                 height=self.settings.graphics.TEXT_SIZE, units='norm',
                                                 color = self.settings.graphics.TEXT_COLOR,
                                                 pos=self.settings.graphics.POS_SETUP_BUTTON)

        self.accept_button = visual.Rect(self.win_temp, width= self.settings.graphics.WIDTH_ACCEPT_BUTTON,
                                        height=self.settings.graphics.HEIGHT_ACCEPT_BUTTON,
                                        units='norm', fillColor=self.settings.graphics.COLOR_ACCEPT_BUTTON,
                                        pos=self.settings.graphics.POS_ACCEPT_BUTTON)
        self.accept_button_text = visual.TextStim(self.win_temp, text=self.settings.graphics.ACCEPT_BUTTON_TEXT,
                                                  height=self.settings.graphics.TEXT_SIZE,
                                                  color = self.settings.graphics.TEXT_COLOR,
                                                  units='norm',
                                                  pos=self.settings.graphics.POS_ACCEPT_BUTTON)

        self.back_button = visual.Rect(self.win_temp, width= self.settings.graphics.WIDTH_BACK_BUTTON,
                                        height=self.settings.graphics.HEIGHT_BACK_BUTTON,
                                        units='norm', fillColor=self.settings.graphics.COLOR_BACK_BUTTON,
                                        pos=self.settings.graphics.POS_BACK_BUTTON)
        self.back_button_text = visual.TextStim(self.win_temp, text=self.settings.graphics.BACK_BUTTON_TEXT,
                                                height=self.settings.graphics.TEXT_SIZE,
                                                color = self.settings.graphics.TEXT_COLOR,
                                                units='norm',
                                                pos=self.settings.graphics.POS_BACK_BUTTON)

        self.gaze_button = visual.Rect(self.win_temp, width= self.settings.graphics.WIDTH_GAZE_BUTTON,
                                        height=self.settings.graphics.HEIGHT_GAZE_BUTTON,
                                        units='norm', fillColor=self.settings.graphics.COLOR_GAZE_BUTTON,
                                        pos=self.settings.graphics.POS_GAZE_BUTTON)
        self.gaze_button_text = visual.TextStim(self.win_temp, text=self.settings.graphics.GAZE_BUTTON_TEXT,
                                                height=self.settings.graphics.TEXT_SIZE, units='norm',
                                                color = self.settings.graphics.TEXT_COLOR,
                                                pos=self.settings.graphics.POS_GAZE_BUTTON)

        self.calibration_image = visual.Rect(self.win_temp, width= self.settings.graphics.WIDTH_CAL_IMAGE_BUTTON,
                                        height=self.settings.graphics.HEIGHT_CAL_IMAGE_BUTTON,
                                        units='norm', fillColor=self.settings.graphics.COLOR_CAL_IMAGE_BUTTON,
                                        pos=self.settings.graphics.POS_CAL_IMAGE_BUTTON)

        self.calibration_image_text = visual.TextStim(self.win_temp, text=self.settings.graphics.CAL_IMAGE_BUTTON_TEXT,
                                                height=self.settings.graphics.TEXT_SIZE, units='norm',
                                                color = self.settings.graphics.TEXT_COLOR,
                                                pos=self.settings.graphics.POS_CAL_IMAGE_BUTTON)

        # Dots for the setup screen
        self.setup_dot = helpers.MyDot2(units='height',
                                     outer_diameter=self.settings.graphics.SETUP_DOT_OUTER_DIAMETER,
                                     inner_diameter=self.settings.graphics.SETUP_DOT_INNER_DIAMETER, win=self.win)


        # Dot for showing et data
        self.et_sample_l = visual.Circle(self.win_temp, radius = self.settings.graphics.ET_SAMPLE_RADIUS,
                                         fillColor = 'red', units='pix')
        self.et_sample_r = visual.Circle(self.win_temp, radius = self.settings.graphics.ET_SAMPLE_RADIUS,
                                         fillColor = 'blue', units='pix')

        if self.win_operator:
            self.raw_et_sample_l = visual.Circle(self.win_temp, radius = 0.01,
                                             fillColor = 'red', units='norm')
            self.raw_et_sample_r = visual.Circle(self.win_temp, radius = 0.01,
                                             fillColor = 'blue', units='norm')
            self.current_point = helpers.MyDot2(outer_diameter=0.05, inner_diameter=0.02, 
                                             units='norm', win=self.win_temp)

        # Show images (eye image, validation resutls)
        self.eye_image_stim_l = visual.ImageStim(self.win_temp, units='norm',
                                                   size=self.settings.graphics.EYE_IMAGE_SIZE,
                                                   pos=self.settings.graphics.EYE_IMAGE_POS_L,
                                                   image=np.zeros((512, 512)))
        self.eye_image_stim_r = visual.ImageStim(self.win_temp, units='norm',
                                                   size=self.settings.graphics.EYE_IMAGE_SIZE,
                                                   pos=self.settings.graphics.EYE_IMAGE_POS_R,
                                                   image=np.zeros((512, 512)))
        self.eye_image_stim_l_1 = visual.ImageStim(self.win_temp, units='norm',
                                                   size=self.settings.graphics.EYE_IMAGE_SIZE,
                                                   pos=self.settings.graphics.EYE_IMAGE_POS_L_1,
                                                   image=np.zeros((512, 512)))
        self.eye_image_stim_r_1 = visual.ImageStim(self.win_temp, units='norm',
                                                   size=self.settings.graphics.EYE_IMAGE_SIZE,
                                                   pos=self.settings.graphics.EYE_IMAGE_POS_R_1,
                                                   image=np.zeros((512, 512)))

        # Accuracy image
        self.accuracy_image = visual.ImageStim(self.win_temp, image=None,units='norm', size=(2,2),
                                          pos=(0, 0))

    #%%
    def start_recording(self,   gaze=False,
                                time_sync=False,
                                eye_image=False,
                                notifications=False,
                                external_signal=False,
                                positioning=False,
                                block_until_data_available=False):
        ''' Starts recording streams
        See bug re. positioning stream (ordering of starting and stopping streams)
        https://github.com/dcnieho/Titta/blob/master/tests/positioningStreamBug.m
        '''

        if gaze and self.buffer.has_stream('gaze'):
            self.buffer.start('gaze')
        if time_sync and self.buffer.has_stream('time_sync'):
            self.buffer.start('time_sync')
        if eye_image and self.buffer.has_stream('eye_image'):
            self.buffer.start('eye_image')
        if notifications and self.buffer.has_stream('notification'):
            self.buffer.start('notification')
        if external_signal and self.buffer.has_stream('external_signal'):
            self.buffer.start('external_signal')
        if positioning and self.buffer.has_stream('positioning'):
            self.buffer.start('positioning')

        '''
        # Block until new data are available. This happens either when
        the most recent timestamp go from en empty list to a value, e.g.,
            1) [], [], [], [],... ->   1230333548588

            or to a new value, e.g.,

            # 1230333548588, 1230333548588, 1230333548588...-> 1230333715267
        '''
        if block_until_data_available:
            t0 = self.get_system_time_stamp()
            while True:
                sample = self.buffer.peek_N('gaze', 1)
                ts = sample['system_time_stamp']
                if ts.size > 0:
                    if ts > t0:
                        break


    #%%
    def stop_recording(self,    gaze=False,
                                time_sync=False,
                                eye_image=False,
                                notifications=False,
                                external_signal=False,
                                positioning=False):
        ''' Stops recording streams
        '''
        if positioning and self.buffer.has_stream('positioning'):
            self.buffer.stop('positioning')
        if gaze and self.buffer.has_stream('gaze'):
            self.buffer.stop('gaze')
        if time_sync and self.buffer.has_stream('time_sync'):
            self.buffer.stop('time_sync')
        if eye_image and self.buffer.has_stream('eye_image'):
            self.buffer.stop('eye_image')
        if notifications and self.buffer.has_stream('notification'):
            self.buffer.stop('notification')
        if external_signal and self.buffer.has_stream('external_signal'):
            self.buffer.stop('external_signal')

    #%%
    def calibrate(self, win, win_operator=None,
                  eye='both', calibration_number = 'second'):
        ''' Enters the calibration screen and gives the user control
        over what happens
        Args:
            win - psychopy window object
            win_operator - psychopy window object for the operator screen (optional)
            eye - 'left', 'right', or 'both' - default
            calibration_number - 'first' or 'second'. If 'first', don't exit
                                 calibration mode until 'second' calibration
                                 has finished

        '''

        # Only the Tobii Pro Spectrum currently support calibrating one eye at the time
        if not TittaPy.capability.can_do_monocular_calibration in self.buffer.capabilities:
            assert eye=='both', 'Monocular calibrations available only in Tobii Pro Spectrum'

        # Generate coordinates for calibration in PsychoPy and
        # Tobii coordinate system
        if self.settings.N_CAL_TARGETS > 0:
            CAL_POS_PIX = helpers.tobii2pix(self.settings.CAL_POS_TOBII, win)
            self.CAL_POS = np.hstack((self.settings.CAL_POS_TOBII, CAL_POS_PIX))

        VAL_POS_PIX = helpers.tobii2pix(self.settings.VAL_POS_TOBII, win)
        self.VAL_POS = np.hstack((self.settings.VAL_POS_TOBII, VAL_POS_PIX))

        # Create a temp variable for screen object
        if win_operator:
            win_temp = win_operator
        else:
            win_temp = win

        self.eye = eye
        self.win = win
        self.win_operator = win_operator
        self.win_temp = win_temp
        self.mouse = event.Mouse(win=win_temp)
        self.mouse.setVisible(0)

        # Used to keep track on monocular calibrations
        self.calibration_number = calibration_number

        # Create click buttons used during calibration
        self._create_calibration_buttons()

        # Animated calibration?
        if self.settings.ANIMATE_CALIBRATION:
            self.animator = helpers.AnimatedCalibrationDisplay(self.win, self.cal_dot, self.settings.MOVE_TARGET_DURATION)

        # Main control loop
        action = 'setup'
        self.deviations = [] # List to store validation accuracies
        self.buffer.start('gaze')
        self.buffer.start('time_sync')

        calibration_started = False

        # Select action
        while True:
            self.action = action
            if 'setup' in action:
                action = self._check_head_position()
            elif 'cal' in action:

                # Enter calibration mode
                if not calibration_started:
                    if self.eye == 'both':
                        # Enter calibration mode
                        if self.settings.DEBUG:
                            print('enter_calibration_mode')
                        self.buffer.enter_calibration_mode(False) # doMonocular=False
                        res = self._wait_for_action_complete()
                    else:
                        if self.calibration_number == 'first':
                            self.buffer.enter_calibration_mode(True) # doMonocular=True
                            res = self._wait_for_action_complete()
                        if self.settings.DEBUG:
                            print('enter_calibration_mode (monocular')

                # Default to last calibration when a new
                # Calibration is run
                self.selected_calibration = len(self.deviations) + 1

                # Run calibration only if number of targets exceeds 0
                if self.settings.N_CAL_TARGETS > 0:
                    action = self._run_calibration()
                else:
                    self.final_cal_position = ()
                    action = 'val'

                calibration_started = True
            elif 'val' in action:
                action = self._run_validation()
            elif 'res' in action:
                action = self._show_validation_screen()
            elif 'done'in action:
                if self.settings.DEBUG:
                    print('calibration completed')

                # Leave calibration mode if binocular calibration or if second
                # bi-monocular calibration
                if calibration_started:
                    if self.eye == 'both':
                        self.buffer.leave_calibration_mode(False)
                        res = self._wait_for_action_complete()

                    else:
                        if self.calibration_number == 'second':
                            self.buffer.leave_calibration_mode(True)
                            res = self._wait_for_action_complete()

                # Break out of loop
                break
            elif 'quit' in action:
                if calibration_started:
                    if self.eye == 'both':
                        self.buffer.leave_calibration_mode(False)
                    else:
                        self.buffer.leave_calibration_mode(True)

                    res = self._wait_for_action_complete()

                self.buffer.stop('gaze')
                self.buffer.stop('time_sync')
                self.win.close()
                if self.win_operator:
                    self.win_operator.close()
                core.quit()
            else:
                pass


            core.wait(0.01)

        self.buffer.stop('gaze')
        self.buffer.stop('time_sync')

        # Save all calibrations (appending 'used' means that the calibration was used)
        for i, devs in enumerate(self.deviations):
            if i == self.selected_calibration - 1:
                self.all_validation_results.append(devs + ['used'])
            else:
                self.all_validation_results.append(devs + ['not used'])

    #%%
    def set_dummy_mode(self):
        # Set current class to Dummy class
        from titta import Tobii_dummy
        self.__class__ = Tobii_dummy.Connect
        self.__class__.__init__(self)

    #%%
    def _add_to_name(self, fname, append_name=True):
        # Add pid and path to name of calibration/validation images and calibration data
        # Add participant name to filename
        if append_name:
            fname = self.settings.FILENAME + '_' + fname
        # add data storage path
        if self.settings.DATA_STORAGE_PATH.strip():
            fname = self.settings.DATA_STORAGE_PATH + os.sep + fname

        return fname

    #%%
    def calibration_history(self):
        '''
        Get calibration history
        Validation results are stored in a list, where each list
        entry contains the accuracy values in degrees from
        [0] - left eye x
        [1] - left eye y
        [2] - right eye x
        [3] - right eye y

        The last entry [4] tells whether the calibration was used (1)
        or not used (0)

        So, if you want to extract the accuracy of the right eye y for the
        third attempted calibration, type
        all_validation_results[2][]

        '''
        return self.all_validation_results
    #%%
    def _draw_gaze(self):
        '''Shows gaze contingent cursor'''

        d = self.buffer.peek_N('gaze',1)

        lx = d['left_gaze_point_on_display_area_x'][0]
        ly = d['left_gaze_point_on_display_area_y'][0]
        rx = d['right_gaze_point_on_display_area_x'][0]
        ry = d['right_gaze_point_on_display_area_y'][0]

        self.et_sample_l.pos = helpers.tobii2pix(np.array([[lx, ly]]),
                                                 self.win_temp)
        self.et_sample_l.draw()
        self.et_sample_r.pos = helpers.tobii2pix(np.array([[rx, ry]]),
                                                 self.win_temp)
        self.et_sample_r.draw()

   #%%
    def _check_head_position(self):
        ''' Check to make sure that the head is in the center of the track box
        Two circles are shown; one static (representing the center of the headbox)
        and one variable representing the head position. The head is in the center
        of the trackbox the circles overlap.

        Four dot are shown in the corners. Ask the participants to fixate them
        to make sure there are not problems in the corners of the screen
        '''

        t0  = self.get_system_time_stamp()

        if self.settings.DEBUG:
            print('start_head_positioning')
        # Clear all events in mouse buffer
        event.clearEvents()

        self.mouse.setVisible(1)

        # Start user positioning guide
        self.buffer.start('positioning')

        # core.wait(0.5)

        if not self.buffer.has_stream('gaze'):
            self.win.close()
            raise Exception('Eye tracker switched on?')

        # Initiate parameters of head class (shown on participant screen)
        et_head = helpers.EThead(self.win, self.settings.HEAD_BOX_CENTER, self.settings.graphics.HEAD_POS_CIRCLE_FIXED_COLOR, self.settings.graphics.HEAD_POS_CIRCLE_MOVING_COLOR)

        # Initiate parameters of head class (shown on operator screen)
        if self.win_operator:
            et_head_op = helpers.EThead(self.win_temp, self.settings.HEAD_BOX_CENTER, self.settings.graphics.HEAD_POS_CIRCLE_FIXED_COLOR, self.settings.graphics.HEAD_POS_CIRCLE_MOVING_COLOR)

        show_eye_images = False
        image_button_pressed = False
        while True:

            # Draw four dots in the corners
            for i in self.POS_CAL_CHECK_DOTS:
                self.setup_dot.set_pos(i)
                self.setup_dot.draw()

            # Draw buttons, one to calibrate
            self.calibrate_button.draw()
            self.calibrate_button_text.draw()

            # Get keys
            k = event.getKeys()

            # Draw setup button information and check whether is was selected
            if self.buffer.has_stream('eye_image'):
                self.setup_button.draw()
                self.setup_button_text.draw()
                if self.settings.graphics.SETUP_BUTTON in k or (self.mouse.isPressedIn(self.setup_button, buttons=[0]) and not image_button_pressed):
                    # Toggle visibility of eye images
                    show_eye_images = not show_eye_images
                    image_button_pressed = True

             # Get position of eyes in track box (wait for valid samples)
            sample = self.buffer.peek_N('gaze',1)
            while len(sample['left_pupil_diameter']) == 0:
                sample = self.buffer.peek_N('gaze',1)

            sample_user_position = self.buffer.peek_N('positioning',1)
            while len(sample_user_position['left_user_position_x']) == 0:
                sample_user_position = self.buffer.peek_N('positioning',1)

            # Draw et head on participant screen
            et_head.update(sample, sample_user_position, eye=self.eye)
            et_head.draw()

            # Draw et head on operator screen
            if self.win_operator:
                et_head_op.update(sample, sample_user_position, eye=self.eye)
                et_head_op.draw()

            # Draw instruction
            self.instruction_text.pos = (0, 0.8)
            self.instruction_text.text = 'Position yourself such that the two circles overlap.'
            self.instruction_text.draw()

            # Get and draw distance information
            l_pos = []
            r_pos = []
            for letter in ['x', 'y', 'z']:
                l_pos.append(sample[f'left_gaze_origin_in_user_coordinates_{letter}'][0])
                r_pos.append(sample[f'right_gaze_origin_in_user_coordinates_{letter}'][0])

            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    self.instruction_text_op.pos = (0, 0.9)

                    if len(self.settings.HEAD_BOX_CENTER) == 0:
                        self.instruction_text_op.text = f'Distance: {int(np.nanmean([l_pos[2], r_pos[2]])/10.0)} cm'
                    else:
                        self.instruction_text_op.text = f'Cyclopean eye position (x, y, z):, \
{int(np.nanmean([l_pos[0], r_pos[0]])/10.0)}, \
{int(np.nanmean([l_pos[1], r_pos[1]])/10.0)}, \
{int(np.nanmean([l_pos[2], r_pos[2]])/10.0)} cm'
                    self.instruction_text_op.draw()
            except:
                pass

            # Show eye images if requested
            if show_eye_images:
                # Start streaming of eye images
                if self.buffer.has_stream('eye_image') and not self.buffer.is_recording('eye_image'):
                    self.buffer.start('eye_image')

                self._draw_eye_image()
            else:
                if self.buffer.has_stream('eye_image') and self.buffer.is_recording('eye_image'):
                    self.buffer.stop('eye_image')

            # check whether someone left clicked any of the buttons or pressed 'space'
            if self.settings.graphics.CAL_BUTTON in k or self.mouse.isPressedIn(self.calibrate_button, buttons=[0]):
                action = 'cal'
                break

            if 'escape' in k:
                action = 'quit'
                break

            # Option to skip calibration (no button for this?)
            if 'return' in k:
                action = 'done'
                break

            # Wait for release of show gaze_button
            if not np.any(self.mouse.getPressed()):
                image_button_pressed = False

            # Update the screen
            self.win.flip()
            if self.win_operator:
                self.win_temp.flip()

        self.mouse.setVisible(0)

        # Always stop image stream (if running) before leaving setup
        if self.buffer.has_stream('eye_image') and self.buffer.is_recording('eye_image'):
            self.buffer.stop('eye_image')

        # Stop user position guide
        self.buffer.stop('positioning')

        # Clear information from all available streams
        t1 = self.get_system_time_stamp()
        self.buffer.clear_time_range('gaze', t0, t1)

        if self.buffer.has_stream('eye_image'):
            self.buffer.clear_time_range('eye_image', t0, t1)

        # Clear the screen
        self.win.flip()
        if self.win_operator:
            self.win_temp.flip()

        if self.settings.DEBUG:
            print('stop_head_positioning')

        return action

    #%% _
    def _draw_operator_screen(self, pos, sample):
        ''' Draws what the operator sees in dual screen mode

        Args:
            bg - background (either image with calibration points or validation points)
            pos - current position of calibration / validation dot
            sample - dict with eye tracker sample
        '''

        # Draw calibration / validation dots
        # self.bg.draw()

        # Draw current target (red cicle)
        self.current_point.set_pos(helpers.tobii2norm(np.expand_dims(pos, axis=0)))
        self.current_point.draw()

        # Draw data for the left and right eyes
        self.raw_et_sample_l.pos = helpers.tobii2norm(np.expand_dims((sample['left_gaze_point_on_display_area_x'][0],
                                                                      sample['left_gaze_point_on_display_area_y'][0]),
                                                                      axis=0))
        self.raw_et_sample_r.pos = helpers.tobii2norm(np.expand_dims((sample['right_gaze_point_on_display_area_x'][0],
                                                                      sample['right_gaze_point_on_display_area_y'][0]),
                                                                      axis=0))
        self.raw_et_sample_l.draw()
        self.raw_et_sample_r.draw()

        # Draw eye images for the left and right eyes
        self._draw_eye_image()

    #%%
    def _wait_for_action_complete(self):
        ''' Wait for an action to finish (and see if i succeded)

        returns:
            information about the completed action
            res-  e.g.,
            print(res.work_item.action)
            print(res.work_item.coordinates)
            print(res.status_string)
        '''

        res = None
        while res==None:
            res = self.buffer.calibration_retrieve_result()

        return res

    #%%
    def _run_calibration(self):
        ''' Calibrates the eye tracker
        Args:   target_pos: N x 4 array with target positions
                first two columns are Tobii coords (x, y) and the two last
                are position in degrees (PsychoPy coord system)
                pval: pacing interval (how long each dot is shown)
        '''


        self.win.flip()
        if self.win_operator:
            self.win_operator.flip()

        paval=self.settings.PACING_INTERVAL

        # Optional start recording of eye images
        if self.settings.RECORD_EYE_IMAGES_DURING_CALIBRATION or self.win_operator:
            if self.buffer.has_stream('eye_image') and not self.buffer.is_recording('eye_image'):
                self.buffer.start('eye_image')

        self.send_message('Calibration_start')

        action = 'setup'

        # Go through the targets one by one
        cal_pos=self.CAL_POS
        np.random.shuffle(cal_pos)
        t0 = self.clock.getTime()
        i = 0
        pos_old = [0, 0]
        animation_state = 'static'
        tick = 0
        autopace = self.settings.AUTO_PACE
        while True:

            k = event.getKeys()

            # Get current calibration target position
            pos = cal_pos[i, 2:] # Psychopoy and Tobii have different coordinate systems
            tobii_data = cal_pos[i, :2]

            # Animate calibration dots or show static dots?
            if self.settings.ANIMATE_CALIBRATION:
                if animation_state == 'move':
                    move_completed = self.animator.move_point(pos_old, (pos[0], pos[1]), tick)
                    if move_completed:
                        animation_state = 'static' # or move
                        tick = 0
                        t0 = self.clock.getTime()
                else:
                    self.animator.animate_point(0, (pos[0], pos[1]), tick)
            else:
                self.cal_dot.set_pos(pos)
                self.cal_dot.draw()

            if self.win_operator:
                self._draw_operator_screen(tobii_data,
                                           self.buffer.peek_N('gaze', 1))
                self.win_temp.flip()

            self.win.flip()

            # Send a message at the onset (first frame) of a new dot
            # Always happens when tick == 0
            if tick == 0 and animation_state == 'static':
                self.send_message('calibration point {} at position {} {}'.format(i, pos[0], pos[1]))

            # Time to switch to a new point
            if autopace == 2 or 'space' in k:

                # Switch to fully automatic pacing once first point is accepted
                if self.settings.AUTO_PACE == 1:
                    autopace = 2

                if (self.clock.getTime() - t0) > paval:

                    pos_old = pos[:]
                    i += 1

                    # Collect some calibration data
                    if self.eye == 'both':
                        self.buffer.calibration_collect_data(tobii_data)
                    else:
                        self.buffer.calibration_collect_data(tobii_data, self.eye)

                    res = self._wait_for_action_complete()

                    if self.settings.DEBUG:
                        print(res['work_item']['action'])
                        print(res['work_item']['coordinates'])
                        print(res['status_string'])

                    if i == self.settings.N_CAL_TARGETS:
                        self.final_cal_position = copy.deepcopy(pos)
                        break

                    t0 = self.clock.getTime()

                    tick = 0
                    animation_state = 'move'

            # Abort calibration if esc is pressed (and go back to setup screen)
            if 'escape' in k:
                return action

            # 'r' aborts and restarts calibration
            if 'r' in k:
                action = 'cal'
                return action

            tick += 1

        # Apply the calibration
        self.buffer.calibration_compute_and_apply()
        res = self._wait_for_action_complete()

        if self.settings.DEBUG:
            print(res['work_item']['action'])
            print(res['status_string'])
            print(res['calibration_result'])


        # Accept of redo the calibration?
        if res['status'] == 0 and len(res['calibration_result']['points']) > 0:
            action = 'val'
            cal_data = self._generate_calibration_image(res)
        else:
            self.instruction_text.text = 'Calibration unsuccessful.'
            self.instruction_text.draw()
            self.win.flip()
            core.wait(1)

        self.send_message('Calibration_stop')

        # Stop recording of eye images unless validation is next
        if 'val' not in action:
            if self.settings.RECORD_EYE_IMAGES_DURING_CALIBRATION or self.win_operator:
                if self.buffer.has_stream('eye_image') and self.buffer.is_recording('eye_image'):
                    self.buffer.stop('eye_image')

        return action


    #%%
    def _generate_calibration_image(self, calibration_result): # TODO: display of gaze data on image does not seem correct
        ''' Generates visual representation of calibration results
        Plot only those who are valid and used?
        '''

        cal_data = []   # where calibration deviations are stored
        xys_left = []   # container for gaze data (left eye)
        xys_right = []  # container for gaze data (right eye)

        # Display the results to the user (loop over each calibration point)
        for p in calibration_result['calibration_result']['points']:

            # Draw calibration dots
            x_dot = p['position_on_display_area_x']
            y_dot = p['position_on_display_area_y']
            self.cal_dot.fillColor = 'white'
            xy_dot = helpers.tobii2pix(np.array([[x_dot, y_dot]]),
                                       self.win)
            self.cal_dot.set_pos(xy_dot) # Tobii and psychopy have different coord systems
            self.cal_dot.draw()

            if self.eye == 'both' or self.eye == 'left':
                # Save gaze data for left eye to list
                x = p['samples_left_position_on_display_area_x']
                y = p['samples_left_position_on_display_area_y']
                xy_sample = helpers.tobii2pix(np.column_stack((x, y)),
                                              self.win) # Tobii and psychopy have different coord systems
                for xy in xy_sample:
                    xys_left.append([xy[0], xy[1]])
                    cal_data.append([x_dot, y_dot, xy[0], xy[1], 'left'])

            if self.eye == 'both' or self.eye == 'right':
                 # Save gaze data for right eye to list
                 x = p['samples_right_position_on_display_area_x']
                 y = p['samples_right_position_on_display_area_y']
                 xy_sample = helpers.tobii2pix(np.column_stack((x, y)),
                                               self.win) # Tobii and psychopy have different coord systems
                 for xy in xy_sample:
                     xys_right.append([xy[0], xy[1]])
                     cal_data.append([x_dot, y_dot, xy[0], xy[1], 'right'])

        samples = visual.ElementArrayStim(self.win,
                                          sizes=self.settings.graphics.ET_SAMPLE_RADIUS,
                                          fieldSize=(100, 100),
                                          nElements=np.max([len(xys_left),
                                                            len(xys_right)]),
                                          elementTex=None,
                                          elementMask='circle',
                                          units='pix')

        # Draw calibration gaze data samples for left eye and right eyes
        if self.eye == 'both' or self.eye == 'left':
            samples.xys = np.array(xys_left)
            samples.colors = 'red'
            samples.draw()

        if self.eye == 'both' or self.eye == 'right':
            samples.xys = np.array(xys_right)
            samples.colors = 'blue'
            samples.draw()

        # Save validation results as image
        # nCalibrations = len(self.deviations) + 1
        fname = 'calibration_image' + str(self.selected_calibration)+'.png'
        fname = self._add_to_name(fname)
        self.win.getMovieFrame(buffer='back')
        self.win.saveMovieFrames(fname)

        # Clear the back buffer without flipping the window
        self.win.clearBuffer()

        return cal_data

    #%%
    def _save_calibration(self, filename):
        ''' Save the calibration to a .bin file
        Args:
            filename: test
        Returns:
            -
        '''
        self.buffer.calibration_get_data()
        res = self._wait_for_action_complete()
        calibration_data = res['calibration_data']

        if self.settings.DEBUG:
            print(res['work_item']['action'])
            print(res['status_string'])

        # None is returned on empty calibration.
        if calibration_data != None:
            if self.settings.DEBUG:
                print("Saving calibration to file {} for eye tracker with serial number {}.".format(filename, self.buffer.serial_number))

            # if a path is given by the user, use it!
            filename = self._add_to_name(filename)

            with open(filename + '.cal', 'wb') as handle:
                pickle.dump(calibration_data, handle)
        else:
            if self.settings.DEBUG:
                print("No calibration available for eye tracker with serial number {0}.".format(self.buffer.serial_number))
    #%%
    def _load_calibration(self, filename):
        ''' Loads the calibration to a .bin file
        Args:
            filename: test
        Returns:
            -
        '''
        # if a path is given by the user, use it!
        filename = self._add_to_name(filename)

        # Read the calibration from file.
        with open(filename + '.cal', 'rb') as handle:
            calibration_data = pickle.load(handle)

        # Don't apply empty calibrations.
        if len(calibration_data) > 0:
            if self.settings.DEBUG:
                print("Applying calibration {} on eye tracker with serial number {}.".format(filename, self.buffer.serial_number))
            self.buffer.calibration_apply_data(calibration_data)
            res = self._wait_for_action_complete()

            if self.settings.DEBUG:
                print(res['work_item']['action'])
                print(res['status_string'])

    #%%
    def _run_validation(self):
        ''' Runs a validation to check the accuracy of the calibration
        '''

        target_pos = self.VAL_POS
        paval = self.settings.PACING_INTERVAL

        np.random.shuffle(target_pos)

        # Set this to true if you want all data from the validation to
        # end up in the main data file (default, False)
        self.send_message('Validation_start')

        action = 'setup'
        # Go through the targets one by one
        self.clock.reset()
        i = 0

        if self.settings.N_CAL_TARGETS == 0:
            pos_old = [0, 0]
        else:
            pos_old = self.final_cal_position

        validation_data = []
        xy_pos = []
        animation_state = 'move'
        tick = 0
        while True:

            k = event.getKeys()

            # Get current calibration target position
            pos = target_pos[i, 2:] # Psychopoy and Tobii have different coordinate systems

            # Animate calibration dots or show static dots?
            if self.settings.ANIMATE_CALIBRATION:
                if animation_state == 'move':
                    move_completed = self.animator.move_point(pos_old, (pos[0], pos[1]), tick)
                    if move_completed:
                        animation_state = 'static' # or move
                        tick = 0
                        self.clock.reset()
                else:
                    self.animator.animate_point(0, (pos[0], pos[1]), tick)
            else:
                animation_state == 'static'
                self.cal_dot.set_pos(pos)
                self.cal_dot.draw()

            if self.win_operator:
                self._draw_operator_screen(target_pos[i, :2], self.buffer.peek_N('gaze',1))
                self.win_temp.flip()

            self.win.flip()

            # Send a message at the onset (first frame) of a new dot
            # Always happens when tick == 0
            # animation_state 'static' means that the dot has completed the
            # movement to a new location.
            if tick == 0 and animation_state == 'static':
                self.send_message('validation point {} at position {} {}'.format(i, pos[0], pos[1]))

            # # Start collecting validation data for a point 500 ms after its onset
            # if (self.clock.getTime() >= 0.500 and self.clock.getTime() < 0.800) and not buffer_started:
            #     self.start_ring_buffer(sample_buffer_length=300)
            #     buffer_started = True

            # Get the last 300 ms of data from the buffer
            if self.clock.getTime() >= 0.800:
                sample = self.buffer.peek_N('gaze',
                                             int(self.buffer.frequency * 0.300))

            # Time to switch to a new point
            if self.settings.AUTO_PACE > 0 or 'space' in k:
                if self.clock.getTime() > paval:

                    # Collect validation data from this point
                    validation_data.append(sample)

                    # Save data as xy list (Change so it's saved to a np.array directly)
                    for ii in range(len(sample['system_time_stamp'])):
                        xy_pos.append([sample['system_time_stamp'][ii],
                                       sample['left_gaze_point_on_display_area_x'][ii],
                                       sample['left_gaze_point_on_display_area_y'][ii],
                                       sample['right_gaze_point_on_display_area_x'][ii],
                                       sample['right_gaze_point_on_display_area_y'][ii],
                                       pos[0], pos[1]])
                    pos_old = pos[:]

                    self.clock.reset()
                    tick = 0
                    animation_state = 'move'

                    i += 1

                    if i > (np.shape(target_pos)[0] - 1):
                        break

            # Abort calibration if esc is pressed (and go back to setup screen)
            if 'escape' in k:
                return action

            # 'r' aborts and restarts calibration
            if 'r' in k:
                action = 'cal'
                return action

            tick += 1


        ##############
        self.send_message('Validation_end')

        self.win.flip()

        # Convert data from Tobii coord system to PsychoPy coordinates
        gaze_pos = np.array(xy_pos)
        gaze_pos[:, 1:3] = helpers.tobii2pix(gaze_pos[:, 1:3], self.win)
        gaze_pos[:, 3:5] = helpers.tobii2pix(gaze_pos[:, 3:5], self.win)

        # Compute data quality per validation point
        deviation_l, rms_l, sd_l, data_loss_l = self._compute_data_quality(validation_data, target_pos[:, :2], 'left')
        deviation_r, rms_r, sd_r, data_loss_r = self._compute_data_quality(validation_data, target_pos[:, :2], 'right')

        if self.eye == 'left':
            deviation_r = np.nan
            rms_r = np.nan
            sd_r = np.nan
            data_loss_r = np.nan

        if self.eye == 'right':
            deviation_l = np.nan
            rms_l = np.nan
            sd_l = np.nan
            data_loss_l = np.nan

        # FIXME: C:\git\Titta\titta\Tobii.py: RuntimeWarning: Mean of empty slice
        data_quality_values = [np.nanmean(deviation_l), np.nanmean(deviation_r),
                                np.nanmean(rms_l), np.nanmean(rms_r),
                                np.nanmean(data_loss_l) * 100, np.nanmean(data_loss_r) * 100,
                                np.nanmean(sd_l), np.nanmean(sd_r)]

        self.deviations.insert(self.selected_calibration - 1,
                               data_quality_values)

        self.send_message('validation data quality Dev_L: {:.2f}, Dev_R: {:.2f} RMS_L: {:.2f}, \
RMS_R: {:.2f}, LOSS_L: {:.1f}, LOSS_R: {:.1f}, SD_L: {:.2f}, SD_R: {:.2f}' \
.format(data_quality_values[0],
        data_quality_values[1],
        data_quality_values[2],
        data_quality_values[3],
        data_quality_values[4],
        data_quality_values[5],
        data_quality_values[6],
        data_quality_values[7]))


        self._generate_validation_image(target_pos[:, 2:], gaze_pos[:, :-2])
        action = 'res' # Show validation results

        # Stop recording of eye images
        if self.settings.RECORD_EYE_IMAGES_DURING_CALIBRATION or self.win_operator:
            if self.buffer.has_stream('eye_image') and self.buffer.is_recording('eye_image'):
                self.buffer.stop('eye_image')

        return action

    #%%
    def _generate_validation_image(self, dot_positions, gaze_positions):
        ''' Generates visual representation of validation results

        Args:
            dot_positions - n x 2 list with x, y location of validation dots
            gaze_positions - n x 5 array, t, lx, ly, rx, ry

        All values should be in the current screen units
        '''

        # Used to draw many dots
        samples = visual.ElementArrayStim(self.win,
                                          sizes=self.settings.graphics.ET_SAMPLE_RADIUS,
                                          fieldSize = (100, 100),  #self.settings.SAMPLE_DOT_SIZE,
                                          nElements = gaze_positions.shape[0],
                                          elementTex=None, elementMask='circle', units='pix')

        # Show all dots...
        for p in dot_positions:
            self.cal_dot.set_pos(p )
            self.cal_dot.draw()

        #... and collected validation samples for left...
        if self.eye == 'both' or self.eye == 'left':
            samples.xys = gaze_positions[:, 1:3]
            samples.colors = 'red'
            samples.draw()

        #... and right eye
        if self.eye == 'both' or self.eye == 'right':
            samples.xys = gaze_positions[:, 3:5]
            samples.colors = 'blue'
            samples.draw()

        # Save validation results as image
        # nCalibrations = len(self.deviations)

        fname = 'validation_image' + str(self.selected_calibration) + '.png'
        fname = self._add_to_name(fname)

        self.win.getMovieFrame(buffer='back')
        self.win.saveMovieFrames(fname)

        # Clear the back buffer without flipping the window
        self.win.clearBuffer()

        # Delete samples
        del samples

    #%%
    def _adcs2ucs(self, v):
        ''' Convert 2D point from Active Display Coordinate System (ADCS) to
        3D point in Tobii User Coordinate System (USC)
        Args:
            v - (x, y) in ADCS, e.g, (0.54, 0.1), norm [0 -> 1]

        Returns
            u - (x, y, z) in UCS in mm
        '''

        display_area = self.buffer.display_area

#        print("Bottom Left: {0}".format(display_area.bottom_left))
#        print("Bottom Right: {0}".format(display_area.bottom_right))
#        print("Height: {0}".format(display_area.height))
#        print("Top Left: {0}".format(display_area.top_left))
#        print("Top Right: {0}".format(display_area.top_right))
#        print("Width: {0}".format(display_area.width))

        dx = (np.array(display_area['top_right']) - np.array(display_area['top_left'])) * v[0]
        dy = (np.array(display_area['bottom_left']) - np.array(display_area['top_left'])) * v[1]

        u = np.array(display_area['top_left']) + dx + dy

        return u
    #%%
    def _compute_data_quality(self, validation_data, val_point_positions, eye):
        ''' Computes data quality (deviation, rms) per validation point

        Args:
            validation_data - list with validation data per validation point
            val_point_positions - list with [x, y] pos of validation point
                                    in ADCS
            eye - 'left' or 'right'
        '''
        # For each point
        deviation_per_point = []
        rms_per_point = []
        sd_per_point = []
        data_loss_point = []
        for p, point_data in enumerate(validation_data):

            val_point_position = self._adcs2ucs(val_point_positions[p])

            # For each sample (in a validation point)
            deviation_per_sample = []
            angle_between_samples = []
            gaze_vector_old = 0
            n_samples = len(point_data['system_time_stamp'])
            n_invalid_samples = 0
            for i in range(n_samples):
                gaze_vector = (point_data[f"{eye}_gaze_point_in_user_coordinates_x"][i] -
                               point_data[f"{eye}_gaze_origin_in_user_coordinates_x"][i],
                               point_data[f"{eye}_gaze_point_in_user_coordinates_y"][i] -
                               point_data[f"{eye}_gaze_origin_in_user_coordinates_y"][i],
                               point_data[f"{eye}_gaze_point_in_user_coordinates_z"][i] -
                               point_data[f"{eye}_gaze_origin_in_user_coordinates_z"][i])

                if np.any(np.isnan(gaze_vector)):
                    n_invalid_samples += 1

                eye_to_valpoint_vector = (val_point_position[0] -
                               point_data[f"{eye}_gaze_origin_in_user_coordinates_x"][i],
                               val_point_position[1] -
                               point_data[f"{eye}_gaze_origin_in_user_coordinates_y"][i],
                               val_point_position[2] -
                               point_data[f"{eye}_gaze_origin_in_user_coordinates_z"][i])

                # Compute RMS (diff between consecutive samples) and deviation
                deviation_per_sample.append(helpers.angle_between(gaze_vector, eye_to_valpoint_vector))
                if i > 0:
                    angle_between_samples.append(helpers.angle_between(gaze_vector, gaze_vector_old))

                gaze_vector_old = gaze_vector

            # Compute averages per point
            deviation_per_point.append(np.rad2deg(np.nanmedian(deviation_per_sample)))
            rms_per_point.append(np.rad2deg(helpers.rms(angle_between_samples)))
            sd_per_point.append(np.rad2deg(helpers.sd(angle_between_samples)))
            data_loss_point.append(n_invalid_samples / float(n_samples))

        return deviation_per_point, rms_per_point, sd_per_point, data_loss_point


    #%%
    def _show_validation_screen(self):
        ''' Shows validation image after a validation has been completed
        '''

        # Get timestamp
        t0_clear = self.get_system_time_stamp()

        # Center position of presented calibration values
        x_pos_res = 0.55
        y_pos_res = 0.2

        self.mouse.setVisible(1)

        # get (and save) validation screen image
        nCalibrations = len(self.deviations)
        self._save_calibration(str(nCalibrations))

        # Add image as texture
        fname = 'validation_image' + str(self.selected_calibration)+'.png'
        fname = self._add_to_name(fname)

        self.accuracy_image.image = fname
        show_validation_image = True    # Default is to show validation results,
                                        # not calibration results

        # information about data quality header
        header = ['Quality', 'Left eye', 'Right eye', 'Left eye', 'Right eye',
                   'Left eye', 'Right eye']
        header_colors = [self.settings.graphics.TEXT_COLOR,
                         'red', 'blue', 'red', 'blue', 'red', 'blue']
        x_pos= np.linspace(-0.35, 0.35, num = 7)

        # Prepare rects for buttons, button text, and accuracy values
        select_accuracy_rect = []
        select_rect_text = []
        accuracy_values = []#[0] * len(x_pos)] * nCalibrations
        # print(accuracy_values)

        y_pos = y_pos_res

        for i in range(nCalibrations):
            select_accuracy_rect.append(visual.Rect(self.win_temp, width= 0.15,
                                                height= 0.05,
                                                units='norm',
                                                pos = (x_pos_res, y_pos)))

            select_rect_text.append(visual.TextStim(self.win_temp,
                                                    text='Select',
                                                    wrapWidth = 1,
                                                    height = self.settings.graphics.TEXT_SIZE,
                                                    color = self.settings.graphics.TEXT_COLOR,
                                                    units='norm',
                                                    pos = (x_pos_res, y_pos)))

            # Then prepare the accuracy values for each calibration preceded
            # by Cal x (the calibration number)
            accuracy_values_j = []
            for j, x in enumerate(x_pos):
                if j > 0:

                    if j >= len(x_pos) - 2:
                        number_of_decimals = '{0:.0f}'
                    else:
                        number_of_decimals = '{0:.2f}'

                    accuracy_values_j.append(visual.TextStim(self.win_temp,
                                                        text=number_of_decimals.format(self.deviations[i][j - 1]),
                                                        wrapWidth = 1,
                                                        height = self.settings.graphics.TEXT_SIZE,
                                                        units='norm',
                                                        color = header_colors[j],
                                                        pos = (x, y_pos)))
                else:
                    accuracy_values_j.append(visual.TextStim(self.win_temp,
                                                        text='Cal' + str(i+1) + ':',
                                                        wrapWidth = 1,
                                                        height = self.settings.graphics.TEXT_SIZE,
                                                        units='norm',
                                                        color = header_colors[j],
                                                        pos = (x, y_pos)))
            accuracy_values.append(accuracy_values_j)
            y_pos -= 0.06

        # Prepare main header
        header_main_text = ['Accuracy (deg)', 'Precision (deg)', 'Data loss (%)']
        self.instruction_text.setColor([1, 1, 1], colorSpace='rgb')
        y_pos_main = y_pos_res + 0.13
        x_pos_main = np.linspace(-0.17, 0.30, num = 3)

        header_text_main = []
        for j, x in enumerate(x_pos_main):
            header_text_main.append(visual.TextStim(self.win_temp,text=header_main_text[j],
                                                wrapWidth = 1,
                                                height = self.settings.graphics.TEXT_SIZE,
                                                units='norm',
                                                pos = (x, y_pos_main),
                                                color = self.settings.graphics.TEXT_COLOR))
        # Prepare header
        header_text = []
        self.instruction_text.setColor([1, 1, 1], colorSpace='rgb')
        y_pos = y_pos_res
        for j, x in enumerate(x_pos):
            header_text.append(visual.TextStim(self.win_temp,text=header[j],
                                                wrapWidth = 1,
                                                height = self.settings.graphics.TEXT_SIZE,
                                                units='norm',
                                                pos = (x, y_pos_res + 0.06),
                                                color = header_colors[j]))


        # Wait for user input
        selection_done = False
        display_gaze = False
        gaze_button_pressed = False
        cal_image_button_pressed = False
        timing = []

        # If there's an operator screen, just show a message 'please wait...'
        # on the participant screen
        if self.win_operator:
            self.instruction_text.text = 'Please wait...'

        while not selection_done:

            t0 = self.clock.getTime()

            # Draw validation results image
            self.accuracy_image.draw()

            # Draw buttons (re-calibrate, accept and move on, show gaze)
            self.recalibrate_button.draw()
            self.recalibrate_button_text.draw()

            self.revalidate_button.draw()
            self.revalidate_button_text.draw()

            self.accept_button.draw()
            self.accept_button_text.draw()

            self.gaze_button.draw()
            self.gaze_button_text.draw()

            if self.settings.N_CAL_TARGETS > 0:
                self.calibration_image.draw()
                self.calibration_image_text.draw()

            # Draw headers
            [h.draw() for h in header_text_main]
            [hh.draw() for hh in header_text]

            # Draw accuracy/precision values and buttons to select a calibration
            for i in range(nCalibrations):

                # Highlight selected calibrations
                if i == self.selected_calibration - 1: # Calibration selected
                    select_accuracy_rect[i].fillColor = self.settings.graphics.blue_active
                    if nCalibrations > 1:
                        select_accuracy_rect[i].draw()
                        select_rect_text[i].draw()
                else:
                    select_accuracy_rect[i].fillColor = self.settings.graphics.blue
                    select_accuracy_rect[i].draw()
                    select_rect_text[i].draw()

                # Then draw the accuracy values for each calibration preceded
                # by Cal x (the calibration number)
                for j, x in enumerate(x_pos):
                    accuracy_values[i][j].draw()

            # Check if mouse is clicked to select a calibration
            for i, button in enumerate(select_accuracy_rect):
                if self.mouse.isPressedIn(button):
                    self._load_calibration(str(i + 1))  # Load the selected calibration
                    if show_validation_image:
                        fname = 'validation_image' + str(i + 1) + '.png'
                    else:
                        fname = 'calibration_image' + str(i + 1) + '.png'
                    fname = self._add_to_name(fname)

                    self.accuracy_image.image = fname
                    self.selected_calibration = int(i + 1)
                    break

            # Check if key or button is pressed
            k = event.getKeys()
            if self.settings.graphics.RECAL_BUTTON in k or self.mouse.isPressedIn(self.recalibrate_button):
                action = 'setup'
                selection_done = True
            elif self.settings.graphics.REVAL_BUTTON in k or self.mouse.isPressedIn(self.revalidate_button):

                action = 'val'

                # Delete previous validation results, since we want to
                # re-validate
                self.deviations.pop(self.selected_calibration - 1)

                selection_done = True
            elif self.settings.graphics.ACCEPT_BUTTON in k or self.mouse.isPressedIn(self.accept_button):
                action = 'done'
                selection_done = True
            elif k:
                if k[0].isdigit():
                    if any([s for s in range(nCalibrations+1) if s == int(k[0])]):
                        self._load_calibration(k[0])  # Load the selected calibration
                        fname = 'validation_image' + str(k[0]) + '.png'
                        fname = self._add_to_name(fname)
                        self.accuracy_image.image = fname
                        self.selected_calibration = int(k[0])

            elif 'escape' in k:
                action = 'quit'
                break

            # Toggle display gaze
            if self.settings.graphics.GAZE_BUTTON in k or (self.mouse.isPressedIn(self.gaze_button, buttons=[0]) and not gaze_button_pressed):
                display_gaze = not display_gaze
                gaze_button_pressed = True

            # Display gaze along with four dots in the corners
            if display_gaze:
                for i in self.POS_CAL_CHECK_DOTS:
                    self.setup_dot.set_pos(i)
                    self.setup_dot.draw()
                self._draw_gaze()

            # Show calibration image or validation image
            if self.settings.N_CAL_TARGETS > 0:
                if self.settings.graphics.CAL_IMAGE_BUTTON in k or (self.mouse.isPressedIn(self.calibration_image, buttons=[0])and not cal_image_button_pressed):

                    # Toggle the state of the button
                    show_validation_image = not show_validation_image

                    # If validation image show, switch to calibration and vice versa
                    if show_validation_image:
                        fname = 'validation_image' + str(self.selected_calibration)+'.png'
                        fname = self._add_to_name(fname)
                        self.accuracy_image.image = fname
                        self.calibration_image_text.text = self.settings.graphics.CAL_IMAGE_BUTTON_TEXT
                    else:
                        fname = 'calibration_image' + str(self.selected_calibration)+'.png'
                        fname = self._add_to_name(fname)
                        self.accuracy_image.image = fname
                        self.calibration_image_text.text = 'Show validation (s)'

                    cal_image_button_pressed = True

            # Wait for release of show gaze_button
            if not np.any(self.mouse.getPressed()):
                gaze_button_pressed = False
                cal_image_button_pressed = False

            timing.append(self.clock.getTime() - t0)

            if self.win_operator:
                self.win_temp.flip()
                self.instruction_text.draw()

            self.win.flip()

        # Clear data that were recorded during the validation screen
        t1_clear = self.get_system_time_stamp()
        self.buffer.clear_time_range('gaze', t0_clear, t1_clear)

        if self.buffer.has_stream('eye_image'):
            self.buffer.clear_time_range('eye_image', t0_clear, t1_clear)

        # Clear screen and return
        self.instruction_text.setColor([1, 1, 1], colorSpace='rgb')
        self.win.flip()
        self.mouse.setVisible(0)


        return action

    #%%
    def system_info(self):
        ''' Returns information about system in dict
        '''

        info = {}
        info['serial_number']  = self.buffer.serial_number
        info['address']  = self.buffer.address
        info['model']  = self.buffer.model
        info['name']  = self.buffer.device_name
        info['firmware_version'] = self.buffer.firmware_version
        info['runtime_version'] = self.buffer.runtime_version
        info['tracking_mode']  = self.buffer.tracking_mode
        info['sampling_frequency']  = self.buffer.frequency

        try:
            info['track_box']  = self.buffer.track_box
        except:
            print('track box not supported by this eye tracker')

        info['display_area']  = self.buffer.display_area
        info['python_version'] = '.'.join([str(sys.version_info[0]),
                                           str(sys.version_info[1]),
                                           str(sys.version_info[2])])
        info['psychopy_version'] = psychopy.__version__
        info['TittaPy_version'] = TittaPy.__version__
        info['Tobii_SDK_version'] = TittaPy.get_SDK_version()
        info['titta_version'] = titta.__version__
        # info['git_revision'] = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()

        return info

    #%%
    def get_system_time_stamp(self):
        ''' Get system time stamp
        '''

        return TittaPy.get_system_timestamp()

    #%%
    def send_message(self, msg, ts=None):
        ''' Sends a message to the data file
        '''

        if not ts:
            ts = self.get_system_time_stamp()
        self.msg_container.append([ts, msg])


    #%%
    def _draw_eye_image(self):
        ''' Draw left and right eye image
        '''

        if self.buffer.has_stream('eye_image'):

            # Grab the two most recent eye images from the buffer
            if self.settings.eye_tracker_name == 'Tobii Pro Fusion':
                eye_images = self.buffer.peek_N('eye_image', 4, 'end')
            else:
                eye_images = self.buffer.peek_N('eye_image', 2, 'end')


            for i in range(len(eye_images['image'])):

                # Read eye image
                im_arr = eye_images['image'][i]

                # Convert to have values between -1 adn 1
                im_arr = np.fliplr(np.flipud((im_arr / float(255) * 2.0) - 1))

                # Always display image from camera_id == 0 on left side
                if eye_images['camera_id'][i] == 0:
                    if eye_images['region_id'][i] == 0:
                        self.eye_image_stim_l.image = im_arr
                    else:
                        self.eye_image_stim_r_1.image = im_arr
                else:
                    if eye_images['region_id'][i] == 0:
                        self.eye_image_stim_r.image = im_arr
                    else:
                        self.eye_image_stim_l_1.image = im_arr

            # Draw eye images
            self.eye_image_stim_l.draw()
            self.eye_image_stim_r.draw()

            # The Fusion has 4 eye images, while Spectrum only 2
            if self.settings.eye_tracker_name == 'Tobii Pro Fusion':
                self.eye_image_stim_l_1.draw()
                self.eye_image_stim_r_1.draw()

    #%%
    def set_sample_rate(self, Fs):
        '''Sets the sample rate
        '''

        # print([i for i in self.buffer.supported_frequencies], Fs)
        assert np.any([int(i) == Fs for i in self.buffer.supported_frequencies]), "Supported frequencies are: {}".format(self.buffer.supported_frequencies)

        self.buffer.frequency = int(Fs)
    #%%
    def get_sample_rate(self):
        '''Gets the sample rate
        '''
        return self.buffer.frequency

    #%%
    def save_data(self, filename=None, append_version=True):
        ''' Saves the data to HDF5 container
        If you want to read the data, see the 'resources' folder

        Args:
            filename - if a filename is given, it overrides the name stored
                in self.settings.FILENAME
            append_version : if file exists, it is appended with filename_1 etc.
                THis is to prevent file from being overwritten
        '''

        t0 = time.time()

        if filename:
            fname = filename
        else:
            fname = self.settings.FILENAME

        # Check if the filename already exists, if so append to name
        i = 1
        filename_ext = ''

        # If a path for data storage is given, use that, otherwise save data
        # in current working directory
        if self.settings.DATA_STORAGE_PATH.strip():
            files = Path(self.settings.DATA_STORAGE_PATH).glob('*.h5')
        else:
            files = Path.cwd().glob('*.h5')

        #print(Path.cwd())
        while True:

            # Go through the files and look for a match
            filename_exists = False
            for f in files:
                f_temp = str(f).split(os.sep)[-1].split('.')[0]
                #print(f_temp, fname)

                # if the file exists
                if fname + filename_ext == f_temp:
                    if not append_version:
                        print('Warning! Filename already exists. Will be overwritten.')
                    else: # append '_i to filename
                        filename_ext = '_' + str(i)
                        i += 1
                    filename_exists = True
                    break

            # If we've gone through all files without
            # a match, we ready!
            if not filename_exists:
                 break

         # Add the new extension the the filename
        fname = os.sep.join([fname + filename_ext])
        fname = self._add_to_name(fname, append_name=False)

        # Save gaze data to HDF5 container
        temp = self.buffer.consume_N('gaze',sys.maxsize)
        pd.DataFrame.from_dict(temp).to_hdf(fname + '.h5', key='gaze')

        # Save messages as HDF5 container
        df_msg = pd.DataFrame(self.msg_container,  columns=['system_time_stamp', 'msg'])
        df_msg.to_hdf(fname + '.h5', key='msg')

        # Save all other gaze streams in the same HDF5 container
        if self.buffer.has_stream('time_sync'):
            temp = self.buffer.consume_N('time_sync',sys.maxsize)
            pd.DataFrame.from_dict(temp).to_hdf(fname + '.h5', key='time_sync')
        if self.buffer.has_stream('external_signal'):
            temp = self.buffer.consume_N('external_signal',sys.maxsize)

            # Change external_signal_change_type type into list
            temp['change_type'] = [t.name for t in temp['change_type']]

            pd.DataFrame.from_dict(temp).to_hdf(fname + '.h5', key='external_signal')
        if self.buffer.has_stream('notification'):
            '''
            your performance may suffer as PyTables will pickle object types that it cannot
            map directly to c-types [inferred_type->mixed,key->block2_values] [items->Index(['notification_type', 'display_area', 'errors_or_warnings'], dtype='object')]
            '''
            temp = self.buffer.consume_N('notification',sys.maxsize)

            # Change notification type into list
            temp['notification_type'] = [t.name for t in temp['notification_type']]

            # Change change all others to strings to prevent above warning
            # columns = ['errors_or_warnings', 'display_area', 'output_frequency']
            # df.loc[:,columns] = df[columns].applymap(str)
            temp['display_area'] = [repr(t) for t in temp['display_area']]
            temp['output_frequency'] = [repr(t) for t in temp['output_frequency']]
            temp['errors_or_warnings'] = [repr(t) for t in temp['errors_or_warnings']]

            pd.DataFrame.from_dict(temp).to_hdf(fname + '.h5', key='notification')

       # Save calibration history to HDF5 container
        df_cal = pd.DataFrame(self.calibration_history(),  columns=['offset_left_eye (deg)',
                                                                  'offset_right_eye (deg)',
                                                                  'RMS_S2S_left_eye (deg)',
                                                                  'RMS_S2S_right_eye (deg)',
                                                                  'Prop_data_loss_left_eye',
                                                                  'Prop_data_loss_right_eye',
                                                                  'SD_left_eye (deg)',
                                                                  'SD_right_eye (deg)',
                                                                  'Calibration used'])
        df_cal.to_hdf(fname + '.h5', key='calibration_history')

        # Save tracker/python version info as json
        temp = self.system_info()
        with open(fname + '.json', "w") as outfile:
            json.dump(temp, outfile)

        # Also save tracker/python version to .h5-file as attributes
        with h5py.File(fname + '.h5', 'a') as hf:
            for a in temp:
                if a in ('track_box', 'display_area'):
                    continue
                hf.attrs[a] = temp[a]

        # Save image stream in the same HDF5 container
        temp = self.buffer.consume_N('eye_image')
        if len(temp['image']) > 0:

            with h5py.File(fname + '.h5', 'a') as hf:
                grp = hf.create_group('eye_image')

                # Save each frame as a separate dataset in this group
                # To access later, use [i[:] for i in grp.values()]
                for k, im in enumerate(temp['image']):
                    grp.create_dataset(str(k), data=im)

            # # Remove the numpy image and save the rest
            del temp['image']
            temp['type'] = [t.name for t in temp['type']] # LIst of strings, e.g, "full_image", "cropped_image"
            pd.DataFrame.from_dict(temp).to_hdf(fname + '.h5', key='eye_metadata')

        # Clear data containers
        self.msg_container = []
        self.all_validation_results = []

        # Stop logging and Save data from the python wrapper
        TittaPy.stop_logging()
        l=TittaPy.get_log(True)  # True means the log is consumed. False (default) its only peeked.
        if len(l) > 0:
            d =  {}
            for key in list(l[0].keys()):
                d[key] = [i[key] for i in l]

            # Convert to prevent warning when saving to Hdf5 (see notifications above)
            d['level'] = [t.name for t in d['level']]
            d['source'] = [t.name for t in d['source']]

            # Save log file
            pd.DataFrame.from_dict(d).to_hdf(fname + '.h5', key='log')

        print(f'Took {time.time() - t0} s to save the data')





