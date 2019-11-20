1# -*- coding: utf-8 -*-
"""
Created on Wed Sep  5 15:45:41 2018

@author: Marcus

A number of short test you can run and look at plots of your eye movements data.

Before running
1) Change the 'et_name' below to the eye tracker model you are using.
2) Make sure the monitor settings (in 'mon') are aligned with your specific setup.
Then select from the drop down menu which task you want to run. Data will be presented 
immediately after the recording is done.
"""

from psychopy import visual, event, core, gui, monitors
from psychopy.tools.monitorunittools import cm2deg

import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import pandas as pd
import random
import sys


# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)
sys.path.insert(0, os.path.dirname(_thisDir))


plt.close('all')
print(os.getcwd())

# Set parameters
eye_tracking = True
et_name = 'Tobii Pro Spectrum'
dummy_mode = False


from titta import Titta, helpers_tobii as helpers    
import tobii_research as tr

 
#%% 
def plot_et_data(df, plot_type = 'xy'):
    ''' Plots eye-tracker data as xy or xy over time.
    
    Args:
        df - pandas dataframe with eye-tracking data 
    '''
    
    xy_l = np.array(df[['left_gaze_point_on_display_area_x',
               'left_gaze_point_on_display_area_y']])
    xy_l = helpers.tobii2deg(xy_l, settings.mon)
    
    xy_r = np.array(df[['right_gaze_point_on_display_area_x',
               'right_gaze_point_on_display_area_y']])
    xy_r = helpers.tobii2deg(xy_r, settings.mon)
    
    if plot_type == 'xy':
        plt.plot(xy_l[:, 0], 
                 xy_l[:, 1], '.', ms=2, c='r', label='Left eye')
        plt.plot(xy_r[:, 0], 
                 xy_r[:, 1], '.', ms=2, c='b', label='Right eye')
        plt.xlabel('Horizontal gaze coordinate (deg)')
        plt.ylabel('Vertical gaze coordinate (deg)')   
        plt.legend()
        
        axis_deg = helpers.tobii2deg(np.array([[0.99, 0.99]]), settings.mon).flatten()
        plt.axis([-axis_deg[0], axis_deg[0], -axis_deg[1], 
                  axis_deg[1]])  
        plt.gca().invert_yaxis()    
    else:
        tt =  np.array(df['system_time_stamp'])
#        print(tt)
        tt =   (tt - tt[0]) / 1000.0 / 1000.0        
        plt.plot(tt, 
                 xy_r[:, 0], '-', label='Horizontal gaze coordinate (right eye)')
        plt.plot(tt, 
                 xy_r[:, 1], '-', label='Vertical gaze coordinate (right eye)')         
        plt.xlabel('Time (s)')
        plt.legend()
        plt.ylabel('Horizontal/vertical gaze coordinate (deg)')       
    #plt.show()
        
    
#%%
def read_et_data():
    ''' Read eye tracking data from the buffer
    
    Returns:
        df - pandas dataframe
    '''
    df = pd.DataFrame(tracker.gaze_data_container, columns=tracker.header)
    df.reset_index()
    
    return df

 
    
#%%
def display_fixation_cross(pos = (0, 0), duration=1):
    ''' Display cue before stim onset
    '''
    dot.pos = pos
    dot.draw()
    win.flip()
    core.wait(duration)
        
#%%
def display_cue(pos):
    ''' Display cue before stim onset
    '''
    dot.pos = pos
    for i in range(3):
        core.wait(0.2)
        dot.draw()
        win.flip()
        core.wait(0.2)
        win.flip()
        
#%%
def sinusoid_pursuit(nCycles=1, cps=1, amp=1, show_results=False, blank_screen=False):
    ''' Shows a dot that follows a sinusoidal movement from left to right
    '''
    
    # Show instruction
    ins = 'Follow the dot \n(Press space to start).'
    if blank_screen:
        ins = 'Imagine a dot moving across the screen. Follow the imagined movement \n(Press space to start)'
        
        
    instruction_text.setText(ins) # "Stare" nystagmus
    instruction_text.draw()
    win.flip()
    k = event.waitKeys()
    if k[0] == 'q':
        win.close()
        core.quit()
    
    screen_fs = win.getActualFrameRate()
    
    # Construct the trajectory
    t = np.arange(-0.8, 0.8, 2 * 1.0/screen_fs * float(cps)) 
    y = -amp*np.sin(nCycles / 2.0* 2*np.pi*t)
    
    
    display_cue((t[0], y[0]))

    #print(screen_fs, len(t))
    
    if eye_tracking:
        tracker.start_recording(gaze_data=True)
        tracker.gaze_data_container = [] # Remove calibration/validation data

        
    for i in range(len(t)):
