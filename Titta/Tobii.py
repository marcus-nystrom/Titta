# -*- coding: utf-8 -*-
"""
Created on Thu Jun 01 14:11:57 2017

@author: Marcus

ToDO: 
    1) Integrate raw classes
    2) Fix lag in eye image presentation in Spectrum 
    3) Test monocular calibrations (calibration mode cannot exit until both eyes done)
        Use flags
       hide data from the eye that is not calibrated (DONE!)
    4) Implement dynamic calibration (use as default)
"""
from __future__ import print_function # towards Python 3 compatibility

from psychopy import visual, core, event
import pandas as pd
import csv
#import time
import sys

if sys.version_info[0] == 3: # if Python 3:
    from io import StringIO
    import pickle
else: # else Python 2
    from cStringIO import StringIO
    import cPickle as pickle

from PIL import Image
#import base64
import tobii_research as tr

import numpy as np
import scipy.misc
import helpers_tobii as helpers
import calibration_graphics as graphics


    
#%%    
class myTobii(object):
    """
    A Class to communicate with Tobii eye trackers
    """

    def __init__(self, in_arg):
        '''
        Constructs an instance of the TITTA interface, with specified settings. 
        If settings is not provided, the name of an eye tracker should 
        be given, e.g., Tobii4C, Spectrum.
        If an eye tracker name is given, the default values from the settings
        file (e.g., Tobii4C.py) are used.
        '''        
        # String, i.e., eye tracker name OR settings as argument?
        if isinstance(in_arg, str): # eye tracker name (use default settings)
            eye_tracker_name = in_arg
            
            # Load default setttings
            if eye_tracker_name == 'Tobii4C':
                import Tobii4C as settings
                settings.eye_tracker_name = 'Tobii4C'
            elif in_arg == 'Spectrum':
                import Spectrum as settings
                settings.eye_tracker_name = 'Spectrum'        
            else:
                print('eye tracker type not supported')
                core.quit()            
        else:                       # settings
            settings = in_arg
            eye_tracker_name = settings.eye_tracker_name
            
        if 'Spectrum' not in eye_tracker_name:
            settings.RECORD_EYE_IMAGES_DURING_CALIBRATION = False

        self.settings = settings
        self.eye_tracker_name = eye_tracker_name  
        
        # Initiate direct access to barebone SDK functionallity
        self.rawSDK = rawSDK()
        
    #%%  
    def init(self):
        ''' Apply settings and check capabilities
        '''
        
        self.filename = self.settings.FILENAME
		
        # Remove empty spaces (if any are given)
        self.settings.TRACKER_ADDRESS = self.settings.TRACKER_ADDRESS.replace(" ", "")
        
        # If no tracker address is give, find it automatically
        k = 0
        while len(self.settings.TRACKER_ADDRESS) == 0 and k < 4:
            
            # if the tracker doesn't connect, try four times to reconnect
            ets = tr.find_all_eyetrackers()
            for et in ets:
                self.settings.TRACKER_ADDRESS = et.address
            
            k += 1
            core.wait(2)
			
        # Make functions from the EyeTracker object available            
        self.tracker = tr.EyeTracker(self.settings.TRACKER_ADDRESS) # 
