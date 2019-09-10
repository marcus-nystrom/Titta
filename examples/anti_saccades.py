#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy import visual, core, data, event, monitors # gui
import socket
from random import randint, uniform
import numpy as np
from psychopy import logging
import os, sys

# Insert the parent directory (where Titta is) to path
curdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(curdir)
sys.path.insert(0, os.sep.join([os.path.dirname(curdir), 'Titta'])) 
import Titta
import helpers_tobii as helpers  
from TalkToProLab import TalkToProLab
from helpers_tobii import MyDot2

#%%
class ProAntiSaccades(object):  
    
    def __init__(self, win, duration_central_target,
                 saccade_amplitude=8, 
                 duration_peripheral_target = 1,
                 screen_refresh_rate = 60,
                 Fs = 120,
                 eye_tracking = True,
                 screen_size = [1680, 1050],
                 tracker=None, # Eye tracker object
                 pro_lab_integration=False,
                 upload_stimuli=False,
                 pid=None):
        
        self.trialClock = core.Clock() # Init clock
        
        self.pro_instr = 'Look at the central dot; as soon as a new dot appears on the left or right, LOOK AT IT as fast as you can.'
        self.anti_instr = 'Look at the central dot; as soon as a new dot appears look in the OPPOSITE DIRECTION as fast as you can. You will probably sometimes make mistakes, and this is perfectly normal.'
        self.goodByeMessage = 'Thanks! That is all!'
        self.keypress_test = '(Press any key to TEST the experiment)'
        self.keypress_exp = '(Press any key to START the experiment)'
        self.correct_msg = 'Correct!, press space to continue'
        self.incorrect_msg = 'Incorrect!, press space to continue'
        self.break_instruction_s = 'Pause'
        self.break_instruction_e = 'seconds. Please do not remove your head from the chinrest. \n\n Feel free to blink.' 
                
    
        self.win = win
        self.saccade_amplitude = saccade_amplitude
        self.eye_tracking = eye_tracking
        self.tracker = tracker
        self.screen_refresh_rate = screen_refresh_rate
        self.screen_size = screen_size
        self.Fs = Fs
        self.pro_lab_integration = pro_lab_integration
        self.upload_stimuli = upload_stimuli
        
        # Target durations in frames
        self.duration_central_target = np.round(duration_central_target * screen_refresh_rate)
        self.duration_peripheral_target = duration_peripheral_target * screen_refresh_rate
            
        #Initialize stimuli used in experiment
        self.dot_stim = MyDot2(win)
        self.et_sample = visual.GratingStim(win, color='black', tex=None, mask='circle',units='pix',size=2)
        self.line = visual.Line(win, start=(-0.5, -0.5), end=(0.5, 0.5), units='pix')
        self.instruction_text = visual.TextStim(win,text='',wrapWidth = 10,height = 0.5)        
        
        # Connect to Pro Lab and add participant
        if pro_lab_integration:
            self.ttl = TalkToProLab()
            participant_info = self.ttl.add_participant(pid)
            upload_stimuli()
            
            self.rec = self.ttl.start_recording("antisaccade", 
                    participant_info['participant_id'], 
                    screen_width=self.screen_size[0],
                    screen_height=self.screen_size[1])
    
    def upload_stimuli(self):
        ''' Uploads all relevant stimuli to Pro Lab. They are
        
        * Central fixation point
        
        * Prosaccade left 
        * Prosaccade right 
        * Practice instruction text prosaccade
        * Instruction text prosaccade
        
        * Antisaccade left 
        * Antisaccade right   
        * Practice nstruction text antisaccade        
        * Instruction text antisaccade
        
        * Break instruction
        * Goodbye message
        
        
        '''
        self.stim_info = {} # Dict to keep track of media id for each stimulus
        
        
        # General settings
        aoi_color =  'AAC333'
        vertices_left = ((0, 0),
                         (self.screen_size[0]/2.0 - 100, 0), 
                         (self.screen_size[0]/2.0 - 100, self.screen_size[1]),
                         (0, self.screen_size[1]))      
        
        vertices_right = ((self.screen_size[0], self.screen_size[1]),
                         (self.screen_size[0]/2.0 + 100, 0), 
                         (self.screen_size[0]/2.0 + 100, self.screen_size[1]),
                         (self.screen_size[0], 0))         

        ######### Upload stimulus for central fixation cross
        im_name = 'central_fixation.png'
        self.dot_stim.set_pos((0,0))
        self.dot_stim.draw()
        win.getMovieFrame(buffer='back')   
        win.saveMovieFrames(im_name)  
        media_info = self.ttl.upload_media(im_name[:-4], im_name)   

        self.stim_info[im_name[:-4]] = media_info['media_id']
        
        ######### Upload stimulus for pro-saccade (target to left)
        # for corrent (left) and incorrect (right) aois
        im_name = 'prosaccade_left.png'
        self.dot_stim.set_pos((-8,0))
        self.dot_stim.draw()
        win.getMovieFrame(buffer='back')   
        win.saveMovieFrames(im_name)  
        media_info = self.ttl.upload_media(im_name[:-4], im_name)
        aoi_name = 'left'
        tag_name = 'correct'
        group_name = 'prosaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color, 
                              vertices_left, tag_name=tag_name, group_name=group_name)    
              
        aoi_name = 'right'
        tag_name = 'incorrect'
        group_name = 'prosaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color, 
                              vertices_right, tag_name=tag_name, group_name=group_name)    
          
        self.stim_info[im_name[:-4]] = media_info['media_id']
        
        ######### Upload stimulus for pro-saccade (target to right)
        # for corrent (right) and incorrect (left) aois
        im_name = 'prosaccade_right.png'
        self.dot_stim.set_pos((8,0))
        self.dot_stim.draw()
        win.getMovieFrame(buffer='back')   
        win.saveMovieFrames(im_name)  
        media_info = self.ttl.upload_media(im_name[:-4], im_name)
        aoi_name = 'right'
        tag_name = 'correct'
        group_name = 'prosaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color, 
                              vertices_left, tag_name=tag_name, group_name=group_name)    
              
        aoi_name = 'left'
        tag_name = 'incorrect'
        group_name = 'prosaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color, 
                              vertices_right, tag_name=tag_name, group_name=group_name)    
          
        self.stim_info[im_name[:-4]] = media_info['media_id']   
        
        ######### Upload stimulus for anti-saccade (target to left)
        # for corrent (left) and incorrect (right) aois
        im_name = 'antisaccade_left.png'
        self.dot_stim.set_pos((-8,0))
        self.dot_stim.draw()
        win.getMovieFrame(buffer='back')   
        win.saveMovieFrames(im_name)  
        media_info = self.ttl.upload_media(im_name[:-4], im_name)
        aoi_name = 'left'
        tag_name = 'incorrect'
        group_name = 'antisaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color, 
                              vertices_left, tag_name=tag_name, group_name=group_name)    
              
        aoi_name = 'right'
        tag_name = 'correct'
        group_name = 'antisaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color, 
                              vertices_right, tag_name=tag_name, group_name=group_name)    
          
        self.stim_info[im_name[:-4]] = media_info['media_id']
        
        ######### Upload stimulus for pro-saccade (target to right)
        # for corrent (right) and incorrect (left) aois
        im_name = 'antisaccade_right.png'
        self.dot_stim.set_pos((8,0))
        self.dot_stim.draw()
        win.getMovieFrame(buffer='back')   
        win.saveMovieFrames(im_name)  
        media_info = self.ttl.upload_media(im_name[:-4], im_name)
        aoi_name = 'right'
        tag_name = 'incorrect'
        group_name = 'antisaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color, 
                              vertices_left, tag_name=tag_name, group_name=group_name)    
              
        aoi_name = 'left'
        tag_name = 'correct'
        group_name = 'antisaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color, 
                              vertices_right, tag_name=tag_name, group_name=group_name)    
          
        self.stim_info[im_name[:-4]] = media_info['media_id']    
        
        ######### Upload stimulus prosaccade trial instruction
        im_name = 'pro_instruction_test.png'
        ins = self.pro_instr+'\n\n' + self.keypress_test
        self.instruction_text.setText(ins)
        self.instruction_text.draw()  
        media_info = self.ttl.upload_media(im_name[:-4], im_name)
        self.stim_info[im_name[:-4]] = media_info['media_id']          
        
        ######### Upload stimulus prosaccade exp instruction
        im_name = 'pro_instruction_exp.png'
        ins = self.pro_instr+'\n\n' + self.keypress_exp
        self.instruction_text.setText(ins)
        self.instruction_text.draw()  
        media_info = self.ttl.upload_media(im_name[:-4], im_name) 
        self.stim_info[im_name[:-4]] = media_info['media_id']          
        
        
        ######### Upload stimulus antisaccade trial instruction
        im_name = 'anti_instruction_test.png'
        ins = self.anti_instr+'\n\n' + self.keypress_test
        self.instruction_text.setText(ins)
        self.instruction_text.draw()  
        media_info = self.ttl.upload_media(im_name[:-4], im_name)
        self.stim_info[im_name[:-4]] = media_info['media_id']          
        
        
        ######### Upload stimulus prosaccade exp instruction
        im_name = 'anti_instruction_exp.png'
        ins = self.anti_instr+'\n\n' + self.keypress_exp
        self.instruction_text.setText(ins)
        self.instruction_text.draw()  
        media_info = self.ttl.upload_media(im_name[:-4], im_name) 
        self.stim_info[im_name[:-4]] = media_info['media_id']          
        
        
        ######### Upload break instruction
        im_name = 'break_instruction.png'
        break_instruction = ' '.join([self.break_instruction_s, 
                                      str(5),
                                      self.break_instruction_e])
        self.instruction_text.setText(break_instruction) # and then a break
        self.instruction_text.draw()
        media_info = self.ttl.upload_media(im_name[:-4], im_name)
        self.stim_info[im_name[:-4]] = media_info['media_id']                  

        ######### Goodbye message
        im_name = 'goodbye_instruction.png'
        self.instruction_text.setText(self.goodByeMessage) # and then a break
        self.instruction_text.draw()      
        media_info = self.ttl.upload_media(im_name[:-4], im_name)
        self.stim_info[im_name[:-4]] = media_info['media_id']  
        
    #%%    
    def prosaccades(self, nTrials, practice=False):
        ''' prosaccades
        '''
        
        # Display instruction and wait for input from the keyboard
        if practice:
            ins = self.pro_instr+'\n\n' + self.keypress_test
        else:
            ins = self.pro_instr+'\n\n' + self.keypress_exp 
        self.instruction_text.setText(ins)
        self.instruction_text.draw()
        self.win.flip()
        
        if self.pro_lab_integration:
            if practice:
                m_info = self.stim_info['pro_instruction_test']
            else:
                m_info = self.stim_info['pro_instruction_exp']
                
            self.ttl.send_stimulus_event(self.rec['recording_id'],
                                         str(self.ttl.get_time_stamp()),
                                         m_info) 
            
        event.waitKeys()    
        
        self.run_trials(nTrials, 'pro', practice=practice)
    
    #%%
    def antisaccades(self, nTrials, practice=False):
        ''' Antisaccades
        '''
        
      # Display instruction and wait for input from the keyboard
        if practice:
            ins = self.anti_instr+'\n\n' + self.keypress_test
        else:
            ins = self.anti_instr+'\n\n' + self.keypress_exp 

        self.instruction_text.setText(ins)
        self.instruction_text.draw()
        self.win.flip()
        
        if self.pro_lab_integration:
            if practice:
                m_info = self.stim_info['anti_instruction_test']
            else:
                m_info = self.stim_info['anti_instruction_exp']
                
            self.ttl.send_stimulus_event(self.rec['recording_id'],
                                         str(self.ttl.get_time_stamp()),
                                         m_info) 
            
        event.waitKeys()            
    
        self.run_trials(nTrials, 'anti', practice=practice)
    #%%
    def run_trials(self, nTrials, task, practice=False):
        '''
        '''
    
        # Start eye tracker
        if self.eye_tracking:
            if practice:
                self.tracker.start_recording(gaze_data=True, store_data=False)
            else:
                self.tracker.start_recording(gaze_data=True)
                
                
            
        # Now show the saccade targets one by one
        for i in range(nTrials):
                        
            # Coin flip to decide left or right side
            chooseSide = randint(0,1) # 0 - left, 1 - right
            if chooseSide == 0:
                sa = -self.saccade_amplitude
            else:
                sa = self.saccade_amplitude
            
            # Randomly select a duration of the central dot
            nFrames = np.random.choice(self.duration_central_target)
            
            # Display a central dot
            self.dot_stim.set_pos((0,0))
            
            # Wait for exactly nFrames frames
            for i, frames in enumerate(range(int(nFrames))):
                self.dot_stim.draw()
                self.win.flip()
                
                if i == 0 and self.pro_lab_integration:
                    self.ttl.send_stimulus_event(self.rec['recording_id'],
                                                 str(self.ttl.get_time_stamp()),
                                                 self.stim_info['central_fixation'])                     
                    
            # Display the peripheral dot
            self.dot_stim.set_pos((sa,0))
            self.dot_stim.draw()
            self.win.flip()
            
            if self.pro_lab_integration:
                if 'anti' in task:
                    if sa < 0:
                        self.ttl.send_stimulus_event(self.rec['recording_id'],
                                                     str(self.ttl.get_time_stamp()),
                                                     self.stim_info['antisaccade_right'])     
                    else:
                        self.ttl.send_stimulus_event(self.rec['recording_id'],
                                                     str(self.ttl.get_time_stamp()),
                                                     self.stim_info['antisaccade_left'])        
                else:
                    if sa < 0:
                        self.ttl.send_stimulus_event(self.rec['recording_id'],
                                                     str(self.ttl.get_time_stamp()),
                                                     self.stim_info['prosaccade_left'])         
                    else:
                        self.ttl.send_stimulus_event(self.rec['recording_id'],
                                                     str(self.ttl.get_time_stamp()),
                                                     self.stim_info['prosaccade_right'])   
            if self.eye_tracking:

                # If practice trial, show feedback
                if practice: 
                
                    self.tracker.send_message('_'.join(['START_TRIAL_PRACTICE', task, str(sa), str(i)]))
                    trialClock.reset()
                    t = 0
                    iSample = 0
                    nSampleToCollect = np.round(self.Fs * self.duration_peripheral_target / self.screen_refresh_rate) 

                    xy = np.empty([int(nSampleToCollect),2])

                    while t < (self.duration_peripheral_target / float(self.screen_refresh_rate)) and iSample < nSampleToCollect:
                        t = trialClock.getTime()
                        
                        # Get et sample and convert to pixels
                        et_sample = self.tracker.get_latest_sample()
                        
                        x_mean = np.nanmean([et_sample['left_gaze_point_on_display_area'][0],
                                          et_sample['right_gaze_point_on_display_area'][0]])
                        y_mean = np.nanmean([et_sample['left_gaze_point_on_display_area'][1],
                                          et_sample['right_gaze_point_on_display_area'][1]])    
    
                        pos = helpers.tobii2pix(np.array([[x_mean, y_mean]]), self.win.monitor)
                        pos[:, 0] = pos[:, 0] - self.screen_size[0]/2
                        pos[:, 1] = pos[:, 1] - self.screen_size[0]/4
                        
    
                        xy[iSample,0] = pos[:, 0]
                        xy[iSample,1] = pos[:, 1] * -1

                        # Draw data sample
                        if iSample > 0:
                            self.line.start = (xy[iSample - 1, 0], xy[iSample - 1, 1])
                            self.line.end = (xy[iSample, 0], xy[iSample, 1])
                            self.line.draw()

                        iSample+=1
                        
                        core.wait(1 / (self.Fs * 2))
                        
                    # Was the saccade performed correctly?
                    correct = 1
                    nSamples = 4 
                    if ('pro' in task and sa > 0 and np.sum(xy[:,0] < -self.screen_size[0]/16)     > nSamples) or \
                       ('pro' in task and sa < 0 and np.sum(xy[:,0] >  self.screen_size[0]/16)      > nSamples) or \
                       ('anti' in task and sa < 0 and np.sum(xy[:,0] < -self.screen_size[0]/16)    > nSamples) or \
                       ('anti' in task and sa > 0 and np.sum(xy[:,0] > self.screen_size[0]/16)     > nSamples):
                        correct = 0
                    
                    # Show target +  scanpath + performance feedback to the participant
                    if correct == 1:
                        ins = '\n\n\n' + self.correct_msg
                        self.instruction_text.setColor('green')
                    else:
                        ins = '\n\n\n' + self.incorrect_msg
                        self.instruction_text.setColor('red')          
                    
                    self.dot_stim.set_pos((0,0))
                    self.dot_stim.draw()       
                    self.dot_stim.set_pos((sa,0))
                    self.dot_stim.draw()           
                    self.instruction_text.setText(ins)
                    self.instruction_text.draw()
                    self.win.flip()
                    self.tracker.send_message('_'.join(['STOP_TRIAL_PRACTICE', task, str(sa), str(i)]))
                    # self.tracker.stop_recording(gaze_data=True)

                    k = event.waitKeys() # Here you discuss the feedback with the participants
                    self.instruction_text.setColor('white') 
                    
                else: # If actual recording (=not practice)
                    self.tracker.send_message('_'.join(['START_TRIAL_EXP', task, str(sa), str(i)]))
                    for frames in range(int(self.duration_peripheral_target)): # Wait for exactly nFrames frames
                        self.dot_stim.draw()
                        self.win.flip()
                    k = event.getKeys()
                    self.tracker.send_message('_'.join(['STOP_TRIAL_EXP', task, str(sa), str(i)]))

                
            else: # If not eye tracking, just wait             
                for frames in range(int(self.duration_peripheral_target)): # Wait for exactly nFrames frames
                    self.dot_stim.draw()
                    self.win.flip()
                k = event.getKeys()
            
            # Finally, check whether some one wants to quit or calibrate
            if k:
                if k[0] == 'escape':
                    print('Someone pressed escape')
                    self.win.close()
                    core.quit()
                elif k[0] == 'q':
                    if self.eye_tracking:
                        print('Someone pressed q, initiate calibration') 
                        self.tracker.calibrate(win)
 
            event.clearEvents() # Clear buffer of events  
            
        # Stops eye tracker when all trials are completed
        if self.eye_tracking:
            self.tracker.stop_recording(gaze_data=True)
            
    #%%        
    def take_a_break(self, duration, calibrate=False):
        ''' Break 
        Args:
            duration - time in s to break
        '''
        
        break_instruction = ' '.join([self.break_instruction_s, 
                                      str(duration),
                                      self.break_instruction_e])
        self.instruction_text.setText(break_instruction) # and then a break
        self.instruction_text.draw()
        self.win.flip()
        
        if self.pro_lab_integration:
            self.ttl.send_stimulus_event(self.rec['recording_id'],
                                         str(self.ttl.get_time_stamp()),
                                         self.stim_info['break_instruction'])         
        core.wait(duration)  
        
        # Optional calibration after the break
        if self.eye_tracking and calibrate:
            self.tracker.calibrate(win)
    #%%    
    def goodbye(self):   
        ''' Display message '''
        waitdur = 2
        self.instruction_text.setText(self.goodByeMessage) # and then a break
        self.instruction_text.draw()
        self.win.flip()
        ts = self.ttl.get_time_stamp()
        if self.pro_lab_integration:
            self.ttl.send_stimulus_event(self.rec['recording_id'],
                                         str(ts),
                                         self.stim_info['goodbye_instruction'],
                                         end_timestamp = str(ts + waitdur * 1000000))         
           
        core.wait(waitdur)      
        
        # Finalize recording
        self.ttl.finalize_recording(self.rec['recording_id'])        
        