#        print(t, y)
        dot.pos = (t[i], y[i])
        if blank_screen:
            pass
        else:
            dot.draw()
        win.flip()
        
        key = event.getKeys()
        if 'escape' in key:
            win.close()
            core.quit()
            
    if eye_tracking:
        tracker.stop_recording(gaze_data=True)            
#        tracker.save_data()
            
    if eye_tracking and show_results:
        win.close()
        # Read et data and plot (xy, xt, yt, + stim)
        # Plot results
        df = read_et_data()
        
        # Create a figure and put it on the left side
        plt.figure()
        plt.subplot(2, 1, 1)
        # fig, ax = plt.subplots()
        # mngr = plt.get_current_fig_manager()
        # mngr.window.setGeometry = (mon.getSizePix()[0] / 2.0 - mon.getSizePix()[0] / 4.0, 
        #                            mon.getSizePix()[1] / 2.0, 
        #                            mon.getSizePix()[0] / 4.0, 
        #                            mon.getSizePix()[1] / 4.0)

        p = np.vstack((t, y))
        pos_norm =  helpers.norm2tobii(p.T)   
        pos_norm = helpers.tobii2deg(pos_norm, settings.mon)
        
        plt.plot(pos_norm[:, 0], pos_norm[:, 1], '-', c='k', 
                 label='Stimulus (dot) position')
        
        plot_et_data(df, plot_type = 'xy')        
        
        
        # Gaze over time
        plt.subplot(2, 1, 2)
        # mngr = plt.get_current_fig_manager()
        # mngr.window.setGeometry = (mon.getSizePix()[0] / 2.0 + mon.getSizePix()[0] / 4.0, 
        #                            mon.getSizePix()[1] / 2.0, 
        #                            mon.getSizePix()[0] / 4.0, 
        #                            mon.getSizePix()[1] / 4.0)       

        
        # Plot dot location
        tt =  np.array(df['system_time_stamp'])
        tt =   (tt - tt[0]) / 1000.0 / 1000.0
        ta = np.linspace(tt.min(), tt.max(), len(pos_norm))
        # plt.plot(ta, pos_norm[:, 0], '-', c='k')
        plt.plot(ta, np.array(pos_norm[:, 1]), '-', c='k',
                 label='Stimulus (dot) position')
        
        plot_et_data(df, plot_type = 'tx')
        plt.show()
        
        
#%% 
def present_dots(dot_positions, duration=1, show_results=False):
    '''
    Args:
        dot_positions - list of dot locations [[x, y], [x, y],...]
    '''            
    
    ins = 'Look at the dot(s) \n(Press space to start).'
    instruction_text.setText(ins) # "Stare" nystagmus
    instruction_text.draw()
    win.flip()
    k = event.waitKeys()
    if k[0] == 'q':
        win.close()
        core.quit()
            
    if eye_tracking:
        tracker.start_recording(gaze_data=True)
        tracker.gaze_data_container = [] # Remove calibration/validation data

        
    for dot_position in dot_positions:
        dot.pos = dot_position
        dot.draw()
        win.flip()
        core.wait(duration)
        
        key = event.getKeys()
        if 'escape' in key:
            win.close()
            core.quit()        
            
    
    if eye_tracking:
        tracker.stop_recording(gaze_data=True)  

    win.flip()
    if eye_tracking and show_results:
        df = read_et_data()
        tt =  np.array(df['system_time_stamp'])
        tt =   (tt - tt[0]) / 1000.0 / 1000.0
        
        
        win.close()
        
        # xy-plot
        plt.figure()
        #print(dot_positions)
        dot_positions = helpers.norm2tobii(np.array(dot_positions))  
        dot_positions = helpers.tobii2deg(dot_positions, settings.mon)
        plt.plot(dot_positions[:, 0],
                 dot_positions[:, 1], 'o', ms=10, label='Stimulus dots')
        plot_et_data(df, plot_type = 'xy')
        
        # tx, ty plot
        plt.figure()
#        ta = np.linspace(tt.min(), tt.max(), len(dot_positions))
        s = len(tt) / len(dot_positions)
        m = np.min([len(tt), len(dot_positions[:, 0].repeat(s))])
        #print(s, m, tt[:m], dot_positions[:, 0].repeat(s, axis=0)[:m])
        plt.plot(tt[:m], dot_positions[:, 0].repeat(s, axis=0)[:m], 
                 label='Stimulus (dot) position')
