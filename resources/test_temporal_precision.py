'''
Since samples are pulled in callbacks with the Tobii SDK, it may get 
hick-ups if your script is doing something very computationally heavy, 
without allowing significant sleeps (which would allow the callback to 
be called and therefore all sample to be collected appropriately).

This can be tested in a while-loop like the one below.                                     
'''
# Import modules
import pickle
import pandas as pd
import numpy as np
import time
from psychopy import core
from titta import Titta, helpers_tobii as helpers
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

#%% test granularity of clock
#k = 0
#out = []
#while k < 10000:
#    k += 1
#    out.append(time.clock())
#    
#plt.plot(np.diff(out))
    
#%% Record some data
tracker.start_recording(gaze_data=True, store_data=True)
core.wait(0.2)
n_samples = 600 * 2 # Record two seconds of data at 600 Hz
k = 0

out = []
ts_old = 0

t0 = time.clock()
call_times = []
while k < n_samples:
    
#    t1 = time.clock()
    s = tracker.get_latest_sample()
    ts = s['system_time_stamp']

    if ts == ts_old:
        core.wait(0.00001) # Wait 1/10 ms
#        call_times.append(time.clock() - t1)
        continue
    
    out.append([time.clock(), ts])
    k += 1
    ts_old = ts
    
print(time.clock() - t0)
tracker.stop_recording(gaze_data=True)

out = np.array(out)

#%% Plot data capture in real time (tobii time stamps, and loop intervals)
plt.plot(np.diff(out[:, 0] * 1000))    
plt.figure()
plt.plot(np.diff(out[:, 1] / 1000))    

#%%
ut =[]
for i in tracker.gaze_data_container:
    ut.append(i[0])
    
plt.figure()
plt.plot(np.diff(ut) / 1000)
