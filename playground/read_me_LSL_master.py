# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 13:23:56 2024

@author: Marcus
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


# %% start experiment scripts on the remote computers
CLIENT_PATH             = Path(r'C:Share\demo_shared_gaze')
CLIENTS                 = [21,22,24] # Clients to use in search exp

IP_prefix               = '192.168.1.'
UDP_IP_SEND             =   IP_prefix+'255'
UDP_IP_LISTEN           = '0.0.0.0'
UDP_PORT                = 9090
#time.sleep(5)

# %% Create outlets and inlets
info = StreamInfo('MyMaster', 'Markers', 1, 0, 'string', 'myid')
'''
        Keyword arguments:
        name -- Name of the stream. Describes the device (or product series)
                that this stream makes available (for use by programs,
                experimenters or data analysts). Cannot be empty.
        type -- Content type of the stream. By convention LSL uses the content
                types defined in the XDF file format specification where
                applicable (https://github.com/sccn/xdf). The content type is the
                preferred way to find streams (as opposed to searching by name).
        channel_count -- Number of channels per sample. This stays constant for
                         the lifetime of the stream. (default 1)
        nominal_srate -- The sampling rate (in Hz) as advertised by the data
                         source, regular (otherwise set to IRREGULAR_RATE).
                         (default IRREGULAR_RATE)
        channel_format -- Format/type of each channel. If your channels have
                          different formats, consider supplying multiple
                          streams or use the largest type that can hold
                          them all (such as cf_double64). It is also allowed
                          to pass this as a string, without the cf_ prefix,
                          e.g., 'float32' (default cf_float32)
        source_id -- Unique identifier of the device or source of the data, if
                     available (such as the serial number). This is critical
                     for system robustness since it allows recipients to
                     recover from failure even after the serving app, device or
                     computer crashes (just by finding a stream with the same
                     source id on the network again). Therefore, it is highly
                     recommended to always try to provide whatever information
                     can uniquely identify the data source itself.
                     (default '')
'''

# next make an outlet
outlet = StreamOutlet(info)

# print("Send message to start calibration")
# outlet.push_sample(['calibrate'])

# Resolve all streams on the network (created by StreamOutlet)
# Client streams have been assigned the type ETmsg
streams = resolve_stream('type', 'ETmsg')

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
time.sleep(10)

# %% Start experiment
input("Press key to start experiment")
outlet.push_sample(['start_exp'])

# %% Wait to receive information about search times
print("Wait to receive search times")

search_times = wait_for_message('TPSP1')


# Print reaction times and winners
print(sorted(search_times, key=lambda st: st[1]) )