#%%
def foreperiod_central_fixation(numel=1000, mu = 1.5, interval = [1, 3.5]): 
    ''' Computes the forperiod duration of each trial.

    
    Args:
        numel - number of foreperiods to generate
        mu - mean of foreperiod
        interval - interval of random part of foreperiod. 
        
    Returns:
        
    '''    
    forperiod_fixed = interval[0]
    
    # Really, really, dirty way to solve it for now!
    foreperiod_random = np.zeros(numel)
    while True:
        foreperiod_random = np.random.exponential(scale = 0.5, size=numel*2)
        foreperiod_random = foreperiod_random[foreperiod_random < interval[1]]
        
        if np.mean(foreperiod_random) < (mu - interval[0] + 0.001) and \
           np.mean(foreperiod_random) > (mu - interval[0] - 0.001):
           break
       
    foreperiod = forperiod_fixed + foreperiod_random[:numel]
    
    return foreperiod

#%%
#=======================================
# This is an implementation of the standardized antisaccade test 
# proposed in the paper Antoniades et al. "An internationally standardised antisaccade protocol", 2013, Vision Research
# Written by Marcus Nystrom (marcus.nystrom@humlab.lu.se) 2019-09-09
#======================================= 

# Run experiment with pro lab integration?
pro_lab_integration = False
upload_stimuli = False # Do this only the first time you run

