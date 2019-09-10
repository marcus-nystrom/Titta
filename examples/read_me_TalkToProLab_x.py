# -*- coding: utf-8 -*-
"""
Created on Sat Dec  1 21:15:18 2018

@author: marcus
"""

import time
import os
import numpy as np
from psychopy import visual, core, event
from talkToLab_client import Talk2Lab

_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

# Connect
ttl = Talk2Lab()


#%% Stuff you can do before recording

# Add participant to project
participant_info = ttl.add_participant("P01")
#print(participant_info)
time.sleep(1)

# Setup PsychoPy window and screen
win = visual.Window(fullscr=True, screen=1, units='pix') # Use two screens, and show psychopy
                                            # window  on the second.
text = visual.TextStim(win, text='Switch to Record tab and press space to start the recording', 
                       height=15)                                            
  
# Create psychopy im objects and upload media to Lab                                          
# Make sure the images have the same resolution as the (second) screen  (1920, 1080)
img = []    
media_info = []                                        
for i in (np.arange(3) + 1):
    im_name = ''.join(["im", str(i), ".jpeg"])
#    print(im_name)
    img.append(visual.ImageStim(win, image= im_name))
    media_info.append(ttl.upload_media("image", im_name))
    
# Wait for the user to switch to the Record tab    
text.draw()
win.flip()    
event.waitKeys()
                                                
#%% Recording (first switch to recording tab)
# Would be nice to have it change automatically once a 'start_recording' 
# command is issued.

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
    print(t_onset, t_offset)

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
            
        

## Stop recording
timestamp = ttl.get_time_stamp()
ts = int(timestamp['timestamp'])
print(ts, t_offset)
core.wait(0.5)
ttl.stop_recording()

win.close()
core.wait(1)
print(trial_times)
#%% Finalize the recording
# Finalize recording
ttl.finalize_recording(rec['recording_id'])