#        self.rawTracker = rawTracker(self.settings.TRACKER_ADDRESS)
#        print(self.rawTracker)
#        self.tracker = self.rawTracker.tracker
        
        print(self.tracker.model)
        if len(self.tracker.model) == 0:
            raise Exception('blah') 
        
        
        # Store recorded data in lists
        self.gaze_data_container = []
        self.msg_container = []
        self.sync_data_container = []
        self.image_data_container = []
        self.external_signal_container = []
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
        self.eye_image = None
        self.image_type = None
        self.eye_image_write = False


        # Internal variable to keep track of whether samples 
        # are put into the buffer or not
        self.__buffer_active = False 
        self.buf = []        
                
        # set sampling frequency
        Fs = self.get_sample_rate()
        if Fs != self.settings.SAMPLING_RATE:
            self.set_sample_rate(self.settings.SAMPLING_RATE)
        
        
           #%% 
    def _create_calibration_buttons(self, win):
        '''Creates click buttons that are used during calibration'''
        
        # Find out ratio aspect of (16:10) or 
        screen_res = win.size
        ratio = screen_res[0] / float(screen_res[1])
        
        # Shown during setup to check gaze in corners
        self.POS_CAL_CHECK_DOTS = [[-0.45 * ratio, -0.45], [0.45 * ratio, -0.45], 
                              [-0.45 * ratio, 0.45], [0.45 * ratio, 0.45]]

        # Text object to draw text (on buttons)
        instruction_text = visual.TextStim(win,text='',wrapWidth = 1,height = graphics.TEXT_SIZE, units='norm')  
        instruction_text = visual.TextStim(win,text='',wrapWidth = 1,height = graphics.TEXT_SIZE, units='norm')  
        self.instruction_text = instruction_text

        # Setup stimuli for drawing calibration / validation targets
        self.cal_dot = helpers.MyDot2(win, units='deg',
                                     outer_diameter=graphics.TARGET_SIZE, 
                                     inner_diameter=graphics.TARGET_SIZE_INNER)
        
        # Click buttons
        self.calibrate_button = visual.Rect(win, width= graphics.WIDTH_CAL_BUTTON, 
                                            height=graphics.HEIGHT_CAL_BUTTON,  
                                        units='norm', fillColor=graphics.COLOR_CAL_BUTTON,
                                        pos=graphics.POS_CAL_BUTTON)                
        self.calibrate_button_text = visual.TextStim(win, text=graphics.CAL_BUTTON_TEXT, 
                                                     height=graphics.TEXT_SIZE, units='norm',
                                                     pos=graphics.POS_CAL_BUTTON)
                                                     
        self.recalibrate_button = visual.Rect(win, width= graphics.WIDTH_RECAL_BUTTON, 
                                            height=graphics.HEIGHT_RECAL_BUTTON,  
                                        units='norm', fillColor=graphics.COLOR_RECAL_BUTTON,
                                        pos=graphics.POS_RECAL_BUTTON) 
        self.recalibrate_button_text = visual.TextStim(win, text=graphics.RECAL_BUTTON_TEXT, 
                                                     height=graphics.TEXT_SIZE, units='norm',
                                                     pos=graphics.POS_RECAL_BUTTON)                                                     
                                        
        self.setup_button = visual.Rect(win, width= graphics.WIDTH_SETUP_BUTTON, 
                                        height=graphics.HEIGHT_SETUP_BUTTON,  
                                        units='norm', fillColor=graphics.COLOR_SETUP_BUTTON,
                                        pos=graphics.POS_SETUP_BUTTON)
        self.setup_button_text = visual.TextStim(win, text=graphics.SETUP_BUTTON_TEXT, 
                                                 height=graphics.TEXT_SIZE, units='norm',
                                                 pos=graphics.POS_SETUP_BUTTON)             

        self.accept_button = visual.Rect(win, width= graphics.WIDTH_ACCEPT_BUTTON, 
                                        height=graphics.HEIGHT_ACCEPT_BUTTON,  
                                        units='norm', fillColor=graphics.COLOR_ACCEPT_BUTTON,
                                        pos=graphics.POS_ACCEPT_BUTTON)
        self.accept_button_text = visual.TextStim(win, text=graphics.ACCEPT_BUTTON_TEXT, 
                                                  height=graphics.TEXT_SIZE, units='norm',
                                                  pos=graphics.POS_ACCEPT_BUTTON)             
                                                                        
        self.back_button = visual.Rect(win, width= graphics.WIDTH_BACK_BUTTON, 
                                        height=graphics.HEIGHT_BACK_BUTTON,  
                                        units='norm', fillColor=graphics.COLOR_BACK_BUTTON,
                                        pos=graphics.POS_BACK_BUTTON)    
        self.back_button_text = visual.TextStim(win, text=graphics.BACK_BUTTON_TEXT, 
                                                height=graphics.TEXT_SIZE, units='norm',
                                                pos=graphics.POS_BACK_BUTTON)             
                                                                      
        self.gaze_button = visual.Rect(win, width= graphics.WIDTH_GAZE_BUTTON, 
                                        height=graphics.HEIGHT_GAZE_BUTTON,  
                                        units='norm', fillColor=graphics.COLOR_GAZE_BUTTON,
                                        pos=graphics.POS_GAZE_BUTTON)   
        self.gaze_button_text = visual.TextStim(win, text=graphics.GAZE_BUTTON_TEXT, 
                                                height=graphics.TEXT_SIZE, units='norm',
                                                pos=graphics.POS_GAZE_BUTTON)   

        self.calibration_image = visual.Rect(win, width= graphics.WIDTH_CAL_IMAGE_BUTTON, 
                                        height=graphics.HEIGHT_CAL_IMAGE_BUTTON,  
                                        units='norm', fillColor=graphics.COLOR_CAL_IMAGE_BUTTON,
                                        pos=graphics.POS_CAL_IMAGE_BUTTON)  
        
        self.calibration_image_text = visual.TextStim(win, text=graphics.CAL_IMAGE_BUTTON_TEXT, 
                                                height=graphics.TEXT_SIZE, units='norm',
                                                pos=graphics.POS_CAL_IMAGE_BUTTON)             
                                        
        # Dots for the setup screen
        self.setup_dot = helpers.MyDot2(win, units='height',
                                     outer_diameter=graphics.SETUP_DOT_OUTER_DIAMETER, 
                                     inner_diameter=graphics.SETUP_DOT_INNER_DIAMETER)        
        
        # Setup control circles for head position
        self.static_circ = visual.Circle(win, radius = graphics.HEAD_POS_CIRCLE_FIXED_RADIUS, 
                                         lineColor = graphics.HEAD_POS_CIRCLE_FIXED_COLOR,
                                         lineWidth=4, units='height')
        self.moving_circ = visual.Circle(win, radius = graphics.HEAD_POS_CIRCLE_MOVING_RADIUS, 
                                         lineColor = graphics.yellow_linecolor,
                                         opacity=0.5,
                                         fillColor = graphics.HEAD_POS_CIRCLE_MOVING_FILLCOLOR,
                                         lineWidth=4, units='height')        
                                         
        # Dot for showing et data
        self.et_sample_l = visual.Circle(win, radius = graphics.ET_SAMPLE_RADIUS, 
                                         fillColor = 'red', units='deg') 
        self.et_sample_r = visual.Circle(win, radius = graphics.ET_SAMPLE_RADIUS, 
                                         fillColor = 'blue', units='deg')   
        self.et_line_l = visual.Line(win, lineColor = 'red', units='deg', lineWidth=0.4)
        self.et_line_r = visual.Line(win, lineColor = 'blue', units='deg', lineWidth=0.4)
        
      
        # Show images (eye image, validation resutls)
        self.eye_image_stim_l = visual.ImageStim(win, units='norm',
                                                   size=graphics.EYE_IMAGE_SIZE,
                                                   pos=graphics.EYE_IMAGE_POS_L, 
                                                   image=np.zeros((512, 512)))
        self.eye_image_stim_r = visual.ImageStim(win, units='norm',
                                                   size=graphics.EYE_IMAGE_SIZE,
                                                   pos=graphics.EYE_IMAGE_POS_R,
                                                   image=np.zeros((512, 512)))
      
        # Accuracy image 
        self.accuracy_image = visual.ImageStim(win, image=None,units='norm', size=(1.5,1.5),
                                          pos=(0, 0.25))
        
        
        # Trackign monitor background and eyes for tracking monitor