#Monitor/geometry 
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = False
SCREEN_RES                  = [1920, 1080]
SCREEN_WIDTH                = 52.7 # cm
VIEWING_DIST                = 63 #  # distance from eye to center of screen (cm)

et_name = 'Tobii Pro Spectrum' 
et_name = 'IS4_Large_Peripheral' 

saccade_amplitude = 8
duration_central_target = foreperiod_central_fixation(numel=1000, 
                                                      mu = 1.5, 
                                                      interval = [1, 3.5])
duration_peripheral_target = 1

  
# ---------------------------------------------
#---- store info about the experiment
# ---------------------------------------------
expName = 'Antisaccades'
expInfo={'participant':'99', 'dummy_mode':['True', 'False']}
expInfo['dummy_mode'] = False
expInfo['participant'] = '99'
#dlg=gui.DlgFromDict(dictionary=expInfo,title=expName)
#if dlg.OK==False: 
#    core.quit() #user pressed cancel
#expInfo['date'] = data.getDateStr()#add a simple timestamp
#expInfo['computer_ip'] = socket.gethostbyname(socket.gethostname()).split('.')[-1]
#expInfo['expName'] = expName

# ---------------------------------------------
#---- setup files for saving  
# ---------------------------------------------
datapath = os.getcwd() + "\\data\\"
if not os.path.isdir(datapath):
    os.makedirs(datapath)

