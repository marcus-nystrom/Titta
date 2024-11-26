from psychopy import visual, monitors, core, event
import numpy as np
from titta import Titta, helpers_tobii as helpers
import TittaLSLPy
import pylsl
import os
import socket
import typing
import json
import time
import OlssonFilter 

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

def get_color(i):
    return dot_col[i % len(dot_col)]

def tobii_get_gaze(samples, filter=None, ts_field='system_time_stamp'):
    def get_sample(samples,idx,ts_field):
        lx = samples['left_gaze_point_on_display_area_x'][idx]
        ly = samples['left_gaze_point_on_display_area_y'][idx]
        rx = samples['right_gaze_point_on_display_area_x'][idx]
        ry = samples['right_gaze_point_on_display_area_y'][idx]
        x,y = np.nanmean([lx, rx]), np.nanmean([ly, ry])
        return samples[ts_field][idx]/1000, x*SCREEN_RES[0], y*SCREEN_RES[1] # convert us->ms, and norm to pixels
    
    if len(samples[ts_field])==0:
        return np.nan,np.nan

    if filter is None:
        return get_sample(samples,-1,ts_field)[1:]

    for i in range(len(samples[ts_field])):
        ts,x,y = get_sample(samples,i,ts_field)
        fx,fy = filter.add_sample(ts,x,y)
    return fx, fy

def draw_sample(dot, x, y):
    dot.pos = (x-SCREEN_RES[0]/2, SCREEN_RES[1]/2-y)
    dot.draw()

def warm_up_bidirectional_comms(outlet, inlet):
    # don't ask. need to try to send and receive back and forth
    # some times for both channels to come online and start 
    # sending and receiving without samples being dropped...
    remote_conn_est = False
    while not outlet.have_consumers():
        outlet.push_sample(['warm up'])
        sample, _ = inlet.pull_sample(timeout=0.1)
        if sample and sample[0]=='connection established':
            remote_conn_est = True
    outlet.push_sample(['connection established'])
    if not remote_conn_est:
        sample, _ = inlet.pull_sample()

def wait_for_message(prefix, inlets: typing.List[pylsl.StreamInlet], exit_key=None, is_json=False):
    if not isinstance(inlets,list):
        inlets = [inlets]
    inlets_to_go = {i:inlet for i,inlet in enumerate(inlets)}
    out = [None for i in inlets_to_go]
    while True:
        for i in list(inlets_to_go.keys()):
            msg, _ = inlets_to_go[i].pull_sample(timeout=0.0)

            if msg and msg[0].startswith(prefix):
                del inlets_to_go[i]
                the_msg = msg[0][len(prefix):]
                if not the_msg:
                    out[i] = ''
                elif is_json:
                    out[i] = json.loads(the_msg[1:])
                else:
                    out[i] = the_msg[1:].split(',')

        # Break if message has been received from all inlets
        if not inlets_to_go or exit_key and exit_key in event.getKeys([exit_key]):
            break
        core.wait(0.01)

    if len(inlets)==1:
        out = out[0]
    return out

# Monitor/geometry
MY_MONITOR = 'testMonitor'  # needs to exists in PsychoPy monitor center
FULLSCREEN = False
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
MAX_SEARCH_TIME = 20                # seconds

# ET settings
et_name = 'Tobii Pro Spectrum'
draw_own_gaze = True # Draw gaze marker for own gaze (true) or only for others?
filter_gaze = True

# Get default settings for the eye tracker, change any if you wish, and connect to the eye tracker
settings = Titta.get_defaults(et_name)
tracker = Titta.Connect(settings)
tracker.init()
et_name = tracker.buffer.serial_number
et_address = tracker.buffer.address

# Get hostname of computer
hostname = socket.gethostname() # Name of computer (e.g., STATION15)

# Find master and open a communication channel with it so that
# commands from the master can be received
streams = pylsl.resolve_byprop('type', 'Wally_master')
if len(streams)>1:
    raise RuntimeError('More than one Wally_master found on the network, can\'t continue')
from_master = pylsl.StreamInlet(streams[0])

# Open a communication channel to send messages to the master
info = pylsl.StreamInfo('Wally_finder', 'Wally_client', 1, pylsl.IRREGULAR_RATE, pylsl.cf_string, f'{hostname}_{et_name}')
to_master = pylsl.StreamOutlet(info,1)

# ensure we're properly connected
warm_up_bidirectional_comms(to_master, from_master)

# tell master about the connected eye tracker
wait_for_message('get_eye_tracker', from_master)
msg = f'eye_tracker,{et_name},{et_address}'
to_master.push_sample([msg])

# Window set-up
win = visual.Window(monitor=mon, fullscr=FULLSCREEN,
                    screen=1, size=SCREEN_RES, units='deg', checkTiming=False)
text = visual.TextStim(win, height=50, units='pix')
dot_wally = visual.Circle(win, radius=60, lineColor='red',
                          fillColor= None, lineWidth=10, units='pix',
                          pos = WALLY_POS)
bg_box = visual.Rect(win, lineColor=None,
                     fillColor= 'grey', opacity=.7, units='pix',
                     pos = (WALLY_POS[0], WALLY_POS[1]-25), size=[320,200])

remote_gaze = visual.Circle(win, radius=50, lineColor='red', units='pix',
                            fillColor= None, lineWidth=5)
local_gaze  = visual.Circle(win, radius=25, lineColor='red', units='pix',
                            fillColor= None, lineWidth=5)