#        self.tracking_monitor = visual.ImageStim(win, image=None,units='norm', size=(0.5,0.5),
#                                          pos=(0, -0.5), ori = 180)        
        self.tracking_monitor_background = visual.Rect(win, units='norm', fillColor=graphics.TRACKING_MONITOR_COLOR,
                                                        lineColor=graphics.TRACKING_MONITOR_COLOR,
                                                       width=graphics.TRACKING_MONITOR_SIZE[0], 
                                                       height=graphics.TRACKING_MONITOR_SIZE[0],
                                                       pos=graphics.TRACKING_MONITOR_POS)
        self.eye_l = visual.Circle(win, radius = graphics.EYE_SIZE, 
                                         lineColor = graphics.EYE_COLOR_VALID,
                                         lineWidth=0.01, units='height')
        self.eye_r = visual.Circle(win, radius = graphics.EYE_SIZE, 
                                         lineColor = graphics.EYE_COLOR_VALID,
                                         lineWidth=0.01, units='height')        
        
        self.eye_l_closed = visual.Rect(win, fillColor=(1,1,1), 
                                        lineColor=(1,1,1), units='height')
        self.eye_r_closed = visual.Rect(win, fillColor=(1,1,1), 
                                        lineColor=(1,1,1), units='height')        
        self.eye_text_l = visual.TextStim(win,text='L',height = graphics.EYE_SIZE, units='height')        
        self.eye_text_r = visual.TextStim(win,text='R',height = graphics.EYE_SIZE, units='height')                                           
        
 
    def is_connected(self):
        pass
        
    #%%
    def calibrate(self, win, eye='both', calibration_number = 'second'):
        ''' Enters the calibration screen and gives the user control 
        over what happens
        Args:
            win - psychopy window object
            eye - 'left', 'right', or 'both' - default
            calibration_number - 'first' or 'second'. If 'first', don't exit
                                 calibration mode until 'second' calibration 
                                 has finished
            
        '''
        if self.eye_tracker_name != 'Spectrum':
            assert eye=='both', 'Monocular calibrations available only in Spectrum'
            
        self.eye = eye
        self.win = win
        self.mouse = event.Mouse()
        self.mouse.setVisible(0)
        
        self.calibration_number = calibration_number
        
        # Create click buttons used during calibration
        self._create_calibration_buttons(win)
        
        # Animated calibration?
        if self.settings.ANIMATE_CALIBRATION:
            
            # Define your calibration target
            target = helpers.MyDot2(self.win, units='pix',
                                     outer_diameter = win.size[0] * 0.02, 
                                     inner_diameter = win.size[0] * 0.005)
            self.animator = helpers.AnimatedCalibrationDisplay(self.win, target, 'animate_point')        
        
        # Screen based calibration 
        if self.eye_tracker_name == 'Spectrum':
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
                action = self._run_calibration()
            elif 'val' in action:
                action = self._run_validation()
            elif 'res' in action:
                action, selected_calibration = self._show_validation_screen()
#            elif 'adv' in action:
##                action = self._advanced_setup()
#                action = self._show_eye_image()
                
            elif 'done'in action:
                print('calibration completed')
                break
            elif 'quit' in action:
                self.stop_recording()
                self.win.close()
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
            if i == selected_calibration-1:
                self.all_validation_results.append(devs + ['used'])
            else:
                self.all_validation_results.append(devs + ['not used'])              

    #%% 
    def set_dummy_mode(self):
        # Set current class to Dummy class
        import Tobii_dummy
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
                                                 self.settings.mon, 
                                                 self.settings.SCREEN_HEIGHT)       
        self.et_sample_l.draw()
            
#        if self.eye == 'right' or self.eye == 'both':
        self.et_sample_r.pos = helpers.tobii2deg(np.array([[rx, ry]]), 
                                                 self.settings.mon, 
                                                 self.settings.SCREEN_HEIGHT)
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
        
        # Initialize values for position and color of eyes
        xyz_pos_eye_l = (0, 0, 0)
        xyz_pos_eye_r = (0, 0, 0)
        self.eye_l.fillColor = (1, 1, 1)
        self.eye_r.fillColor = (1, 1, 1)
        
        self.store_data = False
        
        # Start streaming of eye images
        self.start_recording(image_data=True, store_data = False)

        core.wait(0.5)
        
        if not self.get_latest_sample():
            self.win.close()
            raise ValueError('Eye tracker switched on?')
            
            
        offset = np.array([0, 0, 0])
        circle_pos_both = np.array([0, 0, 0])
        valid_eye_temp = np.array([0, 0])
        reset_i = 0
        
        show_eye_images = False
        image_button_pressed = False
        while True:
            
            # Draw four dots in the corners
            for i in self.POS_CAL_CHECK_DOTS:
                self.setup_dot.setPos(i)
                self.setup_dot.draw()

            # Draw buttons, one to calibrate, and one to 
            # go to the advanced setup screen
            self.calibrate_button.draw()
            self.calibrate_button_text.draw()   
            
            # Get keys
            k = event.getKeys()
                
            # Draw setup button information  and check whether is was selected
            self.setup_button.draw()
            self.setup_button_text.draw()            
            if graphics.SETUP_BUTTON in k or (self.mouse.isPressedIn(self.setup_button, buttons=[0]) and not image_button_pressed):
                # Toggle visibility of eye images
                show_eye_images = not show_eye_images
                image_button_pressed = True
                             
             # Get position of eyes in track box
            sample = self.get_latest_sample()
            xyz_pos_eye_l = sample['left_gaze_origin_in_trackbox_coordinate_system']
            xyz_pos_eye_r = sample['right_gaze_origin_in_trackbox_coordinate_system']
          
            # Compute the average position of the eyes
            avg_pos = np.nanmean([xyz_pos_eye_l, xyz_pos_eye_r], axis=0)
            
            # If one eye is closed, the center of the circle is moved, 
            # Try to prevent this by compensating by an offset            
            if self.eye == 'both':
                valid_left = np.sum(np.isnan(xyz_pos_eye_l))
                valid_right = np.sum(np.isnan(xyz_pos_eye_r))
                valid_eye = np.array([valid_left, valid_right]) # [0, 1] means that left is valid
                valid_sum = valid_left + valid_right        
                if valid_sum == 0: # if both eyes are open
                    circle_pos_both = avg_pos[:]
                    offset = np.array([0, 0, 0])
                    reset_i = 0
                elif  valid_sum == 3: # if one eye is closed
                    if reset_i == 0:
                        offset = np.array(circle_pos_both - avg_pos)
                        reset_i = 1
                        valid_eye_temp = valid_eye[:]
                    if np.sum(valid_eye == valid_eye_temp) < 2:
                        offset *= -1 # 
                        valid_eye_temp = valid_eye[:]
                    
            # Compute position and size of circle
            #(0.5, 0.5, 0.5)  means the eye is in the center of the box
            self.moving_circ.pos = ((avg_pos[0] - 0.5) * -1 - offset[0] , 
                                    (avg_pos[1] - 0.5) * -1 - offset[1]) 
                                    
            self.moving_circ.radius = (avg_pos[2] - 0.5)*-1 + graphics.HEAD_POS_CIRCLE_MOVING_RADIUS
            
            # Control min size of radius
            if self.moving_circ.radius < graphics.HEAD_POS_CIRCLE_MOVING_MIN_RADIUS:
                self.moving_circ.radius = graphics.HEAD_POS_CIRCLE_MOVING_MIN_RADIUS
            
            # Draw circles
            self.moving_circ.draw()
            self.static_circ.draw()
                        
            # Draw instruction
            self.instruction_text.pos = (0, 0.8)
            self.instruction_text.text = 'Position yourself such that the two circles overlap.'
            self.instruction_text.draw()
            
            # Get and draw distance information
            l_pos = self.get_latest_sample()['left_gaze_origin_in_user_coordinate_system'][2]
            r_pos = self.get_latest_sample()['right_gaze_origin_in_user_coordinate_system'][2]
            
            # Draw eyes
            if self.eye == 'both' or self.eye == 'left':
                if np.isnan(xyz_pos_eye_l[0]):
                    self.eye_l_closed.pos = (self.moving_circ.pos[0] - self.moving_circ.radius/2.0,
                                      self.moving_circ.pos[1])
                    self.eye_l_closed.width = self.moving_circ.radius / 2.0 
                    self.eye_l_closed.height = self.eye_l_closed.width / 4.0
                    self.eye_l_closed.draw()                
                else:
                    self.eye_l.pos = (self.moving_circ.pos[0] - self.moving_circ.radius/2.0,
                                      self.moving_circ.pos[1])
                    self.eye_l.radius = self.moving_circ.radius / 4.0   
                    self.eye_l.draw()     
                    
                # Indicate that the right eye is not used
                if self.eye == 'left':
                    self.eye_r_closed.fillColor = (1, -1, -1) # Red
                    self.eye_r_closed.pos = (self.moving_circ.pos[0] + self.moving_circ.radius/2.0,
                                      self.moving_circ.pos[1])
                    self.eye_r_closed.width = self.moving_circ.radius / 2.0 
                    self.eye_r_closed.height = self.eye_r_closed.width / 4.0
                    self.eye_r_closed.draw() 
                    
                    
            if self.eye == 'both' or self.eye == 'right':    
                if np.isnan(xyz_pos_eye_r[0]):
                    self.eye_r_closed.pos = (self.moving_circ.pos[0] + self.moving_circ.radius/2.0,
                                      self.moving_circ.pos[1])
                    self.eye_r_closed.width = self.moving_circ.radius / 2.0 
                    self.eye_r_closed.height = self.eye_r_closed.width / 4.0
                    self.eye_r_closed.draw()                    
                else:
                    self.eye_r.pos = (self.moving_circ.pos[0] + self.moving_circ.radius/2.0,
                                      self.moving_circ.pos[1])
                    self.eye_r.radius = self.moving_circ.radius / 4.0       
                    self.eye_r.draw()
                    
                # Indicate that the right eye is not used
                if self.eye == 'right':
                    self.eye_l_closed.fillColor = (1, -1, -1) # Red
                    self.eye_l_closed.pos = (self.moving_circ.pos[0] - self.moving_circ.radius/2.0,
                                      self.moving_circ.pos[1])
                    self.eye_l_closed.width = self.moving_circ.radius / 2.0 
                    self.eye_l_closed.height = self.eye_l_closed.width / 4.0
                    self.eye_l_closed.draw()                         
             
            
            try:
                self.instruction_text.pos = (0, 0.9)
                self.instruction_text.text = ' '.join(['Distance:', 
                                                       str(int(np.nanmean([l_pos, r_pos])/10.0)), 'cm'])
                self.instruction_text.draw() 
            except:
                pass
            
            # Show eye images if requested
            if show_eye_images:
                self._draw_eye_image()  
                

