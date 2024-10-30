# Import relevant modules
from psychopy import visual, monitors, core, event
import numpy as np
from titta import Titta, helpers_tobii as helpers
import TittaLSLPy
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream
import os
import socket

# Set path to location where scrip-file is
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# 26 colors from The Colour Alphabet Project suggested by Paul Green-Armytage
# designed for use with white background:
dot_col = (240,163,255),(0,117,220),(153,63,0),(76,0,92),(25,25,25),\
      (0,92,49),(43,206,72),(255,204,153),(128,128,128),(148,255,181),\
      (143,124,0),(157,204,0),(194,0,136),(0,51,128),(255,164,5),\
      (255,168,187),(66,102,0),(255,0,16),(94,241,242),(0,153,143),\
      (224,255,102),(116,10,255),(153,0,0),(255,255,128),(255,255,0),(255,80,5)

# %%
def get_color(i):
    '''
    Args:
        i (int)

    Returns:
        tuple: triplet with RGB color

    '''
    return dot_col[np.mod(i, len(dot_col))]

#%%
def draw_sample(sample, dot):
    '''
    Args:
        sample (dictionary of numpy arrays): Contains eye tracking data
        dot (psychopy object)

    Returns:
        None.

    '''

    # Convert from tobii coordinate system to pixels and draw dot
    temp = np.array([sample['left_gaze_point_on_display_area_x'][0],
                     sample['left_gaze_point_on_display_area_y'][0]])
    xy = helpers.tobii2deg(np.expand_dims(temp, axis=0), win.monitor)


    dot.pos = (xy[0][0],
               xy[0][1])
    dot.draw()

# %%
def wait_for_message(msg):
    '''
    Args:
        msg (str): message to wait for

    Returns:
        None.

    '''
    # Wait for command from the master to start
    message_received = False
    while not message_received:
        for inlet in inlets:
            sample, timestamp = inlet.pull_sample(timeout=0.0)

            # Sample is None or contains a string
            if sample:
                if msg in sample[0]:
                    message_received = True
                    break

        k = event.getKeys()
        if k:
            if 'space' in k:
                break

        core.wait(0.001)

# %%  Monitor/geometry
MY_MONITOR = 'testMonitor'  # needs to exists in PsychoPy monitor center
FULLSCREEN = True
SCREEN_RES = [1920, 1080]
SCREEN_WIDTH = 52.7  # cm
VIEWING_DIST = 63  # distance from eye to center of screen (cm)

monitor_refresh_rate = 60  # frames per second (fps)
mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)

# info about wally
WALLY_POS = (1920/2-955, 1080/2-74) # Pixel position of Walley in image
IMNAME_WALLY = 'wally_search.png'
IMNAME_WALLY_FACE = 'wally_face.jpg'
MAX_SEARCH_TIME = 20

# %%  ET settings
et_name = 'Tobii Pro Spectrum'
# et_name = 'IS4_Large_Peripheral'
# et_name = 'Tobii Pro Nano'
dummy_mode = False # Run without eye tracker
draw_own_gaze = True # Draw gaze marker for own client

# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile'
settings.N_CAL_TARGETS = 5

# %% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()

tracker.init()
device_name = tracker.buffer.device_name
address = tracker.buffer.address

# Create a TittaLSLPy sender that subscribes to the gaze data stream
sender = TittaLSLPy.Sender(address)
local_stream_source_id = sender.get_stream_source_id("gaze")
sender.start('gaze')

# Get hostname of computer
hostname = socket.gethostname() # Name of computer (e.g., STATION15)
hostname_id = int(''.join([n for n in hostname if n.isdigit()]))

# Make an LSL outlet to send messages
info = StreamInfo('MyClientStream', 'ETmsg', 1, 0, 'string', device_name)
outlet = StreamOutlet(info)

# Window set-up
win = visual.Window(monitor=mon, fullscr=FULLSCREEN,
                    screen=1, size=SCREEN_RES, units='deg', checkTiming=False)
text = visual.TextStim(win, height=50, units='pix')
dot_wally = visual.Circle(win, radius=60, lineColor='green',
                    fillColor= None, lineWidth=10, units='pix',
                    pos = WALLY_POS)

dot = visual.Circle(win, radius=2, lineColor='red',
                    fillColor= None, lineWidth=5)
dot_local = visual.Circle(win, radius=1, lineColor='red',
                    fillColor= None, lineWidth=5)
