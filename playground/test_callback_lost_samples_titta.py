'''
Since samples are pulled in callbacks with the Tobii SDK, it may get
hick-ups if your script is doing something very computationally heavy,
without allowing significant sleeps (which would allow the callback to
be called and therefore all sample to be collected appropriately).

This can be tested in a while-loop like the one below.

If in a while loop without a time.sleep() or core.wait(), data are lost!
IMPORTANT:  Make sure your script always have a core.wait() or win.flip in each loop.
'''
# Import modules
import numpy as np
import time
from titta import Titta
import matplotlib.pyplot as plt

plt.close('all')

#%% ET settings
et_name = 'Tobii Pro Spectrum'

# Change any of the default dettings?e
settings = Titta.get_defaults(et_name)
settings.FILENAME = 'testfile.tsv'

#%% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
tracker.init()


#%% Record some data
tracker.start_recording(gaze_data=True, store_data=True)

# Do something computationally heavy (like a for-loop) that distrubs the callback
recording_duration = 10
data = []
ts_old = 0
t0 = time.time()
global_gaze_data = []
while True:

    if (time.time() - t0) > recording_duration:
        print(time.time() - t0)
        break

    s = tracker.get_latest_sample()
    ts = s['system_time_stamp']

    # Uncomment this and you'll have great data again
    time.sleep(0.001)

tracker.stop_recording(gaze_data=True)

#%% Plot timestamps
ut =[]
for i in tracker.gaze_data_container:
    ut.append(i[0])

plt.figure()
t = (np.array(ut) - ut[0])/1000
plt.plot(t[1:], np.diff(ut) / 1000)
plt.xlabel('Time (ms)')
plt.title('Timestamps gaze')
plt.ylabel('Intersample interval (ms)')

ut =[]
for i in tracker.eye_openness_data_container:
    ut.append(i[0])

plt.figure()
t = (np.array(ut) - ut[0])/1000
plt.plot(t[1:], np.diff(ut) / 1000)
plt.xlabel('Time (ms)')
plt.title('Timestamps eyeopenness')
plt.ylabel('Intersample interval (ms)')