#            # Advanced setup
#            if graphics.SETUP_BUTTON in k:
#                action = 'adv'
#                break 
                
            # check whether someone left clicked any of the buttons or pressed 'space'
            if graphics.CAL_BUTTON in k or self.mouse.isPressedIn(self.calibrate_button, buttons=[0]):
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
     
#        self.stop_recording()
        
        # Stop streaming of eye images
        self.stop_recording(image_data=True)   
        self.mouse.setVisible(0)
        
        return action
                
        

    #%%    
    def _run_calibration(self):  
        ''' Calibrates the eye tracker
        Args:   target_pos: N x 4 array with target positions 
                first two columns are Tobii coords (x, y) and the two last
                are position in degrees (PsychoPy coord system)
                pval: pacing interval (how long each dot is shown)
        '''
        
        
        self.win.flip()
        
        self.store_data = True
        
        cal_pos=self.settings.CAL_POS
        paval=self.settings.PACING_INTERVAL   
        
        # Optional start recording of eye images
        if self.settings.RECORD_EYE_IMAGES_DURING_CALIBRATION:
            self.start_recording(image_data=True)            
        
        np.random.shuffle(cal_pos)
                
        core.wait(0.5)     
        self.send_message('Calibration_start')

        
        action = 'setup'
        
        # Go through the targets one by one
        for i, pos in enumerate(cal_pos[:, :2]):
            # Display dot and give user chance to move the eye
            self.cal_dot.setPos(cal_pos[i, 2:]) # Tobii and psychopy have different coord systems
            self.cal_dot.draw()
            self.win.flip()
            self.send_message('Calibration point {} at position {} {}'.format(i, pos[0], pos[1]))

            
            if paval == 0:
                k = event.waitKeys()
            else:
                core.wait(paval)
                k = event.getKeys() 
            
            # Collect some data 
            if self.eye_tracker_name == 'Spectrum':
                if self.eye == 'left':
                    if self.calibration.collect_data(pos[0], pos[1], self.eye_to_calibrate) != tr.CALIBRATION_STATUS_SUCCESS_LEFT_EYE:
                        self.calibration.collect_data(pos[0], pos[1], self.eye_to_calibrate)
                elif self.eye == 'right':
                    if self.calibration.collect_data(pos[0], pos[1], self.eye_to_calibrate) != tr.CALIBRATION_STATUS_SUCCESS_RIGHT_EYE:
                        self.calibration.collect_data(pos[0], pos[1], self.eye_to_calibrate)
                else:
                    if self.calibration.collect_data(pos[0], pos[1], self.eye_to_calibrate) != tr.CALIBRATION_STATUS_SUCCESS:
                        self.calibration.collect_data(pos[0], pos[1], self.eye_to_calibrate)  
            else:
                if self.calibration.collect_data(pos[0], pos[1]) != tr.CALIBRATION_STATUS_SUCCESS:
                    self.calibration.collect_data(pos[0], pos[1])                
                          
                  
            # Abort calibration if esc is pressed (and go back to setup screen)
            if 'escape' in k:                