#        m = np.min([len(tt), len(dot_positions[:, 1].repeat(s))])        
#        plt.plot(tt, dot_positions[:, 1].repeat(s, axis=0)[:m])
        plot_et_data(df, plot_type = 'tx')
        plt.show()
        
            

        
#%% OKN
def okn(temporal_frequency,okn_dur,screen_Fs,direction='R',show_instruction=True):
    '''
    OKN-stim
    '''
        
    if 'R' in direction or 'L' in direction:
        okn_stim.setOri(0)
    else:
        okn_stim.setOri(90)
        
        
    # First show instructions for the task and then wait for key response
    if show_instruction:
        ins = 'Look in the center of the screen \n(Press space to start).'
        instruction_text.setText(ins) # "Stare" nystagmus
        instruction_text.draw()
        win.flip()
        k = event.waitKeys()
        if k[0] == 'q':
            win.close()
            core.quit()
        
    t = core.getTime()  
    t_diff = core.getTime() - t
    i = 0                   
    
    # Start eye tracker
    if eye_tracking:
        tracker.start_recording(gaze_data=True)
        tracker.gaze_data_container = [] # Remove calibration/validation data

        
    while t_diff < okn_dur:
#        print(i)
        if 'R' in direction:
            okn_stim.setPhase((i,0))
            i+=temporal_frequency/screen_Fs 
        elif 'L' in direction:
            okn_stim.setPhase((i,0))
            i-=temporal_frequency/screen_Fs 
        elif 'U' in direction:
            okn_stim.setPhase((i,0))
            i-=temporal_frequency/screen_Fs  
        else:
            okn_stim.setPhase((i,0))
            i+=temporal_frequency/screen_Fs                   
            
        okn_stim.draw()
        win.flip()
        t_diff = core.getTime() - t
         
#        # Interrupt if someoone presses escape
#        k = event.getKeys(keyList = ['q'])
#        if k:
#            end_session()        
            
    # Stop eye tracker
    if eye_tracking:
        tracker.stop_recording(gaze_data=True)              
        
        df = read_et_data()
        tt =  np.array(df['system_time_stamp'])
        tt =   (tt - tt[0]) / 1000.0 / 1000.0
        
        
        win.close()
        
        # xy-plot
        plt.figure()
        plot_et_data(df, plot_type = 'xy')    
        
        # xy-plot
        plt.figure()
        plot_et_data(df, plot_type = 't')    
        plt.show()


        
#%%
def stim_slideshow(fname, stim_type = 'text', 
                   duration=1, show_results=False):
    ''' Displays image stimuli in the folder 'fname'
    if fname is not a folder, a single image is displayed
    '''
    
    if 'image' in stim_type:
        ins = 'Explore the image \n(Press space to start).'
    else:
        ins = 'Read the text carefully. Press space when done reading \n(Press space to start).'
        
    instruction_text.setText(ins) # 
    instruction_text.draw()
    win.flip()
    k = event.waitKeys()
    if k[0] == 'q':
        win.close()
        core.quit()
        
    if os.path.isdir(fname):
        # List pictures
        stimnames = glob.glob(fname)
        
    else:
        stimnames = [fname]
    
    # preload pictures
    im = []
    for stim in stimnames:
        temp_im = visual.ImageStim(win, image=stim, 
                                   units='norm', size=(1, 1))
        temp_im.size *= [2, 2]     # For full screen      
        im.append(temp_im)
        
        
    if eye_tracking:
        tracker.start_recording(gaze_data=True)
        tracker.gaze_data_container = [] # Remove calibration/validation data

        
    # Show pictures
    for i in range(len(im)):
        im[i].draw()
        win.flip()
        if not duration:
            event.waitKeys()
        else:
            core.wait(duration)
               
        key = event.getKeys()
        if 'escape' in key:
            win.close()
            core.quit()
            
    win.flip()
    
    if eye_tracking:
        tracker.stop_recording(gaze_data=True)          
    
    if eye_tracking and show_results:
        df = read_et_data()
        im[i].draw()

        x_old = 0
        y_old = 0
        k = 0
        for index, row in df.iterrows():
            #print(index) 

            p = np.array([[row['left_gaze_point_on_display_area_x'],
                 row['left_gaze_point_on_display_area_y']]])
            pos_norm =  helpers.tobii2norm(p)   
            et_sample.pos = (pos_norm[0][0], pos_norm[0][1])
            et_sample.draw()
            
            if k > 0:
                et_line.start=(x_old, y_old)
                et_line.end = (pos_norm[0][0], pos_norm[0][1])
                et_line.draw()
                
            x_old = pos_norm[0][0]
            y_old = pos_norm[0][1]
        
            k += 1
        win.flip()
        
        event.waitKeys()        
                
            
