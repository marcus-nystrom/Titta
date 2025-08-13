# -*- coding: utf-8 -*-

'''
To run this demo,
1) open a new External Presenter in Tobii Pro Lab
2) navigate to the 'record'-tab in Pro Lab
3) Make sure the External presenter button is red and says 'not connected'
4) run this script

Data can after the recording be viewed in Pro Lab under the Analyze tab.
'''

# Import modules
from psychopy import visual, monitors, core
from titta import Titta, helpers_tobii as helpers
from titta.TalkToProLab import TalkToProLab
import random

#%% Monitor/geometry
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = True
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
project_name = None # None or a project name that is open in Pro Lab.
                    # If None, the currently opened project is used.

# Change any of the default settings?
settings = Titta.get_defaults(et_name)
settings.FILENAME = '11'

# Participant ID and Project name for Lab
pid = settings.FILENAME


#%% Connect to eye tracker and calibrate (you need to do this outside of lab)
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()
tracker.init()


#%% Talk to Pro Lab
ttl = TalkToProLab(project_name=project_name,
                   dummy_mode=dummy_mode)
participant_info = ttl.add_participant(pid)

try:
    # Window set-up (this color will be used for calibration)
    win = visual.Window(monitor = mon, fullscr = FULLSCREEN,
                        screen=1, size=SCREEN_RES, units = 'deg')

    image = visual.ImageStim(win, image='im1.jpeg', units='norm', size = (2, 2))
    text = visual.TextStim(win, text='', height=1)
    # Create psychopy image objects and upload media to Lab
    # Make sure the images have the same resolution as the screen
    im_names = ["im1.jpeg", "im2.jpeg", "im3.jpeg"]
    img = []
    media_info = []
    for im_name in im_names:
        img.append(visual.ImageStim(win, image = im_name, name=im_name))

        # Upload media (if not already uploaded)
        if not ttl.find_media(im_name):
            media_info.append(ttl.upload_media(im_name, "image"))
            print(f'Uploaded media {im_name}')

    # If the media were uploaded already, just get their names and IDs.
    if len(media_info) == 0:
        print('Media already exist. Get names and IDs')
        uploaded_media = ttl.list_media()['media_list']
        for im_name in im_names:

            # Store media information in list
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

    # Randomize image presentation order
    random.shuffle(img)

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

        # Get media id for this image
        for m in media_info:
            if im.name[:-5] == m['media_name']:
                media_id = m['media_id']
                break

        if i == len(img) - 1:

            # Send a message indicating what stimulus is shown
            ttl.send_stimulus_event(rec['recording_id'],
                                    str(t_onset),
                                    media_id,
                                    end_timestamp = str(t_offset))
        else:
            # Send a message indicating what stimulus is shown
            ttl.send_stimulus_event(rec['recording_id'],
                                    str(t_onset),
                                    media_id)

except Exception as e:
    print(e)
    win.close()

## Stop recording
ttl.stop_recording()
win.close()

#%% Finalize the recording
# Finalize recording
ttl.finalize_recording(rec['recording_id'])
ttl.disconnect()
