#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
To run the antisaccade demo:
    * Open an External Presenter project in Tobii Pro Lab. Go to the Record tab.
    * Run anti_saccades.py (this script). The first time you run it, set
      upload_stimuli = True (see below), to upload relevant stimuli to lab.
      You only need to upload stimuli once. The second time you run anti_saccades.py
      set upload_stimuli to False, otherwise an error will appear.

'''



from psychopy import visual, core, data, event, monitors, gui
from random import randint, uniform
import numpy as np
from psychopy import logging
from titta import Titta, helpers_tobii as helpers
from titta.TalkToProLab import TalkToProLab

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
                 upload_media=False,
                 pid=None,
                 project_name = None):

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
        self.upload_media = upload_media

        # Target durations in frames
        self.duration_central_target = np.round(duration_central_target * screen_refresh_rate)
        self.duration_peripheral_target = duration_peripheral_target * screen_refresh_rate

        #Initialize stimuli used in experiment
        self.dot_stim = helpers.MyDot2(win=win, units='deg', outer_diameter=1,
                                       inner_diameter=0.2)
        self.et_sample = visual.GratingStim(win, color='black', tex=None, mask='circle',units='pix',size=2)
        self.line = visual.Line(win, start=(-0.5, -0.5), end=(0.5, 0.5), units='pix')
        self.instruction_text = visual.TextStim(win,text='',wrapWidth = 10,height = 0.5)


        # Connect to Pro Lab and add participant
        if pro_lab_integration:
            self.ttl = TalkToProLab(project_name) # Connect to Lab

            participant_info = self.ttl.add_participant(pid)

            if upload_media:
                self.upload_stimuli()
            else:
                # Collect information about the already uploaded stimuli
                self.stim_info = {}
                uploaded_media = self.ttl.list_media()['media_list']
                for m in uploaded_media:
                    self.stim_info[m['media_name']] = m['media_id']

        # Calibrate eye tracker
        tracker.calibrate(win)

        # Start recording in Lab
        if pro_lab_integration:
            self.rec = self.ttl.start_recording("antisaccade",
                    participant_info['participant_id'],
                    screen_width=self.screen_size[0],
                    screen_height=self.screen_size[1])



    #%%
    def screenshot_and_upload(self, im_name, im_type):
        ''' Takes a screenshot of the backbuffer and uploads media to Pro Lab

        '''

        win.getMovieFrame(buffer='back')
        win.saveMovieFrames(im_name)
        media_info = self.ttl.upload_media(im_name, im_type)
        self.stim_info[im_name[:-4]] = media_info['media_id']

        return media_info

    #%%
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

        self.instruction_text.setText("Uploading media to Lab. Please wait.") # and then a break
        self.instruction_text.draw()
        self.win.flip()


        self.stim_info = {} # Dict to keep track of media id for each stimulus


        # General settings
        aoi_color_left =  'AAC333'
        aoi_color_right = 'FFD700'
        vertices_left = ((0, 0),
                         (self.screen_size[0]/2.0 - 100, 0),
                         (self.screen_size[0]/2.0 - 100, self.screen_size[1]),
                         (0, self.screen_size[1]))

        vertices_right = ((self.screen_size[0]/2.0 + 100, 0),
                          (self.screen_size[0], 0),
                          (self.screen_size[0], self.screen_size[1]),
                          (self.screen_size[0]/2.0 + 100, self.screen_size[1]))

        im_type = 'image'

        ######### Upload stimulus for central fixation cross
        im_name = 'central_fixation.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        self.dot_stim.set_pos((0,0))
        self.dot_stim.draw()
        self.screenshot_and_upload(im_name, im_type)
        self.win.clearBuffer()

        ######### Upload stimulus for pro-saccade (target to left)
        # for corrent (left) and incorrect (right) aois
        im_name = 'prosaccade_left.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        self.dot_stim.set_pos((-self.saccade_amplitude,0))
        self.dot_stim.draw()
        media_info = self.screenshot_and_upload(im_name, im_type)
        aoi_name = 'left'
        tag_name = 'correct'
        group_name = 'prosaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color_left,
                              vertices_left, tag_name=tag_name, group_name=group_name)

        aoi_name = 'right'
        tag_name = 'incorrect'
        group_name = 'prosaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color_right,
                              vertices_right, tag_name=tag_name, group_name=group_name)
        self.win.clearBuffer()


        ######### Upload stimulus for pro-saccade (target to right)
        # for corrent (right) and incorrect (left) aois
        im_name = 'prosaccade_right.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        self.dot_stim.set_pos((self.saccade_amplitude,0))
        self.dot_stim.draw()
        media_info = self.screenshot_and_upload(im_name, im_type)
        aoi_name = 'right'
        tag_name = 'correct'
        group_name = 'prosaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color_right,
                              vertices_right, tag_name=tag_name, group_name=group_name)

        aoi_name = 'left'
        tag_name = 'incorrect'
        group_name = 'prosaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color_left,
                              vertices_left, tag_name=tag_name, group_name=group_name)
        self.win.clearBuffer()


        ######### Upload stimulus for anti-saccade (target to left)
        # for corrent (left) and incorrect (right) aois
        im_name = 'antisaccade_left.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        self.dot_stim.set_pos((-self.saccade_amplitude,0))
        self.dot_stim.draw()
        media_info = self.screenshot_and_upload(im_name, im_type)
        aoi_name = 'left'
        tag_name = 'incorrect'
        group_name = 'antisaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color_left,
                              vertices_left, tag_name=tag_name, group_name=group_name)

        aoi_name = 'right'
        tag_name = 'correct'
        group_name = 'antisaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color_right,
                              vertices_right, tag_name=tag_name, group_name=group_name)
        self.win.clearBuffer()

        ######### Upload stimulus for pro-saccade (target to right)
        # for corrent (right) and incorrect (left) aois
        im_name = 'antisaccade_right.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        self.dot_stim.set_pos((self.saccade_amplitude,0))
        self.dot_stim.draw()
        media_info = self.screenshot_and_upload(im_name, im_type)
        aoi_name = 'right'
        tag_name = 'incorrect'
        group_name = 'antisaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color_right,
                              vertices_right, tag_name=tag_name, group_name=group_name)

        aoi_name = 'left'
        tag_name = 'correct'
        group_name = 'antisaccade'

        self.ttl.add_aois_to_image(media_info['media_id'], aoi_name, aoi_color_left,
                              vertices_left, tag_name=tag_name, group_name=group_name)
        self.win.clearBuffer()


        ######### Upload stimulus prosaccade trial instruction
        im_name = 'pro_instruction_test.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        ins = self.pro_instr+'\n\n' + self.keypress_test
        self.instruction_text.setText(ins)
        self.instruction_text.draw()
        media_info = self.screenshot_and_upload(im_name, im_type)
        self.win.clearBuffer()

        ######### Upload stimulus prosaccade exp instruction
        im_name = 'pro_instruction_exp.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        ins = self.pro_instr+'\n\n' + self.keypress_exp
        self.instruction_text.setText(ins)
        self.instruction_text.draw()
        media_info = self.screenshot_and_upload(im_name, im_type)
        self.win.clearBuffer()


        ######### Upload stimulus antisaccade trial instruction
        im_name = 'anti_instruction_test.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        ins = self.anti_instr+'\n\n' + self.keypress_test
        self.instruction_text.setText(ins)
        self.instruction_text.draw()
        media_info = self.screenshot_and_upload(im_name, im_type)
        self.win.clearBuffer()


        ######### Upload stimulus prosaccade exp instruction
        im_name = 'anti_instruction_exp.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        ins = self.anti_instr+'\n\n' + self.keypress_exp
        self.instruction_text.setText(ins)
        self.instruction_text.draw()
        media_info = self.screenshot_and_upload(im_name, im_type)
        self.win.clearBuffer()


        ######### Upload break instruction
        im_name = 'break_instruction.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        break_instruction = ' '.join([self.break_instruction_s,
                                      str(5),
                                      self.break_instruction_e])
        self.instruction_text.setText(break_instruction) # and then a break
        self.instruction_text.draw()
        media_info = self.screenshot_and_upload(im_name, im_type)
        self.win.clearBuffer()


        ######### Goodbye message
        im_name = 'goodbye_instruction.png'
        assert not self.ttl.find_media(im_name), "Media {} already exists in Lab".format(im_name)
        self.instruction_text.setText(self.goodByeMessage) # and then a break
        self.instruction_text.draw()
        media_info = self.screenshot_and_upload(im_name, im_type)

        self.win.clearBuffer()


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

            timestamp = int(self.ttl.get_time_stamp()['timestamp'])
            self.ttl.send_stimulus_event(self.rec['recording_id'],
                                         str(timestamp),
                                         m_info)

        event.waitKeys()

        self.run_trials(nTrials, 'anti', practice=practice)
    #%%
    def run_trials(self, nTrials, task, practice=False):
        '''
        '''

        # Start eye tracker
        if self.eye_tracking:
            self.tracker.start_recording(gaze=True)

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
                    timestamp = int(self.ttl.get_time_stamp()['timestamp'])
                    self.ttl.send_stimulus_event(self.rec['recording_id'],
                                                 str(timestamp),
                                                 self.stim_info["central_fixation"])

            # Display the peripheral dot
            self.dot_stim.set_pos((sa,0))
            self.dot_stim.draw()
            self.win.flip()

            if self.pro_lab_integration:
                if 'anti' in task:
                    timestamp = int(self.ttl.get_time_stamp()['timestamp'])
                    if sa < 0:
                        self.ttl.send_stimulus_event(self.rec['recording_id'],
                                                     str(timestamp),
                                                     self.stim_info['antisaccade_left'])
                    else:
                        self.ttl.send_stimulus_event(self.rec['recording_id'],
                                                     str(timestamp),
                                                     self.stim_info['antisaccade_right'])
                else:
                    if sa < 0:
                        self.ttl.send_stimulus_event(self.rec['recording_id'],
                                                     str(timestamp),
                                                     self.stim_info['prosaccade_left'])
                    else:
                        self.ttl.send_stimulus_event(self.rec['recording_id'],
                                                     str(timestamp),
                                                     self.stim_info['prosaccade_right'])
            if self.eye_tracking:

                # If practice trial, show feedback
                if practice:

                    self.tracker.send_message('_'.join(['START_TRIAL_PRACTICE', task, str(sa), str(i)]))
                    self.trialClock.reset()
                    t = 0
                    iSample = 0
                    nSampleToCollect = np.round(self.Fs * self.duration_peripheral_target / self.screen_refresh_rate)

                    xy = np.empty([int(nSampleToCollect),2])

                    while t < (self.duration_peripheral_target / float(self.screen_refresh_rate)) and iSample < nSampleToCollect:
                        t = self.trialClock.getTime()

                        # Get et sample and convert to pixels
                        sample = self.tracker.buffer.peek_N('gaze', 1)

                        x_mean = np.nanmean([sample['left_gaze_point_on_display_area_x'],
                                          sample['right_gaze_point_on_display_area_x']])
                        y_mean = np.nanmean([sample['left_gaze_point_on_display_area_y'],
                                          sample['right_gaze_point_on_display_area_y']])

                        pos = helpers.tobii2pix(np.array([[x_mean, y_mean]]), self.win)

                        xy[iSample,0] = pos[:, 0]
                        xy[iSample,1] = pos[:, 1]

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
                    if ('pro' in task and sa > 0 and np.nansum(xy[:,0] < -self.screen_size[0]/16)     > nSamples) or \
                       ('pro' in task and sa < 0 and np.nansum(xy[:,0] >  self.screen_size[0]/16)      > nSamples) or \
                       ('anti' in task and sa < 0 and np.nansum(xy[:,0] < -self.screen_size[0]/16)    > nSamples) or \
                       ('anti' in task and sa > 0 and np.nansum(xy[:,0] > self.screen_size[0]/16)     > nSamples):
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
            self.tracker.stop_recording(gaze=True)

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
            timestamp = int(self.ttl.get_time_stamp()['timestamp'])
            self.ttl.send_stimulus_event(self.rec['recording_id'],
                                         str(timestamp),
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

        if self.pro_lab_integration:
            timestamp = int(self.ttl.get_time_stamp()['timestamp'])
            self.ttl.send_stimulus_event(self.rec['recording_id'],
                                         str(timestamp),
                                         self.stim_info['goodbye_instruction'],
                                         end_timestamp = str(timestamp + waitdur * 1000000))

        core.wait(waitdur)

        # Finalize recording
        if self.pro_lab_integration:
            ## Stop recording
            self.ttl.stop_recording()
            self.ttl.finalize_recording(self.rec['recording_id'])
            self.ttl.disconnect()

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
pro_lab_project_name = None                # Specific project name. 'None' means
                                           # the the currently opened project is used.
upload_stimuli = True                      # Set to True only the first time you run

# Monitor/geometry
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = False
SCREEN_RES                  = [1920, 1080]
SCREEN_WIDTH                = 52.7          # cm
VIEWING_DIST                = 63            # distance from eye to center of screen (cm)

# Eye tracker
et_name = 'Tobii Pro Spectrum'
# et_name = 'IS4_Large_Peripheral'
dummy_mode = False                          # Run eye tracker in dummy mode

# Antisaccade parameters
saccade_amplitude = 8
duration_central_target = foreperiod_central_fixation(numel=1000,
                                                      mu = 1.5,
                                                      interval = [1, 3.5])
duration_peripheral_target = 1

# Ask user for participant ID
expName = 'Antisaccades'
expInfo={'participant':'01'}
dlg=gui.DlgFromDict(dictionary=expInfo,title=expName)
if dlg.OK==False:
    core.quit() #user pressed cancel

mon = monitors.Monitor(MY_MONITOR)          # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)                  # Width of screen (cm)
mon.setDistance(VIEWING_DIST)               # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)

# Window set-up
win = visual.Window(monitor = mon, screen = 1,
                    size = SCREEN_RES,
                    units = 'deg', fullscr = FULLSCREEN,
                    allowGUI = False)

# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile.tsv'

#%% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
if dummy_mode == True:
    tracker.set_dummy_mode()
else:
    tracker.init()


# Initiate antisaccade class
try:
    sac = ProAntiSaccades(win, saccade_amplitude=saccade_amplitude,
                     duration_central_target = duration_central_target,
                     duration_peripheral_target = duration_peripheral_target,
                     screen_refresh_rate = win.getActualFrameRate(),
                     Fs = settings.SAMPLING_RATE,
                     screen_size = SCREEN_RES,
                     eye_tracking = dummy_mode==False,
                     tracker=tracker,
                     pro_lab_integration=pro_lab_integration,
                     upload_media=upload_stimuli,
                     pid = expInfo['participant'],
                     project_name=pro_lab_project_name)


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

except Exception as e:
    print(e)
    win.close()
    sac.ttl.stop_recording()
    sac.ttl.disconnect()


# Save data and close connection with eye trackers
if not dummy_mode:
    tracker.save_data()

# Close PsychoPy window
win.close()
#core.quit()

#=========================================================
''' We recommend 10 practice trials before the first prosaccade block, and 4 before the first anti-
saccade block, those data being discarded, and feedback being pro-
vided to the subject as necessary.'''

''' 60 Prosaccades;40 antisaccades;40 antisaccades;40 antisaccades; 60 prosaccades
There should be a break of 1 min between each block; with
automated recording this total of 240 trials should take significantly less than the target of 20 min overall'''




