# -*- coding: utf-8 -*-
"""
Created on Thu Jun 01 14:11:57 2017

@author: Marcus

ToDO: 
    * Integrate raw classes
    *	Align validation screen with Matlab interface
    * Select calibration with arrow keys
	* self.tracker = tr.EyeTracker(self.settings.TRACKER_ADDRESS - add better error message if this call fails
	  e.g. "Could not connect to eye tracker. Did you forget to switch is on or provide the wrong eye tracker name?
    * make sure that pressing 'r' during validation, restarts a validition when in validation mode
    (i.e., when the validation button has been pressed)
    * CHANGE NAMES TO THOSE IN SDK
"""
from __future__ import print_function # towards Python 3 compatibility

from psychopy import visual, core, event
from collections import deque
import pandas as pd
import copy
import sys

if sys.version_info[0] == 3: # if Python 3:
    from io import BytesIO as StringIO
    import pickle
else: # else Python 2
    from cStringIO import StringIO
    import cPickle as pickle

from PIL import Image
import tobii_research as tr
import numpy as np
from titta import helpers_tobii as helpers

    
#%%    
class myTobii(object):
    """
    A Class to communicate with Tobii eye trackers
    """

    def __init__(self, settings):
        '''
        Constructs an instance of the TITTA interface, with specified settings
        acquited through the call (Titta.get_defaults)
        '''        
            
        if 'Tobii Pro Spectrum' not in settings.eye_tracker_name:
            settings.RECORD_EYE_IMAGES_DURING_CALIBRATION = False

        self.settings = settings
		
        # Remove empty spaces (if any are given)
        self.settings.TRACKER_ADDRESS = self.settings.TRACKER_ADDRESS.replace(" ", "")        
        
        
    #%%  
    def init(self):
        ''' Apply settings and check capabilities
        '''        
        
        
        # If no tracker address is give, find it automatically
        k = 0
        while len(self.settings.TRACKER_ADDRESS) == 0 and k < 4:
            
            # if the tracker doesn't connect, try four times to reconnect
            ets = tr.find_all_eyetrackers()
            for et in ets:
                
                # Check that the desired eye tracker is found
                if et.model == self.settings.eye_tracker_name:
                    self.settings.TRACKER_ADDRESS = et.address
            
            k += 1
            core.wait(2)
            
            
        # If no tracker address could be set, the eye tracker was not found
        if len(self.settings.TRACKER_ADDRESS) == 0:
            
            # List available eye trackers:
            if len(ets) == 0:              
                raise Exception('No eye tracker was found')
            else:
                raise Exception('The desired eye tracker not found. \
                                These are available: ' + ' '.join([str(m.model) for m in ets]))                
      
        if self.settings.PACING_INTERVAL < 0.8:
            raise Exception('Calibration pacing interval must be \
                            larger than 0.8 s') 

        # Store recorded data in lists
        self.gaze_data_container = []
        self.msg_container = []
        self.sync_data_container = []
        self.image_data_container = []
        self.external_signal_container = []
        self.stream_errors_container = []
        
        self.user_position_guide_data = None
        
        self.all_validation_results = []

        # When recording, store data or just it online without storing
        self.store_data = False
        
        self.clock = core.Clock()
               
        # header / column names
        self.header = ['device_time_stamp',
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
         
        self.old_timestamp = 0
        
        # Placeholder for eye images
        self.eye_image = deque(maxlen=2) # To store the most recent eye images
                                            # for the left and right eyes
        self.image_type = None
        self.eye_image_write = False


        # Internal variable to keep track of whether samples 
        # are put into the buffer or not
        self.__buffer_active = False 
        self.buf = []        
        
        # Initiate direct access to barebone SDK functionallity
        self.rawTracker = rawTracker(self.settings.TRACKER_ADDRESS)
        self.tracker = self.rawTracker.tracker        
                
        # set sampling frequency
        Fs = self.get_sample_rate()
        if Fs != self.settings.SAMPLING_RATE:
            self.set_sample_rate(self.settings.SAMPLING_RATE)
            
        # Assert that the selected tracking mode is supported
        assert np.any([tracking_mode == self.settings.TRACKING_MODE \
                        for tracking_mode in self.tracker.get_all_eye_tracking_modes()]), \
            "The given tracking mode is not supported. \
            Supported are: {}".format(self.tracker.get_all_eye_tracking_modes())
            
        try:
            print('Current tracking mode: {}'.format(self.tracker.get_eye_tracking_mode()))
            self.tracker.set_eye_tracking_mode(self.settings.TRACKING_MODE)
        except NameError:
            print('Tracking mode not found: {}'.format(self.settings.TRACKING_MODE))
        
        
           #%% 
    def _create_calibration_buttons(self):
        '''Creates click buttons that are used during calibration
        If another window object, win_operator, is given, the experiment 
        will be run in dual screen mode.
        
        '''
        
        # Find out ratio aspect of the stimulus screen (16:10) or 
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
        self.cal_dot = helpers.MyDot2(self.win, units='deg',
                                     outer_diameter=self.settings.graphics.TARGET_SIZE, 
                                     inner_diameter=self.settings.graphics.TARGET_SIZE_INNER)
        
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
        self.setup_dot = helpers.MyDot2(self.win, units='height',
                                     outer_diameter=self.settings.graphics.SETUP_DOT_OUTER_DIAMETER, 
                                     inner_diameter=self.settings.graphics.SETUP_DOT_INNER_DIAMETER)        
              
                                         
        # Dot for showing et data
        self.et_sample_l = visual.Circle(self.win_temp, radius = self.settings.graphics.ET_SAMPLE_RADIUS, 
                                         fillColor = 'red', units='deg') 
        self.et_sample_r = visual.Circle(self.win_temp, radius = self.settings.graphics.ET_SAMPLE_RADIUS, 
                                         fillColor = 'blue', units='deg')   
        # self.et_line_l = visual.Line(self.win_temp, lineColor = 'red', units='deg', lineWidth=0.4)
        # self.et_line_r = visual.Line(self.win_temp, lineColor = 'blue', units='deg', lineWidth=0.4)
        
        if self.win_operator:
            self.raw_et_sample_l = visual.Circle(self.win_temp, radius = 0.01, 
                                             fillColor = 'red', units='norm') 
            self.raw_et_sample_r = visual.Circle(self.win_temp, radius = 0.01, 
                                             fillColor = 'blue', units='norm')     
            self.current_point = helpers.MyDot2(self.win_temp, units='norm',
                                         outer_diameter=0.05, 
                                         inner_diameter=0.02)            
            
        
      
        # Show images (eye image, validation resutls)
        self.eye_image_stim_l = visual.ImageStim(self.win_temp, units='norm',
                                                   size=self.settings.graphics.EYE_IMAGE_SIZE,
                                                   pos=self.settings.graphics.EYE_IMAGE_POS_L, 
                                                   image=np.zeros((512, 512)))
        self.eye_image_stim_r = visual.ImageStim(self.win_temp, units='norm',
                                                   size=self.settings.graphics.EYE_IMAGE_SIZE,
                                                   pos=self.settings.graphics.EYE_IMAGE_POS_R,
                                                   image=np.zeros((512, 512)))
      
        # Accuracy image 
        self.accuracy_image = visual.ImageStim(self.win_temp, image=None,units='norm', size=(2,2),
                                          pos=(0, 0))
        
    
    #%%
    def is_connected(self):
        pass
        
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
        if self.settings.eye_tracker_name != 'Tobii Pro Spectrum':
            assert eye=='both', 'Monocular calibrations available only in Tobii Pro Spectrum'
            
        # Generate coordinates for calibration in PsychoPy and 
        # Tobii coordinate system
        CAL_POS_DEG = helpers.tobii2deg(self.settings.CAL_POS_TOBII, win.monitor)
        VAL_POS_DEG = helpers.tobii2deg(self.settings.VAL_POS_TOBII, win.monitor)
        self.CAL_POS = np.hstack((self.settings.CAL_POS_TOBII, CAL_POS_DEG))
        self.VAL_POS = np.hstack((self.settings.VAL_POS_TOBII, VAL_POS_DEG))        
            
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
            
            # Define your calibration target
            target = helpers.MyDot2(self.win, units='deg',
                                     outer_diameter=self.settings.graphics.TARGET_SIZE, 
                                     inner_diameter=self.settings.graphics.TARGET_SIZE_INNER)  
            self.animator = helpers.AnimatedCalibrationDisplay(self.win, target, 'animate_point')        
        
        # Screen based calibration 
        if self.settings.eye_tracker_name == 'Tobii Pro Spectrum':
            self.calibration = tr.ScreenBasedMonocularCalibration(self.tracker)        
            if 'both' in eye:
    #            self.calibration = tr.ScreenBasedCalibration(self.tracker)
                self.eye_to_calibrate = tr.SELECTED_EYE_BOTH
            elif 'left' in eye:
                self.eye_to_calibrate = tr.SELECTED_EYE_LEFT
            else:
                self.eye_to_calibrate = tr.SELECTED_EYE_RIGHT
        else:
            self.calibration = tr.ScreenBasedCalibration(self.tracker)        

        # Main control loop
        action = 'setup'
        self.deviations = [] # List to store validation accuracies
        self.start_recording(store_data=False, 
                             gaze_data=True,
                             sync_data=True)
        
        # Enter calibration mode if binocular calibration or if first 
        # bi-monocular calibration
        if self.eye == 'both' or self.calibration_number == 'first':
            self.calibration.enter_calibration_mode()                
        
        while True:
            self.action = action
            print(action)
            if 'setup' in action:
                action = self._check_head_position()
            elif 'cal' in action:   
                
                # Default to last calibration when a new 
                # Calibration is run
                self.selected_calibration = len(self.deviations) + 1                                        
                action = self._run_calibration()
            elif 'val' in action:
                action = self._run_validation()
            elif 'res' in action:
                action = self._show_validation_screen()                
            elif 'done'in action:
                print('calibration completed')
                break
            elif 'quit' in action:
                self.calibration.leave_calibration_mode() 
                self.stop_recording(gaze_data=True,
                            sync_data=True)
                self.win.close()
                if self.win_operator:
                    self.win_operator.close()
                core.quit()
            else:
                pass
            
            
            core.wait(0.1)
    
        # Leave calibration mode if binocular calibration or if second 
        # bi-monocular calibration
        if self.eye == 'both' or self.calibration_number == 'second':
            self.calibration.leave_calibration_mode()          
        
        self.stop_recording(gaze_data=True,
                            sync_data=True)
            
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
        
        d = self.get_latest_sample()
        lx = d['left_gaze_point_on_display_area'][0] 
        ly = d['left_gaze_point_on_display_area'][1] 
        rx = d['right_gaze_point_on_display_area'][0] 
        ry = d['right_gaze_point_on_display_area'][1]
        
            
#        if self.eye == 'left' or self.eye == 'both':
        self.et_sample_l.pos = helpers.tobii2deg(np.array([[lx, ly]]), 
                                                 self.win_temp.monitor)       
        self.et_sample_l.draw()
            
#        if self.eye == 'right' or self.eye == 'both':
        self.et_sample_r.pos = helpers.tobii2deg(np.array([[rx, ry]]), 
                                                 self.win_temp.monitor)
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
        
        self.mouse.setVisible(1)
        
        self.store_data = False
        
        # Start streaming of eye images
        if self.settings.eye_tracker_name == 'Tobii Pro Spectrum':
            self.start_recording(image_data=True, store_data = self.store_data)
            
            
        # Start user positioning guide
        self.start_recording(user_position_guide=True, store_data = self.store_data)

        core.wait(0.5)
        
        if not self.get_latest_sample():
            self.win.close()
            raise ValueError('Eye tracker switched on?')
            
            
        # Initiate parameters of head class (shown on participant screen)
        et_head = helpers.EThead(self.win)
        latest_valid_yaw = 0 
        latest_valid_roll = 0
        previous_binocular_sample_valid = True
        latest_valid_bincular_avg = np.array([0.5, 0.5, 0.5])
        offset = np.array([0, 0, 0])
        
        # Initiate parameters of head class (shown on operator screen)        
        if self.win_operator:
            et_head_op = helpers.EThead(self.win_temp)      
            
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
                
            # Draw setup button information  and check whether is was selected
            if self.settings.eye_tracker_name == 'Tobii Pro Spectrum':
                self.setup_button.draw()
                self.setup_button_text.draw()            
                if self.settings.graphics.SETUP_BUTTON in k or (self.mouse.isPressedIn(self.setup_button, buttons=[0]) and not image_button_pressed):
                    # Toggle visibility of eye images
                    show_eye_images = not show_eye_images
                    image_button_pressed = True
                             
             # Get position of eyes in track box
            sample = self.get_latest_sample()
            sample_user_position = self.get_latest_user_position_guide_sample()
            
            # Draw et head on participant screen
            latest_valid_bincular_avg, \
            previous_binocular_sample_valid,\
            latest_valid_yaw, \
            latest_valid_roll, \
            offset = et_head.update(sample,
                                    sample_user_position,
                                    latest_valid_bincular_avg,    
                                    previous_binocular_sample_valid,
                                    latest_valid_yaw, 
                                    latest_valid_roll, 
                                    offset, eye=self.eye)         
            et_head.draw()       
            
            # Draw et head on operator screen
            if self.win_operator:            
                latest_valid_bincular_avg, \
                previous_binocular_sample_valid,\
                latest_valid_yaw, \
                latest_valid_roll, \
                offset = et_head_op.update(sample,
                                           sample_user_position,
                                           latest_valid_bincular_avg,    
                                           previous_binocular_sample_valid,
                                           latest_valid_yaw, 
                                           latest_valid_roll, 
                                           offset, eye=self.eye)         
                et_head_op.draw()              
                        
            # Draw instruction
            self.instruction_text.pos = (0, 0.8)
            self.instruction_text.text = 'Position yourself such that the two circles overlap.'
            self.instruction_text.draw()
            
            # Get and draw distance information
            l_pos = self.get_latest_sample()['left_gaze_origin_in_user_coordinate_system'][2]
            r_pos = self.get_latest_sample()['right_gaze_origin_in_user_coordinate_system'][2]
             
            
            try:
                self.instruction_text_op.pos = (0, 0.9)
                self.instruction_text_op.text = ' '.join(['Distance:', 
                                                           str(int(np.nanmean([l_pos, r_pos])/10.0)), 'cm'])
                self.instruction_text_op.draw() 
            except:
                pass
            
            # Show eye images if requested
            if show_eye_images:
                self._draw_eye_image()  
                
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

        # Stop streaming of eye images
        if self.settings.eye_tracker_name == 'Tobii Pro Spectrum':
            self.stop_recording(image_data=True)   
        self.mouse.setVisible(0)
        
        # Stop user position guide
        self.stop_recording(user_position_guide=True)
        
        # Clear the screen
        self.win.flip()
        if self.win_operator:            
            self.win_temp.flip()        
        
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
        self.current_point.pos = helpers.tobii2norm(np.expand_dims(pos, axis=0))
        self.current_point.draw()
        
        # Draw data for the left and right eyes
        self.raw_et_sample_l.pos = helpers.tobii2norm(np.expand_dims(sample['left_gaze_point_on_display_area'], axis=0))
        self.raw_et_sample_r.pos = helpers.tobii2norm(np.expand_dims(sample['right_gaze_point_on_display_area'], axis=0))
        self.raw_et_sample_l.draw()
        self.raw_et_sample_r.draw()
        
        # Draw eye images for the left and right eyes        
        self._draw_eye_image() 
        
        
        
        

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
            
        self.store_data = True
        
        cal_pos=self.CAL_POS
        paval=self.settings.PACING_INTERVAL
        
        # Optional start recording of eye images
        if self.settings.RECORD_EYE_IMAGES_DURING_CALIBRATION or self.win_operator:
            self.start_recording(image_data=True)            
        
        np.random.shuffle(cal_pos)
                
        core.wait(0.5)     
        self.send_message('Calibration_start')

        
        action = 'setup'
        
        # Go through the targets one by one
        t0 = self.clock.getTime()
        i = 0
        pos_old = [0, 0]
        calibration_done = False
        animation_state = 'static'
        tick = 0
        autopace = self.settings.AUTO_PACE
        while not calibration_done:
            
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
                    self.animator.animate_target(0, (pos[0], pos[1]), tick)
            else:
                self.cal_dot.set_pos(pos)
                self.cal_dot.draw()    
                
            if self.win_operator:
                self._draw_operator_screen(tobii_data, self.get_latest_sample())
                self.win_temp.flip()
                
            self.win.flip()
            
            # Send a message at the onset (first frame) of a new dot
            # Always happens when tick == 0
            if tick == 0 and animation_state == 'static':
                self.send_message('calibration point {} at position {} {}'.format(i, pos[0], pos[1]))                
            
            # Time to switch to a new point
            if autopace == 2 or 'space' in k:
                
                # Switch to fully automatic pacing once first point is accepted
                autopace = 2
                
                if (self.clock.getTime() - t0) > paval:
                    
                    pos_old = pos[:]
                    i += 1
                    
                    # Collect some calibration data
                    if self.settings.eye_tracker_name == 'Tobii Pro Spectrum':
                        if self.eye == 'left':
                            if self.calibration.collect_data(tobii_data[0], tobii_data[1], self.eye_to_calibrate) != tr.CALIBRATION_STATUS_SUCCESS_LEFT_EYE:
                                self.calibration.collect_data(tobii_data[0], tobii_data[1], self.eye_to_calibrate)
                        elif self.eye == 'right':
                            if self.calibration.collect_data(tobii_data[0], tobii_data[1], self.eye_to_calibrate) != tr.CALIBRATION_STATUS_SUCCESS_RIGHT_EYE:
                                self.calibration.collect_data(tobii_data[0], tobii_data[1], self.eye_to_calibrate)
                        else:
                            if self.calibration.collect_data(tobii_data[0], tobii_data[1], self.eye_to_calibrate) != tr.CALIBRATION_STATUS_SUCCESS:
                                self.calibration.collect_data(tobii_data[0], tobii_data[1], self.eye_to_calibrate)  
                    else:
                        if self.calibration.collect_data(tobii_data[0], tobii_data[1]) != tr.CALIBRATION_STATUS_SUCCESS:
                            self.calibration.collect_data(tobii_data[0], tobii_data[1])           
                            
                    if i == 5:
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

        # Apply the calibration and get the calibration results
        calibration_result = self.calibration.compute_and_apply()
        self.calibration_results = calibration_result
        print("Compute and apply returned {0} and collected at {1} points.".
              format(calibration_result.status, len(calibration_result.calibration_points)))       
        

        
        # Accept of redo the calibration?
        if 'success' in calibration_result.status:   
            action = 'val'
            if 'Tobii Pro Spectrum' in self.settings.eye_tracker_name:
                print(self.eye, self.eye_to_calibrate)

            cal_data = self._generate_calibration_image(calibration_result)
#                pos, xy_pos = self.run_validation()                 
#                self.generate_validation_image(pos, xy_pos)
#                self.win.flip()
#                event.waitKeys()  
#                calibration_completed = True
        else:
            self.instruction_text.text = 'Calibration unsuccessful.'
            self.instruction_text.draw()
            self.win.flip()
            core.wait(1) 

#        self.calibration.leave_calibration_mode()            
        self.send_message('Calibration_stop')
        
        # Stop recording of eye images unless validation is next      
        if 'val' not in action:
            if self.settings.RECORD_EYE_IMAGES_DURING_CALIBRATION or self.win_operator:
                self.stop_recording(image_data=True)     
     
        return action

  
    #%%
    def _generate_calibration_image(self, calibration_result):
        ''' Generates visual representation of calibration results
        '''        
        
        cal_data = []   # where calibration deviations are stored
        xys_left = []   # container for gaze data (left eye)
        xys_right = []  # container for gaze data (right eye)
                
        # Display the results to the user (loop over each calibration point)
        for p in calibration_result.calibration_points:
            
            # Draw calibration dots
            x_dot = p.position_on_display_area[0]
            y_dot = p.position_on_display_area[1]
            self.cal_dot.fillColor = 'white'
            xy_dot = helpers.tobii2deg(np.array([[x_dot, y_dot]]), 
                                       self.win.monitor)
            self.cal_dot.set_pos(xy_dot) # Tobii and psychopy have different coord systems            
            self.cal_dot.draw()
                        
            if self.eye == 'both' or self.eye == 'left':
                # Save gaze data for left eye to list
                for si in p.calibration_samples: # For each sample
                    samples_l = si.left_eye.position_on_display_area
                    x, y = samples_l
                    xy_sample = helpers.tobii2deg(np.array([[x, y]]), 
                                                  self.win.monitor) # Tobii and psychopy have different coord systems
                    xys_left.append([xy_sample[0][0], xy_sample[0][1]])
                    cal_data.append([x_dot, y_dot, x, y, 'left'])
                    
            if self.eye == 'both' or self.eye == 'right':                   
                # Save gaze data for right eye to list
                for si in p.calibration_samples:
                    samples_r = si.right_eye.position_on_display_area
                    x, y = samples_r
                    xy_sample = helpers.tobii2deg(np.array([[x, y]]), 
                                                  self.win.monitor) # Tobii and psychopy have different coord systems
                    xys_right.append([xy_sample[0][0], xy_sample[0][1]])                  
                    cal_data.append([x_dot, y_dot, x, y, 'right'])
                    
        samples = visual.ElementArrayStim(self.win, 
                                          sizes=0.1, 
                                          fieldSize=(5, 5),
                                          nElements=np.max([len(xys_left),
                                                            len(xys_right)]),
                                          elementTex=None, 
                                          elementMask='circle', 
                                          units='deg')
        
        # Draw calibration gaze data samples for left eye and right eyes
        if self.eye == 'both' or self.eye == 'left':
            samples.xys = np.array(xys_left)
            samples.colors = (1, 0, 0)        
            samples.draw()
        
        if self.eye == 'both' or self.eye == 'right':            
            samples.xys = np.array(xys_right)
            samples.colors = (0, 0, 1)        
            samples.draw()        
                        
        # Save validation results as image
        # nCalibrations = len(self.deviations) + 1
        fname = 'calibration_image' + str(self.selected_calibration)+'.png'
        self.win.getMovieFrame(buffer='back')
        self.win.saveMovieFrames(fname)

        # Clear the back buffer without flipping the window
        self.win.clearBuffer() 
                
        return cal_data

    #%%        
    def save_calibration(self, filename):
        ''' Save the calibration to a .bin file
        Args:
            filename: test
        Returns:
            -
        '''
        with open(filename + '.bin', "wb") as f:
            calibration_data = self.tracker.retrieve_calibration_data()

            # None is returned on empty calibration.
            if calibration_data is not None:
                print("Saving calibration to file {} for eye tracker with serial number {}.".format(filename, self.tracker.serial_number))
                f.write(self.tracker.retrieve_calibration_data())
            else:
                print("No calibration available for eye tracker with serial number {0}.".format(self.tracker.serial_number))
    #%%        
    def load_calibration(self, filename):
        ''' Loads the calibration to a .bin file
        Args:
            filename: test
        Returns:
            -
        '''
        # Read the calibration from file.
        with open(filename+'.bin', "rb") as f:
            calibration_data = f.read()
            
        # Don't apply empty calibrations.
        if len(calibration_data) > 0:
            print("Applying calibration {} on eye tracker with serial number {}.".format(filename, self.tracker.serial_number))
            self.tracker.apply_calibration_data(calibration_data)
            
        
    #%%   
    def _run_validation(self):
        ''' Runs a validation to check the accuracy of the calibration
        '''
        
                
        target_pos = self.VAL_POS
        paval = self.settings.PACING_INTERVAL
        
        np.random.shuffle(target_pos)
        
        # Set this to true if you want all data from the validation to 
        # end up in the main data file (default, False)
        self.store_data = True
        self.send_message('Validation_start')
        
        action = 'setup'
        # Go through the targets one by one
        self.clock.reset()
        i = 0
        pos_old = self.final_cal_position
        validation_done = False
        validation_data = []
        xy_pos = []
        animation_state = 'move'
        buffer_started = False
        tick = 0
        while not validation_done:
            
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
                    self.animator.animate_target(0, (pos[0], pos[1]), tick)
            else:
                animation_state == 'static'
                self.cal_dot.set_pos(pos)
                self.cal_dot.draw()    
                
            if self.win_operator:
                self._draw_operator_screen(target_pos[i, :2], self.get_latest_sample())
                self.win_temp.flip()                
                
            self.win.flip()
            
            # Send a message at the onset (first frame) of a new dot
            # Always happens when tick == 0
            # animation_state 'static' means that the dot has completed the 
            # movement to a new location.
            if tick == 0 and animation_state == 'static':
                self.send_message('validation point {} at position {} {}'.format(i, pos[0], pos[1]))  
                
            # Start collecting validation data for a point 500 ms after its onset
            if (self.clock.getTime() >= 0.500 and self.clock.getTime() < 0.800) and not buffer_started:
                self.start_sample_buffer(sample_buffer_length=300)
                buffer_started = True
                
            if self.clock.getTime() >= 0.800 and buffer_started:           
                sample = self.consume_buffer()
                self.stop_sample_buffer()
                buffer_started = False
            
            # Time to switch to a new point 
            if self.settings.AUTO_PACE > 0 or 'space' in k:
                if self.clock.getTime() > paval:
                    
                    # Collect validation data from this point
                    validation_data.append(sample)
                    
                    # Save data as xy list
                    for s in sample:
                        xy_pos.append([s['system_time_stamp'], 
                                       s['left_gaze_point_on_display_area'][0], 
                                       s['left_gaze_point_on_display_area'][1], 
                                       s['right_gaze_point_on_display_area'][0], 
                                       s['right_gaze_point_on_display_area'][1], 
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
        gaze_pos[:, 1:3] = helpers.tobii2deg(gaze_pos[:, 1:3], self.win.monitor)
        gaze_pos[:, 3:5] = helpers.tobii2deg(gaze_pos[:, 3:5], self.win.monitor)
        
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
            
        
        data_quality_values = [np.nanmean(deviation_l), np.nanmean(deviation_r),
                                np.nanmean(rms_l), np.nanmean(rms_r),
                                np.nanmean(sd_l), np.nanmean(sd_r),
                                np.nanmean(data_loss_l), np.nanmean(data_loss_r)]
        
        self.deviations.insert(self.selected_calibration - 1,
                               data_quality_values)
            
        self.send_message('validation data quality Dev_L: {:.2f}, Dev_R: {:.2f} RMS_L: {:.2f}, RMS_R: {:.2f}, SD_L: {:.2f}, SD_R: {:.2f}, LOSS_L: {:.2f}, LOSS_R: {:.2f}' \
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
        if self.settings.RECORD_EYE_IMAGES_DURING_CALIBRATION:
            self.stop_recording(image_data=True) 
                    
        self.store_data = False
#        
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
                                          sizes=0.1, 
                                          fieldSize = (5, 5),  #self.settings.SAMPLE_DOT_SIZE,
                                          nElements = gaze_positions.shape[0],
                                          elementTex=None, elementMask='circle', units='deg')
        core.wait(0.1)
        
        # Show all dots...
        for p in dot_positions:
            self.cal_dot.set_pos(p )
            self.cal_dot.draw()
        
        #... and collected validation samples for left...
        if self.eye == 'both' or self.eye == 'left':
            samples.xys = gaze_positions[:, 1:3]
            samples.colors = (1, 0, 0)        
            samples.draw()

        #... and right eye
        if self.eye == 'both' or self.eye == 'right':        
            samples.xys = gaze_positions[:, 3:5]
            samples.colors = (0, 0, 1)        
            samples.draw()       

        # Save validation results as image
        # nCalibrations = len(self.deviations)
        fname = 'validation_image' + str(self.selected_calibration) + '.png'
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
        
        display_area = self.tracker.get_display_area()
        
#        print("Bottom Left: {0}".format(display_area.bottom_left))
#        print("Bottom Right: {0}".format(display_area.bottom_right))
#        print("Height: {0}".format(display_area.height))
#        print("Top Left: {0}".format(display_area.top_left))
#        print("Top Right: {0}".format(display_area.top_right))
#        print("Width: {0}".format(display_area.width)) 
        
        dx = (np.array(display_area.top_right) - np.array(display_area.top_left)) * v[0]
        dy = (np.array(display_area.bottom_left) - np.array(display_area.top_left)) * v[1]
        
        u = np.array(display_area.top_left) + dx + dy    

        return u
    #%% 
    def _compute_data_quality(self, validation_data, val_point_positions, eye):
        ''' Computes data quality (deviation, rms) per validation point
        
        Args:
            validation_data - list with validation data per point
                validation_data[k] - dict with keys (see self.header)
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
            
            # For each sample
            deviation_per_sample = []
            angle_between_samples = []
            gaze_vector_old = 0
            n_invalid_samples = 0
            for i, sample in enumerate(point_data):
                
                gaze_vector = (sample[eye + '_gaze_point_in_user_coordinate_system'][0] - 
                               sample[eye + '_gaze_origin_in_user_coordinate_system'][0],
                               sample[eye + '_gaze_point_in_user_coordinate_system'][1] - 
                               sample[eye + '_gaze_origin_in_user_coordinate_system'][1],
                               sample[eye + '_gaze_point_in_user_coordinate_system'][2] - 
                               sample[eye + '_gaze_origin_in_user_coordinate_system'][2]) 
                
                if np.any(np.isnan(gaze_vector)):
                    n_invalid_samples += 1
                
                eye_to_valpoint_vector = (val_point_position[0] - 
                               sample[eye + '_gaze_origin_in_user_coordinate_system'][0],
                               val_point_position[1] - 
                               sample[eye + '_gaze_origin_in_user_coordinate_system'][1],
                               val_point_position[2] - 
                               sample[eye + '_gaze_origin_in_user_coordinate_system'][2])  
                
                # Compute RMS (diff between consecutive samples) and deviation
                deviation_per_sample.append(helpers.angle_between(gaze_vector, eye_to_valpoint_vector))
                if i > 0:
                    angle_between_samples.append(helpers.angle_between(gaze_vector, gaze_vector_old))

                gaze_vector_old = gaze_vector
                
            # Compute averages per point
            deviation_per_point.append(np.rad2deg(np.nanmedian(deviation_per_sample)))
            rms_per_point.append(np.rad2deg(helpers.rms(angle_between_samples)))
            sd_per_point.append(np.rad2deg(helpers.sd(angle_between_samples)))
            data_loss_point.append(n_invalid_samples / float(i))
            
        return deviation_per_point, rms_per_point, sd_per_point, data_loss_point
                            
            
    #%%     
    def _show_validation_screen(self):
        ''' Shows validation image after a validation has been completed
        '''    
        # Center position of presented calibration values
        x_pos_res = 0.55
        y_pos_res = 0.2
        
        self.mouse.setVisible(1)
        
        # We do not want to save any data here    
        self.store_data = False

        # get (and save) validation screen image
        nCalibrations = len(self.deviations)
        self.save_calibration(str(nCalibrations))
        core.wait(0.2)
        
        # Add image as texture
        fname = 'validation_image' + str(self.selected_calibration)+'.png'        
        self.accuracy_image.image = fname
        show_validation_image = True    # Default is to show validation results, 
                                        # not calibration results
        
        # information about data quality header
        header = ['Quality (deg)', 'L', 'R', 'L_rms', 'R_rms']
        x_pos= np.linspace(-0.30, 0.30, num = 5)        
        
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
                    accuracy_values_j.append(visual.TextStim(self.win_temp,
                                                        text='{0:.2f}'.format(self.deviations[i][j - 1]),
                                                        wrapWidth = 1,
                                                        height = self.settings.graphics.TEXT_SIZE, 
                                                        units='norm',
                                                        color = self.settings.graphics.TEXT_COLOR,
                                                        pos = (x, y_pos)))                
                else:
                    accuracy_values_j.append(visual.TextStim(self.win_temp,
                                                        text='Cal' + str(i+1) + ':',
                                                        wrapWidth = 1,
                                                        height = self.settings.graphics.TEXT_SIZE, 
                                                        units='norm',
                                                        color = self.settings.graphics.TEXT_COLOR,
                                                        pos = (x, y_pos))) 
            accuracy_values.append(accuracy_values_j)                 
            y_pos -= 0.06
            
        
        # Prepare header
        header_text = []    
        self.instruction_text.color = (1, 1, 1) 
        y_pos = y_pos_res
        for j, x in enumerate(x_pos):
            header_text.append(visual.TextStim(self.win_temp,text=header[j],
                                                wrapWidth = 1,
                                                height = self.settings.graphics.TEXT_SIZE, 
                                                units='norm',
                                                pos = (x, y_pos_res + 0.06),
                                                color = self.settings.graphics.TEXT_COLOR))
                                                

        # Wait for user input
        selection_done = False
        display_gaze = False
        gaze_button_pressed = False
        cal_image_button_pressed = False
        timing = []
        
        # If there's an operator screen, just show a message 'please wait...'
        # on the participant screen
        if self.win_operator:
            self.instruction_text = 'Please wait...'
              
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
            
            self.calibration_image.draw()
            self.calibration_image_text.draw()             
           
            # Draw header
            [h.draw() for h in header_text]
                
            # Draw accuracy/precision values and buttons to select a calibration
            for i in range(nCalibrations):
                
                # Highlight selected calibrations
                if i == self.selected_calibration - 1: # Calibration selected
#                    select_rect_text[i].color = self.settings.graphics.blue_active
                    select_accuracy_rect[i].fillColor = self.settings.graphics.blue_active
                    if nCalibrations > 1:
                        select_accuracy_rect[i].draw() 
                        select_rect_text[i].draw()     
                else:
#                    select_rect_text[i].color = self.settings.graphics.blue
                    select_accuracy_rect[i].fillColor = self.settings.graphics.blue
                    select_accuracy_rect[i].draw() 
                    select_rect_text[i].draw()  
                    
                # Then draw the accuracy values for each calibration preceded 
                # by Cal x (the calibration number)
                
                for j, x in enumerate(x_pos): 
#                    print(i, j, accuracy_values[i][j] t, accuracy_values[i][j].pos)
                    accuracy_values[i][j].draw()                    
                    
            # Check if mouse is clicked to select a calibration
            for i, button in enumerate(select_accuracy_rect):
                if self.mouse.isPressedIn(button):
                    self.load_calibration(str(i + 1))  # Load the selected calibration
                    if show_validation_image:
                        fname = 'validation_image' + str(i + 1) + '.png'
                    else:
                        fname = 'calibration_image' + str(i + 1) + '.png'
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
                        self.load_calibration(k[0])  # Load the selected calibration
                        fname = 'validation_image' + str(k[0]) + '.png'
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
            if self.settings.graphics.CAL_IMAGE_BUTTON in k or (self.mouse.isPressedIn(self.calibration_image, buttons=[0])and not cal_image_button_pressed):
                
                # Toggle the state of the button
                show_validation_image = not show_validation_image
                
                # If validation image show, switch to calibration and vice versa
                if show_validation_image:
                    fname = 'validation_image' + str(self.selected_calibration)+'.png'
                    self.accuracy_image.image = fname                
                else:
                    fname = 'calibration_image' + str(self.selected_calibration)+'.png'
                    self.accuracy_image.image = fname                     

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
            if self.win_operator:   
                self.win_temp.flip()
        
        # Clear screen and return
        self.instruction_text.color = (1, 1, 1)
        self.win.flip()
        self.mouse.setVisible(0)

        
        return action
                
    #%%   
    def system_info(self):   
        ''' Returns information about system in dict
        '''
        
        info = {}
        info['serial_number']  = self.tracker.serial_number
        info['address']  = self.tracker.address
        info['model']  = self.tracker.model
        info['name']  = self.tracker.device_name
        info['firmware_version'] = self.tracker.firmware_version        
        info['tracking_mode']  = self.tracker.get_eye_tracking_mode()
        info['sampling_frequency']  = self.tracker.get_gaze_output_frequency()

        
        return info   
        
    #%%   
    def get_system_time_stamp(self):
        ''' Get system time stamp
        '''
        
        return tr.get_system_time_stamp()    
        
    #%% 
    def start_sample_buffer(self, sample_buffer_length=3):
        '''Starts sample buffer'''
        
        # Initialize the ring buffer
        self.buf = helpers.RingBuffer(maxlen=sample_buffer_length)
        self.__buffer_active = True
        
    #%% 
    def stop_sample_buffer(self):
        '''Stops sample buffer''' 
        self.__buffer_active = False
        
    #%%
    def consume_buffer(self):
        ''' Consume all samples and empty buffer'''
        return self.buf.get_all() 
    
    #%%
    def peek_buffer(self):
        ''' Get samples in buffer without emptying the buffer '''
        return self.buf.peek()     
        
    #%%    
    def send_message(self, msg, ts=None):
        ''' Sends a message to the data file
        '''       
        
        if not ts:
            ts = self.get_system_time_stamp()
        self.msg_container.append([ts, msg])
        
    #%%
    def get_latest_sample(self):
        ''' Gets the most recent sample 
        '''
        return self.gaze_data
    
    #%%
    def get_latest_user_position_guide_sample(self):
        ''' Gets the most recent sample 
        '''
        return self.user_position_guide_data    

    #%%            
    def start_recording(self,   gaze_data=False, 
                                sync_data=False,
                                image_data=False,
                                stream_errors=False,
                                external_signal=False,
                                user_position_guide=False,
                                store_data=True):
        ''' Starts recording 
        '''
        
        if gaze_data:
            self.subscribe_to_gaze_data()
        if sync_data:
            self.subscribe_to_time_synchronization_data()
        if image_data:
            self.subscribe_to_eye_images()
        if stream_errors:
            self.subscribe_to_stream_errors()    
        if user_position_guide:
            self.subscribe_to_user_position_guide()                
        if external_signal:
            self.subscribe_to_external_signal()   
            
        self.store_data = store_data
            
        core.wait(0.5)
    #%%    
    def stop_recording(self,    gaze_data=False, 
                                sync_data=False,
                                image_data=False,
                                stream_errors=False,
                                external_signal=False,
                                user_position_guide=False):
        ''' Stops recording
        '''        
        
        if gaze_data:
            self.usubscribe_from_gaze_data()
        if sync_data:
            self.unsubscribe_from_time_synchronization_data()
        if image_data:
            self.unsubscribe_from_eye_images()   
        if stream_errors:
            self.unsubscribe_from_stream_errors()  
        if user_position_guide:
            self.unsubscribe_from_user_position_guide()                
        if external_signal:
            self.unsubscribe_from_external_signal()   
            
        # Stop writing to file            
        self.store_data = False          
 
    #%%
    def _user_position_guide_callback(self, user_position_data):
        ''' Callback function for external signals        
        '''
        
        self.user_position_guide_data = user_position_data
        
    #%%
    def subscribe_to_user_position_guide(self):
        ''' Starts subscribing to gaze data
        '''
        self.tracker.subscribe_to(tr.EYETRACKER_USER_POSITION_GUIDE, self._user_position_guide_callback, as_dictionary=True)
        
    #%%
    def unsubscribe_from_user_position_guide(self):
        ''' Starts subscribing to gaze data
        '''
        self.tracker.unsubscribe_from(tr.EYETRACKER_USER_POSITION_GUIDE, self._user_position_guide_callback) 
        
    #%%
    def _external_signal_callback(self, callback_object):
        ''' Callback function for external signals        
        '''
        
        if self.store_data:                    
            self.external_signal_container.append(callback_object)
        
    #%%
    def subscribe_to_external_signal(self):
        ''' Starts subscribing to gaze data
        '''
        self.tracker.subscribe_to(tr.EYETRACKER_EXTERNAL_SIGNAL, self._external_signal_callback, as_dictionary=True)
        
    #%%
    def unsubscribe_from_external_signal(self):
        ''' Starts subscribing to gaze data
        '''
        self.tracker.unsubscribe_from(tr.EYETRACKER_EXTERNAL_SIGNAL, self._external_signal_callback) 
        
    #%%
    def _gaze_data_callback(self, callback_object):
        '''
        Callback function for gaze data
        Contineously pulls the state of the eye tracker
        that is, the same sample may be return multiple times
        
        '''
        self.gaze_data = callback_object
        
        if self.__buffer_active:
            self.buf.append(callback_object)
            
        time_stamp = int(callback_object['device_time_stamp'])
        if time_stamp == self.old_timestamp:
            print('no new sample generated')
            return
        else:
            if self.store_data:
                gdata = (callback_object['device_time_stamp'],
                         callback_object['system_time_stamp'],
                         callback_object['left_gaze_point_on_display_area'][0],
                         callback_object['left_gaze_point_on_display_area'][1],
                         callback_object['left_gaze_point_in_user_coordinate_system'][0],
                         callback_object['left_gaze_point_in_user_coordinate_system'][1],
                         callback_object['left_gaze_point_in_user_coordinate_system'][2],                     
                         callback_object['left_gaze_origin_in_trackbox_coordinate_system'][0],
                         callback_object['left_gaze_origin_in_trackbox_coordinate_system'][1],
                         callback_object['left_gaze_origin_in_trackbox_coordinate_system'][2],                
                         callback_object['left_gaze_origin_in_user_coordinate_system'][0],
                         callback_object['left_gaze_origin_in_user_coordinate_system'][1],
                         callback_object['left_gaze_origin_in_user_coordinate_system'][2],                     
                         callback_object['left_pupil_diameter'],
                         callback_object['left_pupil_validity'],
                         callback_object['left_gaze_origin_validity'],
                         callback_object['left_gaze_point_validity'],
                         callback_object['right_gaze_point_on_display_area'][0],
                         callback_object['right_gaze_point_on_display_area'][1],
                         callback_object['right_gaze_point_in_user_coordinate_system'][0],
                         callback_object['right_gaze_point_in_user_coordinate_system'][1],
                         callback_object['right_gaze_point_in_user_coordinate_system'][2],                     
                         callback_object['right_gaze_origin_in_trackbox_coordinate_system'][0],
                         callback_object['right_gaze_origin_in_trackbox_coordinate_system'][1],
                         callback_object['right_gaze_origin_in_trackbox_coordinate_system'][2],                
                         callback_object['right_gaze_origin_in_user_coordinate_system'][0],
                         callback_object['right_gaze_origin_in_user_coordinate_system'][1],
                         callback_object['right_gaze_origin_in_user_coordinate_system'][2],                     
                         callback_object['right_pupil_diameter'],
                         callback_object['right_pupil_validity'],
                         callback_object['right_gaze_origin_validity'],
                         callback_object['right_gaze_point_validity'])   
        
                self.gaze_data_container.append(gdata)

        self.old_timestamp = time_stamp        
    #%%
    def subscribe_to_gaze_data(self):
        ''' Starts subscribing to gaze data
        '''
        self.tracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, self._gaze_data_callback, as_dictionary=True)
        
    #%%
    def usubscribe_from_gaze_data(self):
        ''' Starts subscribing to gaze data
        '''
        self.tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self._gaze_data_callback)

        
   
    #%%    
    def get_eye_image(self, im_info):
        ''' Converts an eye image returned from the Tobii SDK to
        a numpy array
        
        Args:
            im_info - dict with info about image as returned by the SDK
            
        Returns:
            nparr
            
        '''
    
#        print("System time: {0}, Device time {1}, Camera id {2}".format(self.eye_image['system_time_stamp'],
#                                                                         self.eye_image['device_time_stamp'],
#                                                                         self.eye_image['camera_id']))
#        im_info = self.eye_image
    
        #image = PhotoImage(data=base64.standard_b64encode(self.eye_image['image_data']))
        #print(self.eye_image)
        temp_im = StringIO(im_info['image_data'])
        tim = Image.open(temp_im)
        nparr = np.array(list(tim.getdata()))

        #tim.save("temp.gif","GIF")
        
        # Full frame or zoomed in image
        if im_info['image_type'] == 'eye_image_type_full':
            eye_image_size = self.settings.graphics.EYE_IMAGE_SIZE_PIX_FULL_FRAME
            #tim.save("temp_full.gif","GIF")
        elif im_info['image_type'] == 'eye_image_type_cropped':
            eye_image_size = self.settings.graphics.EYE_IMAGE_SIZE_PIX
            #tim.save("temp_small.gif","GIF")
        else:
            eye_image_size = [512, 512]
            nparr_t = np.zeros((512* 512))
            nparr_t[:len(nparr)] = nparr
            nparr = nparr_t.copy()
            #tim.save("temp_unknown.gif","GIF")
            
            

        #print(len(nparr))
        nparr = np.reshape(nparr, eye_image_size)
        nparr = np.rot90(nparr, k = 2)
        nparr = (nparr / float(nparr.max()) * 2.0) - 1
#        
#        # Fit image to a 1024x1024s container (must be power of 2)
#        im_sz = 1024
#            
#        # Scale the eye image
#        im_final = np.zeros([im_sz, im_sz])
#        row_idx = (im_sz - eye_image_size[0]) / 2
#        col_idx = (im_sz - eye_image_size[1]) / 2
#        im_final[int(row_idx):int(row_idx+eye_image_size[0]),
#                 int(col_idx):int(col_idx+eye_image_size[1])] = np.rot90(nparr, 2)      
        
        #print(im_final.flatten().min(), im_final.flatten().max())
      
        return nparr
    #%%     
    def _advanced_setup(self):
        ''' Shows eye image and tracking monitor
        Good if you're having problems in the circle setup, 
        and want to see what's wrong.
        
        '''
        
        # This text object is used to show distance information
        self.instruction_text.pos = (0, 0.7)

        print('advanced mode')
        self.mouse.setVisible(1)
   
        action = 'setup'
        
        self.start_recording(image_data=True, store_data = False)
        
        dist = 0
        done = False

        while not done:  
                
                
            # Draw eye image
            self._draw_eye_image()                 
                                   
            # Draw buttons
            self.back_button.draw()
            self.back_button_text.draw()
            
            # Draw calibration button for all systems
            self.calibrate_button.draw()
            self.calibrate_button_text.draw()
            
            # Draw four dots in the corners
            for i in self.POS_CAL_CHECK_DOTS:
                self.setup_dot.set_pos(i)
                self.setup_dot.draw()               
            
            # Get position of each eye in track box 
            sample = self.get_latest_sample()     
            
            # Show tracking monitor 
            self._draw_tracking_monitor(sample)
            
            
            # Get eye tracker distance 
            xyz_pos_eye_l = sample['left_gaze_origin_in_user_coordinate_system']
            xyz_pos_eye_r = sample['right_gaze_origin_in_user_coordinate_system']  
            
            dist = np.nanmean([xyz_pos_eye_l[2], xyz_pos_eye_r[2]])                  
#            dist = (xyz_pos_eye_l[2] + 
#                    xyz_pos_eye_r[2]) / 2.0           
            
            # Draw distance info
            self.instruction_text.text = ' '.join(['Distance:', str(dist /10.0)[:2], 'cm'])
            self.instruction_text.draw()   
            
            # Check for keypress or mouse click to toggle visibility of pupil and CR corsshairs
            # of move on with setup
            k = event.getKeys()

            if self.settings.graphics.BACK_BUTTON in k or self.mouse.isPressedIn(self.back_button, buttons=[0]):
                action = 'setup'
                break
                
            if self.settings.graphics.CAL_BUTTON in k or self.mouse.isPressedIn(self.calibrate_button, buttons=[0]):
                action = 'cal'
                break

                
            self.win.flip()

        self.stop_recording(image_data=True)            
        self.mouse.setVisible(0)
        
        return action       
        
  
    #%%    
    def _draw_eye_image(self):
        ''' Draw left and right eye image
        '''
        
        if tr.CAPABILITY_HAS_EYE_IMAGES in self.tracker.device_capabilities:

            for i, eye_im in enumerate(list(self.eye_image)):
                im_arr = self.get_eye_image(eye_im)

                # Always display image from camera_id == 0 on left side
                if eye_im['camera_id'] == 0:
                    self.eye_image_stim_l.image = im_arr
                else:
                    self.eye_image_stim_r.image = im_arr          
                 
            self.eye_image_stim_l.draw()          
            self.eye_image_stim_r.draw()

               
    #%%    
    def _eye_image_callback(self, im):
        ''' Here eye images are accessed and optionally saved to list
        Called every time a new eye image is available.
        
        Args:
            im - dict with information about eye image
            
        '''
        
        # Make eye image dict available to rest of class
        self.eye_image.append(im)
                        
        # Store image dict in list, if self.store_data = True
        if self.store_data:
            self.image_data_container.append(im[-1])

    #%%    
    def subscribe_to_eye_images(self):
        ''' Starts sending eye images
        '''
        print('subscribe')
        self.tracker.subscribe_to(tr.EYETRACKER_EYE_IMAGES, 
                                  self._eye_image_callback,
                                  as_dictionary=True)
                
    #%%    
    def unsubscribe_from_eye_images(self):
        ''' Stops sending eye images
        '''      
#        self.eye_image_write = False
        self.tracker.unsubscribe_from(tr.EYETRACKER_EYE_IMAGES, self._eye_image_callback)
    #%%   
    def _time_sync_callback(self, time_synchronization_data):
        ''' Callback for sync data
        '''
#        print(time_synchronization_data)
        if self.store_data:
            self.sync_data_container.append(time_synchronization_data)
        
    #%%    
    def subscribe_to_time_synchronization_data(self):
        self.tracker.subscribe_to(tr.EYETRACKER_TIME_SYNCHRONIZATION_DATA,
                                  self._time_sync_callback, as_dictionary=True)
    #%%    
    def unsubscribe_from_time_synchronization_data(self):
        self.tracker.unsubscribe_from(tr.EYETRACKER_TIME_SYNCHRONIZATION_DATA)
        
    #%%   
    def _stream_errors_callback(self, stream_errors):
        ''' Callback for stream_errors
        '''
        if self.store_data:
            self.stream_errors_container.append(stream_errors)
            
    #%%    
    def subscribe_to_stream_errors(self):
        self.tracker.subscribe_to(tr.EYETRACKER_STREAM_ERRORS,
                                  self._stream_errors_callback, as_dictionary=True)
    #%%    
    def unsubscribe_from_stream_errors(self):
        self.tracker.unsubscribe_from(tr.EYETRACKER_STREAM_ERRORS)
        
    #%%      
    def set_sample_rate(self, Fs):
        '''Sets the sample rate
        '''
        
        print([i for i in self.tracker.get_all_gaze_output_frequencies()], Fs)
        assert np.any([int(i) == Fs for i in self.tracker.get_all_gaze_output_frequencies()]), "Supported frequencies are: {}".format(self.tracker.get_all_gaze_output_frequencies())
            
        self.tracker.set_gaze_output_frequency(int(Fs))
    #%%    
    def get_sample_rate(self):
        '''Gets the sample rate
        '''
        return self.tracker.get_gaze_output_frequency()

    #%%
    def save_data(self, *argv):
        ''' Saves the data to pickle
        If you want to read the pickle, see the 'resources' folder
        
        *argv refers to additional information you want to add to the same pickle
        '''
        
        # # Save gaze data. If 32 bit Python version, Pandas throws a Memory error if
        # # gaze_data_container > 2 GB. Therefore the csv-module is used instead.
        # if sys.version_info >= (3,0,0):
        #     df = pd.DataFrame(self.gaze_data_container, columns=self.header)
        #     df.to_csv(self.filename[:-4] + '.tsv', sep='\t')
        # else:        
        #     print(sys.getsizeof(self.gaze_data_container))
        #     with open(self.filename[:-4] + '.tsv', 'wb') as csv_file:
        #         csv_writer = csv.writer(csv_file, delimiter='\t')
        #         csv_writer.writerow(self.header)
        #         for row in self.gaze_data_container:
        #             csv_writer.writerow(row)          
            
        # # Save messages
        # df_msg = pd.DataFrame(self.msg_container,  columns = ['system_time_stamp', 
        #                                                       'msg'])
        # df_msg.to_csv(self.filename[:-4] + '_msg.tsv', sep='\t')            
        
        # Dump other collected information to file
        with open(self.settings.FILENAME[:-4] + '.pkl','wb') as fp:
            pickle.dump(self.gaze_data_container, fp)
            pickle.dump(self.msg_container, fp)            
            pickle.dump(self.external_signal_container, fp)
            pickle.dump(self.sync_data_container, fp)
            pickle.dump(self.stream_errors_container, fp)            
            pickle.dump(self.image_data_container, fp)
            pickle.dump(self.calibration_history(), fp)
            pickle.dump(self.system_info(), fp)
            python_version = '.'.join([str(sys.version_info[0]), 
                                  str(sys.version_info[1]),
                                  str(sys.version_info[2])])
            pickle.dump(python_version, fp)
            
            for arg in argv: 
                pickle.dump(arg, fp)

    
    #%%    
    def de_init(self):
        '''
        '''
         
    
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class rawTracker(object):
    ''' Acess Tobii SDK’s eye tracker handle to call its functions directly
    '''
        
    def __init__(self, tracker_address):    
        self.tracker = tr.EyeTracker(tracker_address)    
        
    #%% FUNCTIONS 
    def apply_calibration_data(self, data):
        ''' Sets the provided calibration data to the eye tracker, which means 
        it will be active calibration.
        
        Args: data: from eyetracker.retrieve_calibration_data()
            
        '''
        return self.tracker.apply_calibration_data(data)
    
    def apply_licenses(self, licenses):
        ''' Sets a key ring of licenses or a single license for unlocking 
        features of the eye tracker.
        Args: - 
            licenses
            
        '''
        return self.tracker.apply_licenses(licenses)
    
    def clear_applied_licenses(self):
        ''' Clears any previously applied licenses.'''
        return self.tracker.clear_applied_licenses()
    
    def get_all_eye_tracking_modes(self):
        ''' Gets a tuple of eye tracking modes supported by the eye tracker.
        Returns:
            uple of strings with available eye tracking modes.      
        '''
        return self.tracker.get_all_eye_tracking_modes
    
    def get_all_gaze_output_frequencies(self):
        ''' 
        Returns:
            Tuple of floats with all gaze output frequencies.
        '''        
        return self.tracker.get_all_gaze_output_frequencies()
    
    def get_display_area(self):
        ''' 
        Returns:
            Display area in the user coordinate system as a DisplayArea object.
            Data Fields:
                
         	bottom_left
         	Gets the bottom left corner of the active display area as a three valued tuple. 
         
         	bottom_right
         	Gets the bottom left corner of the active display area as a three valued tuple. 
         
         	height
         	Gets the height in millimeters of the active display area. 
         
         	top_left
         	Gets the top left corner of the active display area as a three valued tuple. 
         
         	top_right
         	Gets the top right corner of the active display area as a three valued tuple. 
         
         	width
         	Gets the width in millimeters of the active display area. 
            
        '''        
        return self.tracker.get_display_area()
    
    def get_eye_tracking_mode(self):
        ''' 
        Returns:
            String with the current eye tracking mode.
        '''
        
        return self.tracker.get_eye_tracking_mode()
    
    def get_gaze_output_frequency(self):
        ''' Gets the gaze output frequency of the eye tracker.
        Returns
            Float with the current gaze output frequency.
        '''
        return self.tracker.get_gaze_output_frequency()

    
    def get_track_box(self):
        ''' Gets the track box of the eye tracker.
        
        Returns
            Track box in the user coordinate system as a TrackBox object.
            
            track_box.back_lower_left
            track_box.back_lower_right
            track_box.back_upper_left
            track_box.back_upper_right
            track_box.front_lower_left
            track_box.front_lower_right
            track_box.front_upper_left
            track_box.front_upper_right
            
        '''
        
        return self.tracker.get_track_box()
    
    def retrieve_calibration_data(self):
        ''' Gets the calibration data used currently by the eye tracker.
        '''
        return self.tracker.retrieve_calibration_data()
    
    def set_device_name(self, name):
        ''' Changes the device name.

            This is not supported by all eye trackers.
        Args:
            name - str
        '''
        try:
            self.tracker.set_device_name(name)
            print("The eye tracker changed name to {0}".format(self.tracker.device_name))
        except tr.EyeTrackerFeatureNotSupportedError:
            print("This eye tracker doesn't support changing the device name.")
        except tr.EyeTrackerLicenseError:
            print("You need a higher level license to change the device name.")        
    
    def set_eye_tracking_mode(self, mode):
        '''Sets the eye tracking mode of the eye tracker.
        '''
        return self.tracker.set_eye_tracking_mode(mode)
    
    def set_gaze_output_frequency(self, Fs):
        ''' Sets the gaze output frequency of the eye tracker.
        '''
        return self.tracker.set_gaze_output_frequency(Fs)

    #%% DATA FIELDS
    
    def address(self):
        return self.tracker.address
    
    def device_capabilities(self):
        return self.tracker.device_capabilities
    
    def device_name(self):
        return self.tracker.device_name
    
    def firmware_version(self):
        return self.tracker.firmware_version
    
    def model(self):
        return self.tracker.model
    
    def serial_number(self):
        return self.tracker.serial_number
        
        