fixation_point = helpers.MyDot2(win)

im_search = visual.ImageStim(win, image=IMNAME_WALLY)
im_face   = visual.ImageStim(win, image=IMNAME_WALLY_FACE)

# Calibrate the eye tracker
tracker.calibrate(win)
win.flip()

# Send calibration results to master
if len(tracker.deviations) >= 1:
    dev_L, dev_R = tracker.deviations[0][0], tracker.deviations[0][1]
else:
    dev_L, dev_R = np.nan, np.nan
msg = f'calibration_done,{dev_L:.2f},{dev_R:.2f}'
to_master.push_sample([msg])

# wait for master to tell us which clients to connect to
connect_to = wait_for_message(f'connect_to,{hostname}', from_master, is_json=True)
hosts_to_connect_to = {c[0] for c in connect_to}

# Start the eye tracker
tracker.start_recording(gaze=True)

# Create a TittaLSLPy sender that makes this eye tracker's gaze data stream available on the network
sender = TittaLSLPy.Sender(et_address)
sender.start('gaze')

# Start receiving et data with LSL (find started remote streams)
receivers: typing.Dict[str,TittaLSLPy.Receiver] = {}
t0 = time.monotonic()
while True:
    remote_streams = TittaLSLPy.Receiver.get_streams("gaze")
    for stream in remote_streams:
        h = stream['hostname']
        if h in receivers or h not in hosts_to_connect_to:
            continue

        r = TittaLSLPy.Receiver(stream["source_id"])
        r.start()
        receivers[h] = r
    
    if len(receivers)==len(hosts_to_connect_to):
        break

    core.wait(0.05)

# prep filters
if filter_gaze:
    filters = {'local': OlssonFilter.Filter()}
    filters.update({r:OlssonFilter.Filter() for r in receivers})

# prep gaze timestamps
last_ts = {'local': 0}
last_ts.update({r:0 for r in receivers})

# Show wally and wait for command to start exp
im_face.pos = (0, 7)
im_face.draw()
text.text = 'Press the spacebar as soon as you have found Wally\n\nPlease wait for the experiment to start.'
text.draw()
win.flip()

# Wait for start command
wait_for_message('start_exp', from_master)

# Run the search
# Present fixation dot and wait for one second
for i in range(monitor_refresh_rate):
    fixation_point.draw()
    t = win.flip()
    if i == 0:
        tracker.send_message('fix on')
tracker.send_message('fix off')

# Search until keypress or timeout
search_time = np.inf
im_name = im_search.image
to_skip = {r:False for r in receivers}
for i in range(int(MAX_SEARCH_TIME * monitor_refresh_rate)):
    # Draw wally
    im_search.draw()

    # Read and draw local sample
    if draw_own_gaze:
        samples = tracker.buffer.peek_time_range('gaze', last_ts['local'])
        if len(samples['system_time_stamp'])>0:
            last_ts['local'] = samples['system_time_stamp'][-1]
        x,y = tobii_get_gaze(samples, filters['local'] if filter_gaze else None)
        draw_sample(local_gaze, x, y)

    # see if should disconnect from any remote streams
    while True:
        msg, _ = from_master.pull_sample(timeout=0.0)
        if not msg:
            break
        if msg[0].startswith('disconnect_stream'):
            host_to_disconnect = msg[0][len('disconnect_stream')+1:]
            if host_to_disconnect in receivers:
                receivers[host_to_disconnect].stop(True)
                to_skip[host_to_disconnect] = True

    # Get and draw most recent sample from other clients
    for idx,r in enumerate(receivers):
        if to_skip[r]:
            continue

        remote_samples = receivers[r].peek_time_range(last_ts[r])
        if len(remote_samples['local_system_time_stamp'])>0:
            last_ts[r] = remote_samples['local_system_time_stamp'][-1]
        x,y = tobii_get_gaze(remote_samples, filters[r] if filter_gaze else None, 'local_system_time_stamp')
        if np.isnan(x) or np.isnan(y):
            continue
        
        # Set color of dot based on receiver number
        remote_gaze.lineColor = get_color(idx)
        
        draw_sample(remote_gaze, x, y)

        # Save sample as message
        # System time stamp of the sample on remote machine
        t_remote = remote_samples['remote_system_time_stamp'][-1]
        # corresponding local system timestamp (synchronized with LSL's capabilities)
        t_local = remote_samples['local_system_time_stamp'][-1]
        tracker.send_message(f'remotesample_{r}_{t_remote}_{t_local}_{x}_{y}')

    t = win.flip()

    if i == 0:
        t0 = t
        tracker.send_message(f'onset_{im_name}')

    # Check for keypress
    k = event.getKeys()
    dur = core.getTime()-t0
    if 'space' in k and dur>1:
        search_time = dur
        break

tracker.send_message(f'offset_{im_name}_{search_time}')

win.flip()

# Send info about search time to master
to_master.push_sample([f'search_time,{json.dumps(search_time)}'])

# Show the position of wally and clean up a bit
for r in receivers:
    receivers[r].stop()
sender.stop('gaze')

# Stop streams (if available). Normally only gaze stream is stopped
tracker.stop_recording(gaze=True)
tracker.save_data()

# Highlight the correct location of Wally
im_search.draw()
bg_box.draw()
text.color = 'red'
text.pos = (WALLY_POS[0], WALLY_POS[1] - 90)
text.text = 'Here is Wally'
text.draw()
dot_wally.draw()

win.flip()
core.wait(5)

# Close window
win.close()