# Initiate clocks
trialClock =core.Clock() # Init clock

# Log output to a file
path = os.getcwd() + "\\log\\"
if not os.path.isdir(path):
    os.makedirs(path)
#filename='%s_%s_%s' %(expInfo['participant'], expInfo['computer_ip'], expInfo['date'])
filename = 'test'

mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)
 
# Window set-up (the color will be used for calibration)
win = visual.Window(monitor = mon, screen = 1,  
                    size = SCREEN_RES, 
                    units = 'deg', fullscr = FULLSCREEN,
                    allowGUI = False) 


    
# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile.tsv'

#%% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
print(expInfo['dummy_mode'])
if expInfo['dummy_mode'] == True:
    tracker.set_dummy_mode()
    print('DUMMY_MODE')
else:
    tracker.init()
    tracker.calibrate(win)
    print('ET MODE')
    
screen_refresh_rate = win.getActualFrameRate()
eye_tracker_sample_rate = settings.SAMPLING_RATEs   
        
# Initiate antisaccade class
sac = ProAntiSaccades(win, saccade_amplitude=saccade_amplitude, 
                 duration_central_target = duration_central_target,
                 duration_peripheral_target = duration_peripheral_target,
                 screen_refresh_rate = screen_refresh_rate,
                 Fs = eye_tracker_sample_rate,
                 screen_size = SCREEN_RES,
                 eye_tracking= expInfo['dummy_mode']==False,
                 tracker=tracker,
                 pro_lab_integration=False,
                 upload_stimuli=False,
                 pid = expInfo['participant']) 