#                self.calibration.leave_calibration_mode()
                return action
                
                
            # 'r' aborts and restarts calibration 
            if 'r' in k:
#                self.calibration.leave_calibration_mode()
                action = 'cal' 
                return action                          
            
        # Clear the screen
        self.win.flip()       

        # Apply the calibration and get the calibration results
        calibration_result = self.calibration.compute_and_apply()
        self.calibration_results = calibration_result
        print("Compute and apply returned {0} and collected at {1} points.".
              format(calibration_result.status, len(calibration_result.calibration_points)))       
        

        
        # Accept of redo the calibration?
        if 'success' in calibration_result.status:   
            action = 'val'
            if 'Spectrum' in self.eye_tracker_name:
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
            if self.settings.RECORD_EYE_IMAGES_DURING_CALIBRATION:
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
                                       self.settings.mon, self.settings.SCREEN_HEIGHT)
            self.cal_dot.setPos(xy_dot) # Tobii and psychopy have different coord systems            
            self.cal_dot.draw()
                        
            if self.eye == 'both' or self.eye == 'left':
                # Save gaze data for left eye to list
                for si in p.calibration_samples: # For each sample
                    samples_l = si.left_eye.position_on_display_area
                    x, y = samples_l
                    xy_sample = helpers.tobii2deg(np.array([[x, y]]), 
                                                  self.settings.mon, self.settings.SCREEN_HEIGHT) # Tobii and psychopy have different coord systems
                    xys_left.append([xy_sample[0][0], xy_sample[0][1]])
                    cal_data.append([x_dot, y_dot, x, y, 'left'])
                    
            if self.eye == 'both' or self.eye == 'right':                   
                # Save gaze data for right eye to list
                for si in p.calibration_samples:
                    samples_r = si.right_eye.position_on_display_area
                    x, y = samples_r
                    xy_sample = helpers.tobii2deg(np.array([[x, y]]), 
                                                  self.settings.mon, self.settings.SCREEN_HEIGHT) # Tobii and psychopy have different coord systems
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
        nCalibrations = len(self.deviations) + 1
        fname = 'calibration_image' + str(nCalibrations)+'.png'
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
                print("Saving calibration to file for eye tracker with serial number {0}.".format(self.tracker.serial_number))
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
            print("Applying calibration on eye tracker with serial number {0}.".format(self.tracker.serial_number))
            self.tracker.apply_calibration_data(calibration_data)
            
        
    #%%   
    def _run_validation(self,  data_capture_int = 0.5):
        ''' Runs a validation to check the accuracy of the calibration
        '''
        
                
        target_pos = self.settings.VAL_POS
        paval = self.settings.PACING_INTERVAL
        
        
        np.random.shuffle(target_pos)
        
        # Set this to true if you want all data from the validation to 
        # end up in the main data file (default, False)
        self.store_data = True
        self.send_message('Validation_start')
        
        action = 'setup'
        old_ts = 0
        validation_data = [] 
        xy_pos = [] # Stores [l_por_x, l_por_y, r_por_x, r_por_y, target_x, target, y]
        for i, p in enumerate(target_pos[:, 2:]):
            self.cal_dot.setPos(p) # Tobii and psychopy have different coord systems
            self.cal_dot.draw()
            self.win.flip()
            self.send_message('validation point {} at position {} {}'.format(i, p[0], p[1]))
            if paval == 0:
                k = event.waitKeys()
            else:
                core.wait(paval)
                k = event.getKeys() 
            
            # Abort calibration if esc is pressed (and go back to setup screen)
            if 'escape' in k:
                action = 'setup'
                return action
                
            # 'r' aborts and restarts calibration 
            if 'r' in k:
                action = 'cal' 
                return action
            
            # Collect data for some time
            t0 = core.getTime()
            sample = []
            while (core.getTime() - t0) < data_capture_int:
                
                time_stamp = self.gaze_data['device_time_stamp']
                if time_stamp != old_ts: 
                    
                    s = self.get_latest_sample()
                    sample.append(s)
                    xy_pos.append([time_stamp, 
                                   s['left_gaze_point_on_display_area'][0], 
                                   s['left_gaze_point_on_display_area'][1], 
                                   s['right_gaze_point_on_display_area'][0], 
                                   s['right_gaze_point_on_display_area'][1], 
                                   p[0], p[1]])
                core.wait(0.001)
                old_ts = time_stamp
                
            validation_data.append(sample)
            
        self.send_message('Validation_end')
#        self.stop_recording()
        
        self.win.flip()

        # Convert data from Tobii coord system to PsychoPy coordinates 
        gaze_pos = np.array(xy_pos)
        gaze_pos[:, 1:3] = helpers.tobii2deg(gaze_pos[:, 1:3], self.settings.mon, self.settings.SCREEN_HEIGHT)
        gaze_pos[:, 3:5] = helpers.tobii2deg(gaze_pos[:, 3:5], self.settings.mon, self.settings.SCREEN_HEIGHT)

        # Generate an image of the validation results (if validation was completed)
