# Import modules
import pickle
import pandas as pd
import numpy as np
import time
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

n_samples = 600 * 2
k = 0

out = []
ts_old = 0

t0 = time.clock()
#time.sleep(2)
call_times = []
while k < n_samples:
    
    t1 = time.clock()
    s = tracker.get_latest_sample()
    ts = s['system_time_stamp']
    call_times.append(time.clock() - t1)

    if ts == ts_old:
        time.sleep(0.011)
        continue
    
    out.append([time.clock(), ts])
    k += 1
    ts_old = ts
    
#    time.sleep(0.1)
# 
print(time.clock() - t0)
tracker.stop_recording(gaze_data=True)

out = np.array(out)

#%%

plt.plot(np.diff(out[:, 0] * 1000))    
plt.figure()
plt.plot(np.diff(out[:, 1] / 1000))    



#%%
ut =[]
for i in tracker.gaze_data_container:
    ut.append(i[0])
    
plt.figure()
plt.plot(np.diff(ut) / 1000)