fixation_point = helpers.MyDot2(win)

im_search = visual.ImageStim(win, image=IMNAME_WALLY)
im_face = visual.ImageStim(win, image=IMNAME_WALLY_FACE)

# Calibrate the eye tracker
tracker.calibrate(win)
print('calibration done')
win.flip()

# %% Send calibration results to master
if len(tracker.deviations) >= 1:
    dev_L, dev_R = tracker.deviations[0][0], tracker.deviations[0][1]
else:
    dev_L, dev_R = np.nan, np.nan
print([f'{device_name}, {dev_L:.2f}, {dev_R:.2f}'])
outlet.push_sample([f'{device_name}, {dev_L:.2f}, {dev_R:.2f}'])
print("Sent calibration results to master")

# Create inlets for all opened LSL outlets with name 'Markers',
# i.e., the one created by the master. This way, messages sent by the
# master can be received by the clients
streams = resolve_stream('type', 'Markers')

# Start the eye tracker
tracker.start_recording(gaze=True)

# Start receiving et data with LSL (find started remote streams)
remote_streams = TittaLSLPy.Receiver.get_streams("gaze")  # can filter so only streams of specific type are provided
receivers = []
for stream in remote_streams:

    # Do not start a receiver for local client
    if local_stream_source_id == stream["source_id"]:
        continue

    r = TittaLSLPy.Receiver(stream["source_id"])
    r.start()
    receivers.append([r, stream['hostname']])

# %% Show wally and wait for command to start exp

# This is Wally
im_face.pos = (0, 7)
im_face.draw()

text.text = 'Press the spacebar as soon as you have found Wally \n\n Please wait for the experiment to start.'
text.draw()
win.flip()

# create new inlet to read from the streams (one per stream)
inlets = []
for stream in streams:
    inlets.append(StreamInlet(stream))

# %% Start sending and receiving et data with LSL
print('waiting for start command')
wait_for_message('start_exp')

# %% Run the search

# Present fixation dot and wait for one second
for i in range(monitor_refresh_rate):
    fixation_point.draw()
    t = win.flip()
    if i == 0:
        tracker.send_message('fix on')

tracker.send_message('fix off')

# Search until keypress or timeout
search_time = MAX_SEARCH_TIME
im_name = im_search.image
for i in range(int(MAX_SEARCH_TIME * monitor_refresh_rate)):

    # Draw wally
    im_search.draw()

    # Read and draw local sample
    if draw_own_gaze:
        sample = tracker.buffer.peek_N('gaze', 1)
        draw_sample(sample, dot_local)

    # Get and draw most recent sample from other clients
    for receiver in receivers:
        remote_sample = receiver[0].peek_N(1)
        hostname_remote = receiver[1]

        # Set color of dot based on station number
        dot.lineColor = get_color(hostname_id)
        draw_sample(remote_sample, dot)

        # Save sample as message
        x = remote_sample['left_gaze_point_on_display_area_x'][0]
        y = remote_sample['left_gaze_point_on_display_area_y'][0]

        # System time stamp of the sample on remote machine
        t_remote = remote_sample['remote_system_time_stamp'][0]

        # System time stamp on local machine when remote sample was received
        t_local = remote_sample['local_system_time_stamp'][0]
        tracker.send_message(f'remotesample_{hostname_remote}_{t_remote}_{t_local}_{x}_{y}')

    t = win.flip()

    if i == 0:
        t0 = core.getTime()
        tracker.send_message(''.join(['onset_', im_name]))

    # Check for keypress
    k = event.getKeys()
    if 'space' in k:
        search_time = core.getTime() - t0
        break

tracker.send_message(''.join(['offset_', im_name, '_', str(search_time)]))

win.flip()

# %% Sent info about search time to master
outlet.push_sample([f'{device_name}, {search_time}, {hostname}'])
print("Sent search times to master")

# %% Show the position of wally and clean up a bit

for receiver in receivers:
    receiver[0].stop()

sender.stop('gaze')

# Stop streams (if available). Normally only gaze stream is stopped
tracker.stop_recording(gaze=True)
tracker.save_data()

# Highlight the correct location of Wally
im_search.draw()
text.color = 'green'
text.pos = (WALLY_POS[0], WALLY_POS[1] - 70)
text.text = 'Here is Wally'
text.draw()
dot_wally.draw()

win.flip()
core.wait(5)

# Close window
win.close()