#%% Start of lab

# Select task
myDlg = gui.Dlg(title="EM tests")
# myDlg.addField('Task', choices=["Pursuit","Pursuit (blank screen)", "Static dots",
#                                 "images", "text", "okn"])
    
myDlg.addField('Task', choices=["1. Static dots",
                                "2. Images", 
                                "3. Text",
                                "4. Pursuit",
                                "5. Pursuit (blank screen)",
                                "6. OKN",
                                "7. Long fixation"])
    
ok_data = myDlg.show()  # show dialog and wait for OK or Cancel
if myDlg.OK:  # or if ok_data is not None
    print(ok_data)
else:
    print('user cancelled')
    
        
# Sp parameters
amp = 0.8
nCycles = 2
cps = 0.2
pos = (-0.8, -amp*np.sin(nCycles / 2.0* 2*np.pi*-0.8))

stim_duration = 5

dot_positions_x = [-0.8, -0.4, 0, 0.4, 0.8]
dot_positions_y = [0,0,0,0,0]
random.shuffle(dot_positions_x)
dot_positions = list(zip(dot_positions_x, dot_positions_y))

#print(dot_positions)    
#random.shuffle(dot_positions)    
#print(dot_positions)

#%% Monitor/geometry 
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = True
SCREEN_RES                  = [1920, 1080]
SCREEN_WIDTH                = 52.7 # cm
SCREEN_HEIGHT               = 30.0 # cm
VIEWING_DIST                = 63 #  # distance from eye to center of screen (cm)

mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)


# Change any of the default dettings?
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile.tsv'
settings.mon = mon
settings.SCREEN_HEIGHT = SCREEN_HEIGHT


                    

# Connect to eye tracker
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()
tracker.init()

win = visual.Window(monitor = mon, fullscr = FULLSCREEN,
                    screen=1, size=SCREEN_RES, units = 'deg')
                    
win.size = SCREEN_RES      
print(win.size, SCREEN_RES)
tracker.calibrate(win)

  

dot = visual.Circle(win, radius = 0.01, fillColor='red', lineColor='white',
                    units='norm')
et_sample = visual.Circle(win, radius = 0.005, fillColor='red', lineColor='white',
                    units='norm')
text = visual.TextStim(win)
et_line = visual.Line(win, units='norm')
okn_stim = visual.GratingStim(win, color='black', tex='sqr',
                         sf = (0.5,0), mask=None,size=60)
instruction_text = visual.TextStim(win,color='black',text='',wrapWidth = 20,height = 1)
                         


## Show instructions
#text.setText('Press space to start')
#text.draw()
#win.flip()
#event.waitKeys()


if '4. Pursuit' in myDlg.data[0]:
#    display_cue(pos)
    sinusoid_pursuit(nCycles=nCycles, cps=cps, amp=amp, show_results=True, blank_screen=False)   
elif '5. Pursuit' in myDlg.data[0]:
#    display_cue(pos)
    sinusoid_pursuit(nCycles=nCycles, cps=cps, amp=amp, show_results=True, blank_screen=True)       
elif 'Static dots' in myDlg.data[0]:
    present_dots(dot_positions, duration=1, show_results=True)    
elif 'fixation' in myDlg.data[0]:
    present_dots([[0, 0]], duration=20, show_results=True)        
elif 'Images' in myDlg.data[0]:
    # display_fixation_cross()
    files = glob.glob(os.getcwd() + os.sep + 'images' + os.sep + '*.bmp')
    random.shuffle(files)
    stim_slideshow(files[0], duration=stim_duration, show_results=True, 
                   stim_type = 'image')    
elif 'Text' in myDlg.data[0]:
    # display_fixation_cross()
    files = glob.glob(os.getcwd() + os.sep + 'texts' + os.sep + '*.png')
    random.shuffle(files)
    stim_slideshow(files[0], duration=None, show_results=True,
                   stim_type = 'text')    
else:   
    temporal_frequency = 5.0
    okn_dur = 5
    screen_Fs = 60.0
    
    okn(temporal_frequency,okn_dur,screen_Fs,direction='R',show_instruction=True)
    
 

plt.close('all')
    
# Stop eye tracker and clean up 
if eye_tracking:
    #tracker.stop_sample_buffer()
    tracker.stop_recording(gaze_data=True)
    tracker.de_init()    
#win.close()
#core.quit()


        
        
    
    
    