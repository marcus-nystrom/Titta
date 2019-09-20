# -*- coding: utf-8 -*-
"""
Created on Thu Jun 01 14:11:57 2017

@author: Marcus
"""

from psychopy import visual, core, event
import time
from titta import helpers_tobii as helpers
from threading import Thread
import numpy as np

        
class Connect(Thread):
    """
    Create a class that simplifies life for people wanting to use the SDK
    """
    def __init__(self):
        
        # clock
        self.clock = core.Clock()
        
        # Dict to store samples
        self.sample = {}
     
    def init(self):
        ''' Connect to eye tracker
        and apply settings
        '''
        
        self.__stop = True
                
    #%%    
    def is_connected(self):
        print('is connected')      
    
    #%% Init calibration
    def calibrate(self, win, eye='right', calibration_number='first'):
        ''' Master function for setup and calibration
        '''
        
        # Window and instruction text for calibration        
        instruction_text = visual.TextStim(win,text='',wrapWidth = 1,
                                           height = 0.05, units='norm')  
        
        self.instruction_text = instruction_text
        
        self.win = win
        
        # Mouse object
        self.mouse = event.Mouse()        
        
        self.instruction_text.text = 'Calibration Dummy mode: ' + eye + ' eye'
        self.instruction_text.draw()
        self.win.flip()
        core.wait(2)
        
    #%%   
    def get_system_time_stamp(self):
        ''' Get system time stamp
        '''
        
        print('time_stamp')          
                
    #%%            
    def start_recording(self,   gaze_data=False, 
                                sync_data=False,
                                image_data=False,
                                stream_errors=False,
                                external_signal=False,
                                user_position_guide=False,
                                store_data=True):
        print('start_recording')      
        
    #%% 
    def start_sample_buffer(self, sample_buffer_length=3):  
        
        Thread.__init__(self)
        
        # Initialize the ring buffer
        self.buf = helpers.RingBuffer(maxlen=sample_buffer_length)
        self.__stop = False
        self.start()   
        
        
    #%%             
    def run(self):
        # Called by the e.g., et.start()
        # Continously read data into a ringbuffer
        while True:
            if self.__stop:        
                break
            
            # Get samples and store in ringbuffer  
            sample = self.get_latest_sample()
            
            self.buf.append(sample)
            time.sleep(0.01)            
        
    #%% 
    def send_message(self, msg, ts=None):
        print(msg)      
        
    #%%
    def get_latest_sample(self):
        ''' Simulates gaze position with mouse
        ToDO use same struct as gaze data
        '''
        x, y = self.mouse.getPos()
        
        self.sample['left_gaze_point_on_display_area'] = (x, y)
        self.sample['right_gaze_point_on_display_area'] = (x, y)
        
        return self.sample
        
    #%%
    def consume_buffer(self):
        ''' Consume all samples and empty buffer'''
        return self.buf.get_all() 
    
    #%%
    def peek_buffer(self):
        ''' Get samples in buffer without emptying the buffer '''
        return self.buf.peek()  
    
    #%% 
    def stop_sample_buffer(self):
        self.__stop = True
        
    #%%    
    def stop_recording(self,    gaze_data=False, 
                                sync_data=False,
                                image_data=False,
                                stream_errors=False,
                                external_signal=False,
                                user_position_guide=False):
        print('stop_recording')      
    #%% 
    def save_data(self, *argv):
        print('save_data')      
        
    #%%
    def de_init(self):
        print('de_init')      
    
    #%% 
    def set_dummy_mode(self):
        print('Does nothing')

    #%%     
    def calibration_history(self):
        print('Does calibration_history')
        return None
    

   
 