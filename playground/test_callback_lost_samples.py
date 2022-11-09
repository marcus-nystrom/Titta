# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 08:54:27 2022

@author: Marcus
"""


import tobii_research as tr
import numpy as np
import matplotlib.pyplot as plt
import time


def eye_openness_data_callback(eye_openness_data):
    global global_eye_openness_data
    global_eye_openness_data.append(eye_openness_data['system_time_stamp'])

def gaze_data_callback(gaze_data):
    # print(gaze_data)
    global global_gaze_data
    global_gaze_data.append(gaze_data['system_time_stamp'])


# Add a sleep period to avoid hogging of callback
add_sleep = False

eyetrackers = tr.find_all_eyetrackers()
eyetracker = eyetrackers[0]

global_gaze_data = []
global_eye_openness_data = []

Fs = 1200
eyetracker.set_gaze_output_frequency(Fs)
print("Gaze output frequency reset to {0} Hz.".format(Fs))

print("Subscribing to gaze data for eye tracker with serial number {0}.".format(eyetracker.serial_number))
eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)

print("Subscribing to eye openness data for eye tracker with serial number {0}.".format(eyetracker.serial_number))
eyetracker.subscribe_to(tr.EYETRACKER_EYE_OPENNESS_DATA, eye_openness_data_callback, as_dictionary=True)
time.sleep(1)

# Do something that distrubs the callbacks
recording_duration = 30
data = []
ts_old = 0
t0 = time.time()

while True:

    if (time.time() - t0) > recording_duration:
        print(time.time() - t0)
        break

    if add_sleep:
        time.sleep(0.001)

eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)
eyetracker.unsubscribe_from(tr.EYETRACKER_EYE_OPENNESS_DATA, eye_openness_data_callback)

# %%
plt.close('all')
t = (np.array(global_gaze_data) - global_gaze_data[0])/1000
plt.plot(t[1:], np.diff(global_gaze_data) / 1000)
plt.title('Timestamps gaze')
plt.xlabel('Time (ms)')
plt.ylabel('Intersample interval (ms)')

plt.figure()
t = (np.array(global_eye_openness_data) - global_eye_openness_data[0])/1000
plt.plot(t[1:], np.diff(global_eye_openness_data) / 1000)
plt.xlabel('Time (ms)')
plt.title('Timestamps eyeopenness')
plt.ylabel('Intersample interval (ms)')