#        if len(xy_pos) == len(target_pos):
#        self.deviations.append([1, 2, 3, 4])
        
        # Compute data quality per validation point
        deviation_l, rms_l = self._compute_data_quality(validation_data, target_pos[:, :2], 'left')
        deviation_r, rms_r = self._compute_data_quality(validation_data, target_pos[:, :2], 'right')
        
        if self.eye == 'left':
            deviation_r = np.nan
            rms_r = np.nan
            
        if self.eye == 'right':
            deviation_l = np.nan
            rms_l = np.nan            
            
        self.deviations.append([np.nanmean(deviation_l), np.nanmean(deviation_r),
                                np.nanmean(rms_l), np.nanmean(rms_r)])
            
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
            self.cal_dot.setPos(p )
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
        nCalibrations = len(self.deviations)
        fname = 'validation_image' + str(nCalibrations)+'.png'
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
        for p, point_data in enumerate(validation_data):
            
            #print(point_data)
            val_point_position = self._adcs2ucs(val_point_positions[p])
            
            # For each sample
            deviation_per_sample = []
            angle_between_samples = []
            gaze_vector_old = 0
            for i, sample in enumerate(point_data):
                #print(sample)
                gaze_vector = (sample[eye + '_gaze_point_in_user_coordinate_system'][0] - 
                               sample[eye + '_gaze_origin_in_user_coordinate_system'][0],
                               sample[eye + '_gaze_point_in_user_coordinate_system'][1] - 
                               sample[eye + '_gaze_origin_in_user_coordinate_system'][1],
                               sample[eye + '_gaze_point_in_user_coordinate_system'][2] - 
                               sample[eye + '_gaze_origin_in_user_coordinate_system'][2]) 
                
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
            
        return deviation_per_point, rms_per_point
                            
            
    #%%     
    def _show_validation_screen(self):
        ''' Shows validation image after a validation has been completed
        '''    
        # Center position of presented calibration values
        x_pos_res = 0.5
        y_pos_res = -0.4
        
        self.mouse.setVisible(1)
        
        # We do not want to save any data here    
        self.store_data = False

        # get (and save) validation screen image
        nCalibrations = len(self.deviations)
        fname = 'validation_image' + str(nCalibrations)+'.png'
        self.save_calibration(str(nCalibrations))
        core.wait(0.2)
        
        # Add image as texture
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
        print(accuracy_values)

        y_pos = y_pos_res
        print(self.deviations)
        for i in range(nCalibrations):
            print(self.deviations[i])
            select_accuracy_rect.append(visual.Rect(self.win, width= 0.15, 
                                                height= 0.05, 
                                                units='norm',
                                                pos = (x_pos_res, y_pos)))
                                                
            select_rect_text.append(visual.TextStim(self.win,
                                                    text='Select',
                                                    wrapWidth = 1,
                                                    height = graphics.TEXT_SIZE, 
                                                    units='norm',
                                                    pos = (x_pos_res, y_pos)))  
                    
            # Then prepare the accuracy values for each calibration preceded 
            # by Cal x (the calibration number)
            accuracy_values_j = []
            for j, x in enumerate(x_pos):       
                if j > 0:
                    accuracy_values_j.append(visual.TextStim(self.win,
                                                        text='{0:.2f}'.format(self.deviations[i][j - 1]),
                                                        wrapWidth = 1,
                                                        height = graphics.TEXT_SIZE, 
                                                        units='norm',
                                                        pos = (x, y_pos),
                                                        color = (1, 1, 1)))                
                else:
                    accuracy_values_j.append(visual.TextStim(self.win,
                                                        text='Cal' + str(i+1) + ':',
                                                        wrapWidth = 1,
                                                        height = graphics.TEXT_SIZE, 
                                                        units='norm',
                                                        pos = (x, y_pos),
                                                        color = (1, 1, 1))) 
            accuracy_values.append(accuracy_values_j)                 
            y_pos -= 0.06
            
        for i in range(nCalibrations):            
            for j, x in enumerate(x_pos): 
                print(i, j, accuracy_values[i][j].text, accuracy_values[i][j].pos)            
        
        print('acc values done')
        
        # Prepare header
        header_text = []    
        self.instruction_text.color = (1, 1, 1) 
        y_pos = y_pos_res
        for j, x in enumerate(x_pos):
            header_text.append(visual.TextStim(self.win,text=header[j],
                                                wrapWidth = 1,
                                                height = graphics.TEXT_SIZE, 
                                                units='norm',
                                                pos = (x, y_pos_res + 0.06),
                                                color = (1, 1, 1)))
                                                
        print('header done')

        # Wait for user input
        selected_calibration = nCalibrations # keep track of which calibration is selected
        selection_done = False
        display_gaze = False
        gaze_button_pressed = False
        cal_image_button_pressed = False
        timing = []
        while not selection_done:
                        
            t0 = self.clock.getTime()
             
            # Draw validation results image
            self.accuracy_image.draw()
                                   
            # Draw buttons (re-calibrate, accept and move on, show gaze)
            self.recalibrate_button.draw()
            self.recalibrate_button_text.draw()
            
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
                if i == selected_calibration - 1: # Calibration selected
#                    select_rect_text[i].color = graphics.blue_active
                    select_accuracy_rect[i].fillColor = graphics.blue_active
                    if nCalibrations > 1:
                        select_accuracy_rect[i].draw() 
                        select_rect_text[i].draw()     
                else:
#                    select_rect_text[i].color = graphics.blue
                    select_accuracy_rect[i].fillColor = graphics.blue
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
                    selected_calibration = int(i + 1)
                    break
                    
            # Check if key or button is pressed
            k = event.getKeys()
            if graphics.RECAL_BUTTON in k or self.mouse.isPressedIn(self.recalibrate_button):
                action = 'setup'
                selection_done = True
            elif graphics.ACCEPT_BUTTON in k or self.mouse.isPressedIn(self.accept_button):
                action = 'done'
                selection_done = True                
            elif k:
                if k[0].isdigit():
                    if any([s for s in range(nCalibrations+1) if s == int(k[0])]):
                        self.load_calibration(k[0])  # Load the selected calibration
                        fname = 'validation_image' + str(k[0]) + '.png'
                        self.accuracy_image.image = fname
                        selected_calibration = int(k[0])       
                        
            elif 'escape' in k:
                action = 'quit'
                break
                
            # Toggle display gaze
            if graphics.GAZE_BUTTON in k or (self.mouse.isPressedIn(self.gaze_button, buttons=[0]) and not gaze_button_pressed):
                display_gaze = not display_gaze
                gaze_button_pressed = True
              
            # Display gaze along with four dots in the corners
            if display_gaze:
                for i in self.POS_CAL_CHECK_DOTS:
                    self.setup_dot.setPos(i)
                    self.setup_dot.draw()
                self._draw_gaze()
                
            # Show calibration image or validation image
            if graphics.CAL_IMAGE_BUTTON in k or (self.mouse.isPressedIn(self.calibration_image, buttons=[0])and not cal_image_button_pressed):
                
                # Toggle the state of the button
                show_validation_image = not show_validation_image
                
                # If validation image show, switch to calibration and vice versa
                if show_validation_image:
                    fname = 'validation_image' + str(nCalibrations)+'.png'
                    self.accuracy_image.image = fname                
                else:
                    fname = 'calibration_image' + str(nCalibrations)+'.png'
                    self.accuracy_image.image = fname                     

                cal_image_button_pressed = True
                
            # Wait for release of show gaze_button
            if not np.any(self.mouse.getPressed()):
                gaze_button_pressed = False     
                cal_image_button_pressed = False
                
            timing.append(self.clock.getTime()-t0)
            self.win.flip() 
        
        # Clear screen and return
        self.instruction_text.color = (1, 1, 1)
        self.win.flip()
        self.mouse.setVisible(0)

        
        return action, selected_calibration
                
    #%%   
    def system_info(self):   
        ''' Returns information about system in dict
        '''
        
        info = {}
        info['serial_number']  = self.tracker.serial_number
        info['Address']  = self.tracker.address
        info['Model']  = self.tracker.model
        info['Name']  = self.tracker.device_name
        info['tracking_mode']  = self.tracker.get_eye_tracking_mode()
        info['sampling_frequency']  = self.tracker.get_gaze_output_frequency()
        
        return info
