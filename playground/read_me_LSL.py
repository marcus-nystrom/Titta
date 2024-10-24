# Import relevant modules
import pandas as pd
from psychopy import visual, monitors, core, event
import numpy as np
import matplotlib.pyplot as plt
from titta import Titta, helpers_tobii as helpers
import h5py
import numpy as np
import TittaLSLPy
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream

# from TittaLSLPy import Sender, Receiver

# 26 colors from The Colour Alphabet Project suggested by Paul Green-Armytage
# designed for use with white background:
dot_col = (240,163,255),(0,117,220),(153,63,0),(76,0,92),(25,25,25),\
      (0,92,49),(43,206,72),(255,204,153),(128,128,128),(148,255,181),\
      (143,124,0),(157,204,0),(194,0,136),(0,51,128),(255,164,5),\
      (255,168,187),(66,102,0),(255,0,16),(94,241,242),(0,153,143),\
      (224,255,102),(116,10,255),(153,0,0),(255,255,128),(255,255,0),(255,80,5)

# %%
def get_color(i):
    return dot_col[np.mod(i, len(dot_col))]

def draw_sample(sample, dot):

    # Convert from tobii coordinate system to pixels and draw dot
    temp = np.array([sample['left_gaze_point_on_display_area_x'][0],
                     sample['left_gaze_point_on_display_area_y'][0]])

    xy = helpers.tobii2deg(np.expand_dims(temp, axis=0), win.monitor)
    print(xy)


    dot.pos = (xy[0][0],
               xy[0][1])
    dot.draw()

# %%
dummy_mode = False

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

# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile'
settings.N_CAL_TARGETS = 5
settings.DEBUG = False



# Use settings.__dict__ to see all available settings

# Example of how to change the graphics; here, the color of the 'start calibration' button
# settings.graphics.COLOR_CAL_BUTTON = 'green'
# settings.graphics.TEXT_COLOR = 'green'

# %% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
if dummy_mode:
    tracker.set_dummy_mode()

tracker.init()
device_name = tracker.buffer.device_name
address = tracker.buffer.address

# Create a sender
sender = TittaLSLPy.Sender(address)
local_stream_source_id = sender.get_stream_source_id("gaze")
sender.start('gaze')

# Make and outlet
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

# images = []
# for im_name in im_names:
#     images.append(visual.ImageStim(win, image=im_name, units='norm', size=(2, 2)))

tracker.calibrate(win)
win.flip()

# %% Send calibration results to master

if len(tracker.deviations) >= 1:
    dev_L, dev_R = tracker.deviations[0][0], tracker.deviations[0][1]
else:
    dev_L, dev_R = np.nan, np.nan
print("Send calibration results to master")
outlet.push_sample([f'{device_name}, {dev_L:.2f}, {dev_R:.2f}'])


# %% Start sending and receiving et data with LSL
tracker.start_recording(gaze=True)


#core.wait(3)

remote_streams = TittaLSLPy.Receiver.get_streams("gaze")  # can filter so only streams of specific type are provided

receivers = []
for stream in remote_streams:

    # Do not start a receiver for local client
    if local_stream_source_id == stream["source_id"]:
        continue

    r = TittaLSLPy.Receiver(stream["source_id"])
    r.start()
    receivers.append(r)


# print(r.get_info()['source_id'])
# print(r.get_type())

# %% Show wally and wait for command to start exp

# This is Wally
im_face.pos = (0, 7)
im_face.draw()

text.text = 'Press the spacebar as soon as you have found Wally \n\n Please wait for the experiment to start.'
text.draw()
win.flip()

core.wait(3)

# Create inlets for all opened outlets with name 'Markers'
streams = resolve_stream('type', 'Markers')

# create new inlet to read from the streams (one per stream)
inlets = []
for stream in streams:
    inlets.append(StreamInlet(stream))

start_exp = False
while not start_exp:
    for inlet in inlets:
        sample, timestamp = inlet.pull_sample(timeout=0.0)

        # Sample is None or contains a string
        if sample:
            if 'start_exp' in sample[0]:
                start_exp = True
                break

    k = event.getKeys()
    # print(k)
    if 'space' in k:
        start_exp = True
        break

    core.wait(0.001)

    # text.draw()
    # win.flip()

# %% Run the search

# Present fixation dot and wait for one second
for i in range(monitor_refresh_rate):
    fixation_point.draw()
    t = win.flip()
    if i == 0:
        tracker.send_message('fix on')

tracker.send_message('fix off')

search_time = np.nan
im_name = im_search.image
for i in range(int(MAX_SEARCH_TIME * monitor_refresh_rate)):

    # Draw wally
    im_search.draw()

    # Read and draw local sample
    sample = tracker.buffer.peek_N('gaze', 1)
    draw_sample(sample, dot_local)

    # Get and draw most recent sample from remotes
    for receiver in receivers:
        remote_sample = receiver.peek_N(1)

        # Set color of dot based on ip address (last two digits in ip-address)
        # dot.lineColor = get_color(ip)
        draw_sample(remote_sample, dot)

    t = win.flip()

    if i == 0:
        t0 = core.getTime()
        tracker.send_message(''.join(['onset_', im_name]))

    # Check for keypress
    k = event.getKeys()
    if 'space' in k:
        search_time = core.getTime() - t0
        break

    tracker.send_message(''.join(['offset_', im_name]))

win.flip()

# %% Sent info about search time to master
print("Send search time to master")
print(f'{device_name}, {search_time}')
outlet.push_sample([f'{device_name}, {search_time}'])

# %%

for receiver in receivers:
    receiver.stop()

sender.stop('gaze')

# Stop streams (if available). Normally only gaze stream is stopped
tracker.stop_recording(gaze=True)

# Highlight the correct location of Wally
im_search.draw()
text.color = 'green'
text.pos = (WALLY_POS[0], WALLY_POS[1] - 70)
text.text = 'Here is Wally'
text.draw()
dot_wally.draw()
#text.height = 100
# text.setPos(wally_pos)
#text.text = 'o'
#text.draw()
win.flip()
core.wait(5)

# Close window
win.close()

