# Import relevant modules
import pandas as pd
from psychopy import visual, monitors, core, event
import numpy as np
import matplotlib.pyplot as plt
from titta import Titta, helpers_tobii as helpers
import h5py
import TittaLSLPy
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream

# from TittaLSLPy import Sender, Receiver

# %%

def draw_sample(sample):

    # Convert from tobii coordinate system to pixels and draw dot
    temp = np.array([sample['left_gaze_point_on_display_area_x'][0],
                     sample['left_gaze_point_on_display_area_y'][0]])

    xy = helpers.tobii2pix(np.expand_dims(temp, axis=0), win)


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

im_names = ['im1.jpeg']#, 'im2.jpeg', 'im3.jpeg']
stimulus_duration = 30

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

# Create a sender
sender = TittaLSLPy.Sender(tracker.buffer.address)
local_stream_source_id = sender.get_stream_source_id("gaze")
sender.start('gaze')

# Make and outlet
info = StreamInfo('MyClientStream', 'ETmsg', 1, 0, 'string', tracker.buffer.device_name)
outlet = StreamOutlet(info)

# Window set-up (this color will be used for calibration)
win = visual.Window(monitor=mon, fullscr=FULLSCREEN,
                    screen=1, size=SCREEN_RES, units='deg')
text = visual.TextStim(win, height=1)
dot = visual.Circle(win, radius=30, units='pix', lineColor='red',
                    fillColor= None, lineWidth=5)
fixation_point = helpers.MyDot2(win)

images = []
for im_name in im_names:
    images.append(visual.ImageStim(win, image=im_name, units='norm', size=(2, 2)))

tracker.calibrate(win)

win.flip()

# %% Send calibration results to master

if len(tracker.deviations) >= 1:
    dev_L, dev_R = tracker.deviations[0][0], tracker.deviations[0][1]
else:
    dev_L, dev_R = np.nan, np.nan
print("Send calibration results to master")
outlet.push_sample([f'{tracker.buffer.device_name}, {dev_L:.2f}, {dev_R:.2f}'])


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

# %% Wait for command to start exp

text.text = 'Wait for command from Master to start exp (or press space)'
text.draw()
win.flip()

# Create inlets
streams = resolve_stream('type', 'Markers')

# create new inlet to read from the streams (one per stream)
inlets = []
for stream in streams:
    inlets.append(StreamInlet(stream))

# print(len(inlets))
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

# %% Record some data. Normally only gaze stream is started

# Present fixation dot and wait for one second
for i in range(monitor_refresh_rate):
    fixation_point.draw()
    t = win.flip()
    if i == 0:
        tracker.send_message('fix on')

tracker.send_message('fix off')

# Wait exactly 3 * fps frames (3 s)
np.random.shuffle(images)
for image in images:

    search_time = np.nan
    im_name = image.image
    for i in range(int(stimulus_duration * monitor_refresh_rate)):
        image.draw()

        # Read and draw local sample
        sample = tracker.buffer.peek_N('gaze', 1)
        draw_sample(sample)

        # Get and plot most recent sample from remotes
        for receiver in receivers:
            remote_sample = receiver.peek_N(1)
            draw_sample(remote_sample)

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

# %% Sent info about search time to master
print("Send search time to master")
outlet.push_sample([f'{tracker.buffer.device_name}, {search_time}'])

# %%
win.flip()

for receiver in receivers:
    receiver.stop()

sender.stop('gaze')

# Stop streams (if available). Normally only gaze stream is stopped
tracker.stop_recording(gaze=True)

# Close window and save data
win.close()