#        self.info = info
   
        
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
    def get_samples_from_buffer(self):
        ''' Consume all samples '''
        return self.buf.peek() 
        
#    def send_file_log_message(self, msg):
#        self.fid.write(msg)
    #%%    
    def send_message(self, msg):
        ''' Sends a message to the data file
        '''       
        ts = self.get_system_time_stamp()
        self.msg_container.append([ts, msg])
        
    #%%
    def get_latest_sample(self):
        ''' Gets the most recent sample 
        '''
        return self.gaze_data

    #%%            
    def start_recording(self,   gaze_data=False, 
                                sync_data=False,
                                image_data=False,
                                stream_error_data=False,
                                store_data=True):
        ''' Starts recording 
        '''
        
        if gaze_data:
            self.subscribe_to_gaze_data()
        if sync_data:
            self.subscribe_to_time_synchronization_data()
        if image_data:
            self.subscribe_to_eye_images()
        if stream_error_data:
            self.subscribe_to_external_signal()            
            
        self.store_data = store_data
            
        core.wait(0.5)
    #%%    
    def stop_recording(self,    gaze_data=False, 
                                sync_data=False,
                                image_data=False,
                                stream_error_data=False):    
        ''' Stops recording
        '''        
        
        if gaze_data:
            self.usubscribe_from_gaze_data()
        if sync_data:
            self.unsubscribe_from_time_synchronization_data()
        if image_data:
            self.unsubscribe_from_eye_images()   
        if stream_error_data:
            self.usubscribe_from_external_signal()                
            
        # Stop writing to file            
        self.store_data = False          
 
    #%%
    def _external_signal_callback(self, callback_object):
        ''' Callback function for external signals        
        '''
        
        if self.store_data:
            gdata = (callback_object['device_time_stamp'],
                     callback_object['system_time_stamp'],
                     callback_object['value'],
                     callback_object['change_type'])
                     
            self.external_signal_container.append(gdata)
        
    #%%
    def subscribe_to_external_signal(self):
        ''' Starts subscribing to gaze data
        '''
        self.tracker.subscribe_to(tr.EYETRACKER_EXTERNAL_SIGNAL, self._external_signal_callback, as_dictionary=True)
        
    #%%
    def usubscribe_from_external_signal(self):
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
    def get_latest_eye_image(self):
        ''' Retuns the most recently acquired eye image
        as a numpy array
        '''
    
        print("System time: {0}, Device time {1}, Camera id {2}".format(self.eye_image['system_time_stamp'],
                                                                         self.eye_image['device_time_stamp'],
                                                                         self.eye_image['camera_id']))
        im_info = self.eye_image
    
        #image = PhotoImage(data=base64.standard_b64encode(self.eye_image['image_data']))
        #print(self.eye_image)
        temp_im = StringIO(im_info['image_data'])
        tim = Image.open(temp_im)
        nparr = np.array(list(tim.getdata()))

        #tim.save("temp.gif","GIF")
        
        # Full frame or zoomed in image
        if im_info['image_type'] == 'eye_image_type_full':
            eye_image_size = graphics.EYE_IMAGE_SIZE_PIX_FULL_FRAME
            #tim.save("temp_full.gif","GIF")
        elif im_info['image_type'] == 'eye_image_type_cropped':
            eye_image_size = graphics.EYE_IMAGE_SIZE_PIX
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
      
        return nparr, im_info
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
                self.setup_dot.setPos(i)
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

            if graphics.BACK_BUTTON in k or self.mouse.isPressedIn(self.back_button, buttons=[0]):
                action = 'setup'
                break
                
            if graphics.CAL_BUTTON in k or self.mouse.isPressedIn(self.calibrate_button, buttons=[0]):
                action = 'cal'
                break

                
            self.win.flip()

#        self.stop_recording()
        self.stop_recording(image_data=True)            
        self.mouse.setVisible(0)
        
        return action
 
    #%%    
    def _draw_tracking_monitor(self, sample):     
        ''' Draws tracking monitor
        
        Args: 
            sample - Tobii sample dict
        '''

        #lineColor = graphics.EYE_COLOR_VALID
        self.eye_l.radius = graphics.EYE_SIZE
        self.eye_r.radius = graphics.EYE_SIZE
        
        xyz_pos_eye_l = sample['left_gaze_origin_in_trackbox_coordinate_system']
        xyz_pos_eye_r = sample['right_gaze_origin_in_trackbox_coordinate_system']
        validity_l = sample['left_gaze_origin_validity']
        validity_r = sample['right_gaze_origin_validity']     
        
        # Get position of eye in track box (decides color of eye circles),
        # eye green when in center of track box, and red when outside.
        xyz_pos_eye_l = self.get_latest_sample()['left_gaze_origin_in_trackbox_coordinate_system']
        xyz_pos_eye_r = self.get_latest_sample()['right_gaze_origin_in_trackbox_coordinate_system']
          
        avg_pos = []
        for i in np.arange(len(xyz_pos_eye_r)):
            avg_pos.append(np.nanmean([xyz_pos_eye_l[i], xyz_pos_eye_r[i]]))             
            
        # Let colors of eyes be proportional to how far away from the 
        # 'sweet spot' they are (green- best, red-worse)
        z_distance = avg_pos[2]
        if z_distance > 1:
            z_distance = 1
        if z_distance < 0:
            z_distance = 0
            
        red = np.abs(z_distance - 0.5) * 2
        green = 1 - np.abs(z_distance - 0.5) * 2
        blue = 0
        
        # Draw background
        self.tracking_monitor_background.draw()
        
        # Draw eyes
        xy = helpers.tobii2norm(np.array([xyz_pos_eye_r[:2]])) *graphics.TRACKING_MONITOR_SIZE[0]
        x = xy[0][0] * -1 * graphics.TRACKING_MONITOR_SIZE[0]/2.0 + 0.03
        y = xy[0][1] * graphics.TRACKING_MONITOR_SIZE[0]/2.0 + graphics.TRACKING_MONITOR_POS[1]/2
        
        if not np.isnan(x):
            self.eye_r.pos = (x, y)
            self.eye_text_r.pos = (x, y)
            
        if validity_r == 1:
            self.eye_r.fillColor = [red, green, blue] #graphics.green
        else:
            self.eye_r.fillColor = [0, 0, 0]
        self.eye_r.draw()
        self.eye_text_r.draw()
            
        xy = helpers.tobii2norm(np.array([xyz_pos_eye_l[:2]])) *graphics.TRACKING_MONITOR_SIZE[0]
        x = xy[0][0] * -1 * graphics.TRACKING_MONITOR_SIZE[0]/2.0 - 0.03
        y = xy[0][1] * graphics.TRACKING_MONITOR_SIZE[0]/2.0 + graphics.TRACKING_MONITOR_POS[1]/2
        
        if not np.isnan(x):
            self.eye_l.pos = (x, y)
            self.eye_text_l.pos = (x, y)
        if validity_l == 1:
            self.eye_l.fillColor = [red, green, blue]#graphics.green
        else:
            self.eye_l.fillColor = [0, 0, 0]#graphics.red  
        self.eye_l.draw()    
        self.eye_text_l.draw()
        
        
  
    #%%    
    def _draw_eye_image(self):
        ''' Draw left and right eye image
        '''
        
        if tr.CAPABILITY_HAS_EYE_IMAGES in self.tracker.device_capabilities: 
