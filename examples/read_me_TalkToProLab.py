# -*- coding: utf-8 -*-

# Import modules
from psychopy import visual, monitors, core, event
import numpy as np
import os, sys
  
# Insert the parent directory (where Titta is) to path
curdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(curdir)
sys.path.insert(0, os.sep.join([os.path.dirname(curdir), 'Titta'])) 
import Titta
import helpers_tobii as helpers
from TalkToProLab import TalkToProLab

#%% Monitor/geometry 
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = False
SCREEN_RES                  = [1920, 1080]
SCREEN_WIDTH                = 52.7 # cm
VIEWING_DIST                = 63 #  # distance from eye to center of screen (cm)

mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)


    
#%% ET settings
et_name = 'Tobii Pro Spectrum' 
# et_name = 'IS4_Large_Peripheral' 
# et_name = 'Tobii Pro Nano' 

dummy_mode = False
     
# Change any of the default settings?
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'P007.tsv'

# Participant ID and Project name for Lab
pid = settings.FILENAME[:-4]
project_name = 'Project75'


#%% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()
tracker.init()
   

#%% Talk to Pro Lab  
ttl = TalkToProLab()

# Get project name and make sure the same project is open in Lab
assert project_name == ttl.get_project_info()['project_name'], "Wrong project opened in Lab. Should be {}".format(project_name)


# Make sure that the participant id does not already exist in Lab
assert not ttl.find_participant(pid), "Participant {} already exists in Lab".format(pid)
participant_info = ttl.add_participant(pid)
    
    
try:
    # Window set-up (this color will be used for calibration)
    win = visual.Window(monitor = mon, fullscr = FULLSCREEN,
                        screen=1, size=SCREEN_RES, units = 'deg')
    
    fixation_point = helpers.MyDot2(win)
    image = visual.ImageStim(win, image='im1.jpeg', units='norm', size = (2, 2))
    text = visual.TextStim(win, text='', height=1)       
    # Create psychopy image objects and upload media to Lab                                          
    # Make sure the images have the same resolution as the screen  
    im_names = ["im1.jpeg", "im2.jpeg", "im3.jpeg"]
    img = []    
    media_info = []                                        
    for im_name in im_names:
        img.append(visual.ImageStim(win, image = im_name))
        if not ttl.find_media(im_name):  
            media_info.append(ttl.upload_media(im_name, "image"))
    
    # If the media were uploaded already, just get their names and IDs.
    if len(media_info) == 0:
        uploaded_media = ttl.list_media()['media_list']
        for im_name in im_names:
            
            # Make sure they are in the same order as the 'im_names'
            for m in uploaded_media:
                if im_name[:-5] == m['media_name']:
                    media_info.append(m)
                    break
        
    # Add an AOI to the first image
    aoi_name = 'test'
    aoi_color =  'AAC333'
    vertices = ((100, 100),
                          (100, 200), 
                          (200, 200),
                          (200, 100))
    tag_name = 'test_tag'
    group_name = 'test_group'
    ttl.add_aois_to_image(media_info[0]['media_id'], aoi_name, aoi_color, 
                          vertices, tag_name=tag_name, group_name=group_name)    
    
    # Calibrate (must be done independent of Lab)
    tracker.calibrate(win)
    win.flip()
    
    #%% Recording 
    
    # Check that Lab is ready to start a recording
    state = ttl.get_state()
    assert state['state'] == 'ready', state['state']
    
    ## Start recording (Note: you have to click on the Record Tab first!)
    rec = ttl.start_recording("image_viewing", 
                        participant_info['participant_id'], 
                        screen_width=1920,
                        screen_height=1080)
    
    # Show images. Note: there cannot be any gaps between stimuli on the timeline
    dur = 3
    for i, im in enumerate(img):
        
        # Draw the image and flip it onto the screen
        im.draw()
        win.flip()
        
        timestamp = ttl.get_time_stamp()
        t_onset = int(timestamp['timestamp'])    
        
        # Display the image for 3 seconds (use dur in frames for more accurate 
        # presentation times)
        core.wait(dur)
    
        timestamp = ttl.get_time_stamp()
        t_offset = int(timestamp['timestamp'])
        
    
        if i == len(img) - 1:
            
            # Send a message indicating what stimulus is shown
            ttl.send_stimulus_event(rec['recording_id'], 
                                    str(t_onset), 
                                    media_info[i]['media_id'],
                                    end_timestamp = str(t_offset)) 
        else:
            # Send a message indicating what stimulus is shown
            ttl.send_stimulus_event(rec['recording_id'], 
                                    str(t_onset), 
                                    media_info[i]['media_id'])   
        
except Exception as e: 
    print(e)
    win.close()

## Stop recording
ttl.stop_recording()
win.close()

#%% Finalize the recording
# Finalize recording
ttl.finalize_recording(rec['recording_id'])
