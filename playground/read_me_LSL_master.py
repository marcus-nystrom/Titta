# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 13:23:56 2024

@author: Marcus
"""

from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream
import time

def wait_for_message(msg):

    out = []
    while True:
        for inlet in inlets:
            sample, timestamp = inlet.pull_sample(timeout=0.0)

            # Sample is None or contains a string
            if sample:
                if msg in sample:
                    L = sample.split(',')
                    out.append(L)
                    print(L)

        # Break if all calibration are done
        if len(out) >= len(inlets) - 1:
            print('Done!')
            break


# %% start experiment scripts on the remote computers

#time.sleep(5)

# %% Create outlets and inlets
info = StreamInfo('MyMarkerStream', 'Markers', 1, 0, 'string', 'myuidw43536')

# next make an outlet
outlet = StreamOutlet(info)

# print("Send message to start calibration")
# outlet.push_sample(['calibrate'])

# Create inlets
streams = resolve_stream('type', 'Markers')

# create new inlet to read from the streams (one per stream)
inlets = []
for stream in streams:
    inlets.append(StreamInlet(stream))

# %% Wait to receive information about calibration results
print('Waiting to receive calibration results')

out = wait_for_message('TPSP1')

# %% Start experiment
print("Send message to start experiment")
outlet.push_sample(['start_exp'])

# %% Wait to receive information about search times
print("Wait to receive search times")

out = wait_for_message('TPSP1')


# Print reaction times and winners
# print(sorted(search_times, key=lambda st: st[1]) )