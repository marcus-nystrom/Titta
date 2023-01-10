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
import sys

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

'''
Since samples are pulled in callbacks with the Tobii SDK, it may get
hiccups if your script is doing something very computationally heavy,
without allowing significant sleeps (which would allow the callback to
be called and therefore all samples to be collected appropriately).

This can be tested in a while-loop like the one below.

TobiiWrapper doesn't show this problem luckily, so the below loop is OK!
'''
dur = 4 # Record what should be this many seconds of data
n_samples = tracker.frequency * dur

out = []
k = 0
ts = 0
ts_old = 0

tracker.start_recording(gaze=True,
                            time_sync=True,
                            eye_image=True,
                            notifications=True,
                            external_signal=True,
                            positioning=True)

t0 = time.perf_counter()
while k < n_samples:
    samples = tracker.peek_N('gaze')
    if len(samples)>0:
        ts = samples['system_time_stamp'][0]

    if ts == ts_old:
        #core.wait(0.00001) # Wait 1/10 ms
        continue

    out.append([time.perf_counter(), ts])
    k += 1
    ts_old = ts

    if out[-1][0]-t0>dur/2:
        # start recording eye openness. Also, if set to true, any
        # calls to start or stop either gaze or eye_openness will
        # start or stop both
        tracker.set_include_eye_openness_in_gaze(True)

print(time.perf_counter() - t0)
tracker.stop_recording(gaze=True,
                            time_sync=True,
                            eye_image=True,
                            notifications=True,
                            external_signal=True,
                            positioning=True)


#%% Plot data captured in real time (tobii time stamps, and loop intervals)
out = np.array(out)
plt.figure()
plt.plot(np.diff(out[:, 0] * 1000))
plt.figure()
plt.plot(np.diff(out[:, 1] / 1000))

#%% Plot timestamps of samples in the buffer
all_samples = tracker.peek_N('gaze', sys.maxsize)

plt.figure()
plt.plot(np.diff(all_samples['system_time_stamp']) / 1000)