#-----------------------------
# Program flow starts here
#-----------------------------


    
#-------- RUN THE BLOCKS HERE ---------------
 
# An example block
sac.antisaccades(nTrials=3, practice=True)
sac.antisaccades(nTrials= 3, practice=False)
#sac.take_a_break(10, calibrate=False) 
    
# # Third block
# #sac.antisaccades(nTrials=exp_params.nTrialsAnti, practice=False)
# #sac.take_a_break(exp_params.breakDuration, calibrate=False)

# # Fourth block
# sac.antisaccades(nTrials=exp_params.nTrialsAnti, practice=False)
# sac.take_a_break(exp_params.breakDuration, calibrate=False)

# # Fifth block
# sac.prosaccades(nTrials=exp_params.nPracticeTrialsPro, practice=True)
# sac.prosaccades(nTrials=exp_params.nTrialsPro, practice=False)

#-------- DONE WITH ANTISACCADES ---------------

sac.goodbye()
 
# Save data and close connection with eye trackers
if not expInfo['dummy_mode']:
    tracker.save_data()

# Close PsychoPy window
win.close()
core.quit()

#=========================================================
''' We recommend 10 practice trials before the first prosaccade block, and 4 before the first anti- 
saccade block, those data being discarded, and feedback being pro- 
vided to the subject as necessary.'''

''' 60 Prosaccades;40 antisaccades;40 antisaccades;40 antisaccades; 60 prosaccades 
There should be a break of 1 min between each block; with 
automated recording this total of 240 trials should take significantly less than the target of 20 min overall'''




