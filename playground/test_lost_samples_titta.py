'''
Since samples are pulled in callbacks with the Tobii SDK in Python, it may get
hick-ups if your script is doing something very computationally heavy,
without allowing significant sleeps (which would allow the callback to
be called and therefore all sample to be collected appropriately).

This can be tested in a while-loop like the one below.

Pulling samples with PyTitta (C++ wrapper) doesn't show this problem luckily, so the below loop is OK!

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
settings.FILENAME = 'testfile'

#%% Connect to eye tracker and calibrate
tracker = Titta.Connect(settings)
tracker.init()


#%% Record some data

dur = 4 # Record what should be this many seconds of data
n_samples = int(tracker.get_sample_rate() * dur)

out = []
k = 0
ts_old = 0

tracker.start_recording(gaze=True,
                            time_sync=True,
                            eye_image=True,
                            notifications=True,
                            external_signal=True,
                            positioning=True)

t0 = time.perf_counter()
out = np.zeros((n_samples, 2))
while k < n_samples:

    # Grab teh most recent sample
    samples = tracker.buffer.peek_N('gaze', 1, 'end')

    # is there a sample?
    if len(samples['system_time_stamp']) > 0:
        ts = samples['system_time_stamp'][0]
    else:
        continue

    # is it a new sample?
    if ts == ts_old:
        continue

    out[k, 0] = time.perf_counter()
    out[k, 1] = ts

    k += 1
    ts_old = ts

print(time.perf_counter() - t0)
tracker.stop_recording(gaze=True,
                            time_sync=True,
                            eye_image=True,
                            notifications=True,
                            external_signal=True,
                            positioning=True)


#%% Plot data captured in real time (tobii time stamps, and loop intervals)
plt.figure()
plt.plot(np.diff(out[:, 0] * 1000))
plt.figure()
plt.plot(np.diff(out[:, 1] / 1000))

#%% Plot timestamps of samples in the buffer
all_samples = tracker.buffer.consume_N('gaze', sys.maxsize)

plt.figure()
plt.plot(np.diff(all_samples['system_time_stamp']) / 1000)