#                            
            im_arr, im_id = self.get_latest_eye_image()
                
            if im_id['camera_id'] == 0:
                self.eye_image_stim_l.image = im_arr
            elif im_id['camera_id'] == 1:
                self.eye_image_stim_r.image = im_arr                  
                    
            self.eye_image_stim_l.draw()          
            self.eye_image_stim_r.draw()

#    #%% 
#    def _update_eye_textures(self):
#        ''' Updates eye textures as soon as a eye image callback is called
#        '''
##        pass
#        im_arr, im_id = self.get_latest_eye_image()
#            
#        if im_id['camera_id'] == 0:
#            self.eye_image_stim_l.image = im_arr
#        elif im_id['camera_id'] == 1:
#            self.eye_image_stim_r.image = im_arr    
        
               
    #%%    
    def _eye_image_callback(self, im):
        ''' Here eye images are accessed and optionally saved to list
        Called every time a new eye image is available.
        
        Args:
            im - dict with information about eye image
            
        '''
        
        # Make eye image dict available to rest of class
        print(im.shape())
        self.eye_image = im           
        
        
#       # If in advanced setup mode, put image in texture to be displayed
#        if self.action == 'adv':
#            print('here')
#            self._update_eye_textures()
##            self.eye_image_stim_l.draw()
##            self.eye_image_stim_r.draw()
                        
        # Store image dict in list, if self.store_data = True
        if self.store_data:
            self.image_data_container.append(im)

    #%%    
    def subscribe_to_eye_images(self):
        ''' Starts sending eye images
        '''
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
    def subscribe_to_eyetracker_stream_errors(self):
        self.tracker.subscribe_to(tr.EYETRACKER_STREAM_ERRORS,
                                  self._stream_error_callback, as_dictionary=True)
    #%%    
    def unsubscribe_from_eyetracker_stream_errors(self):
        self.tracker.unsubscribe_from(tr.EYETRACKER_TIME_SYNCHRONIZATION_DATA)
        
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
    def save_data(self):
        ''' Saves the data
        '''
        
        # Save gaze data. If 32 bit Python version, Pandas throws a Memory error if
        # gaze_data_container > 2 GB. Therefore the csv-module is used instead.
        if sys.version_info >= (3,0,0):
            df = pd.DataFrame(self.gaze_data_container, columns=self.header)
            df.to_csv(self.filename[:-4] + '.tsv', sep='\t')
        else:        
            print(sys.getsizeof(self.gaze_data_container))
            with open(self.filename[:-4] + '.tsv', 'wb') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter='\t')
                csv_writer.writerow(self.header)
                for row in self.gaze_data_container:
                    csv_writer.writerow(row)          
            
        # Save messages
        df_msg = pd.DataFrame(self.msg_container,  columns = ['system_time_stamp', 
                                                              'msg'])
        df_msg.to_csv(self.filename[:-4] + '_msg.tsv', sep='\t')            
        
        # Dump other collected information to file
        with open(self.filename[:-4] + '.pkl','wb') as fp:
            pickle.dump(self.external_signal_container, fp)
            pickle.dump(self.sync_data_container, fp)
            pickle.dump(self.image_data_container, fp)
            pickle.dump(self.calibration_history(), fp)
            pickle.dump(self.system_info(), fp)
            python_version = '.'.join([str(sys.version_info[0]), 
                                  str(sys.version_info[1]),
                                  str(sys.version_info[2])])
            pickle.dump(python_version, fp)
            


    
    #%%    
    def de_init(self):
        '''
        '''
        
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class rawSDK(object):
    ''' Access Tobii SDK’s EyeTrackingOperations instance to call 
    its functions directly
    '''
        
    def __init__(self):
        pass
        
    def find_all_eye_trackers(self):
        return tr.find_all_eye_trackers()
    
    def get_system_time_stamp(self):
        return tr.get_system_time_stamp()    
    
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
    
    def get_hmd_lens_configuration(self):
        ''' Gets the current lens configuration of the HMD based eye tracker.
        The lens configuration describes how the lenses of the HMD device are 
        positioned.
        '''
        return self.tracker.get_hmd_lens_configuration()
    
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
       
    def set_display_area(self):
        return self.tracker.set_display_area
    
    def set_eye_tracking_mode(self):
        return self.tracker.set_eye_tracking_mode
    
    def set_gaze_output_frequency(self):
        return self.tracker.set_gaze_output_frequency
    
    def set_hmd_lens_configuration(self):
        return self.tracker.set_hmd_lens_configuration
    
    def subscribe_to(self):
        return self.tracker.subscribe_to
    
    def unsubscribe_from(self):
        return self.tracker.unsubscribe_from
    
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
        
        
        

        
        
        