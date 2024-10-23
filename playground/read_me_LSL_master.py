# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 13:23:56 2024

@author: Marcus
ToDo: Use IP addresses instead of serial number of et

"""

from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream
import time
from pathlib import Path

def wait_for_message(msg):

    out = []
    while True:
        for inlet in inlets:
            sample, timestamp = inlet.pull_sample(timeout=0.0)

            # Sample is None or contains a string
            if sample:
                if msg in sample[0]:
                    L = sample[0].split(',')
                    out.append(L)
                    print(L)

        # Break if all calibration are done
        if len(out) >= len(inlets):
            break

        time.sleep(0.001)

    return out
# %% Create outlets and inlets
n_clients = 1
info = StreamInfo('MyMaster', 'Markers', 1, 0, 'string', 'myid')

# next make an outlet
outlet = StreamOutlet(info)

# print("Send message to start calibration")
# outlet.push_sample(['calibrate'])

# Resolve all streams on the network (created by StreamOutlet)
# Client streams have been assigned the type ETmsg

streams = []
while len(streams) < n_clients:
    streams = resolve_stream('type', 'ETmsg')
    print(f'{len(streams)} clients connected')

# create new inlet to read from the streams (one per stream)
# The number of streams correspond to the number or created outlets on the netrowk
# Exclude the local stream just include since it has type 'Markers'
inlets = []
for stream in streams:
    inlets.append(StreamInlet(stream))

print(f'Number of inlets: {len(inlets)}')

# %% Wait to receive information about calibration results
print('Waiting to receive calibration results')
out = wait_for_message('TPSP1')
print('Calibration done!')
time.sleep(5)

# %% Start experiment
input("Press key to start experiment")
outlet.push_sample(['start_exp'])

# %% Wait to receive information about search times
print("Wait to receive search times")

search_times = wait_for_message('TPSP1')
print(f'Search times (received at master) {search_times}')


# Print reaction times and winners
print(sorted(search_times, key=lambda st: st[1]) )
