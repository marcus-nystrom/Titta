import pylsl
import typing
import time
import keyboard
import json
import math

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

def wait_for_message(prefix, inlets: typing.Dict[str,pylsl.StreamInlet], exit_key=None, is_json=False, verbose=False, callback=None):
    extra = f'. Press "{exit_key}" to continue' if exit_key else ''
    print(f'waiting for "{prefix}" messages{extra}')
    inlets_to_go = inlets.copy()
    out = {i: None for i in inlets_to_go}
    while True:
        for i in list(inlets_to_go.keys()):
            msg, _ = inlets_to_go[i].pull_sample(timeout=.1)

            if msg and msg[0].startswith(prefix):
                del inlets_to_go[i]
                the_msg = msg[0][len(prefix):]
                if not the_msg:
                    out[i] = ''
                elif is_json:
                    out[i] = json.loads(the_msg[1:])
                else:
                    out[i] = the_msg[1:].split(',')
                if verbose:
                    if inlets_to_go:
                        print(f'still waiting for "{prefix}": {[i for i in inlets_to_go]}')
                    else:
                        print(f'received "{prefix}" message from all clients')
                if callback:
                    callback(i)

        # Break if all calibration are done
        if not inlets_to_go or exit_key and keyboard.is_pressed(exit_key):
            break
        time.sleep(0.01)

    return out

def tell_to_disconnect(outlet,hostname):
    outlet.push_sample([f'disconnect_stream,{hostname}'])

# Create outlet for sending commands to clients
info = pylsl.StreamInfo('Wally_finder', 'Wally_master', 1, pylsl.IRREGULAR_RATE, pylsl.cf_string, 'Wally_finder_master')
to_clients = pylsl.StreamOutlet(info,1)

# Find all clients
print('Connecting to clients... Press q to start with the connected clients')
clients: typing.Dict[str,pylsl.StreamInlet] = {}
while True:
    found_streams = pylsl.resolve_byprop('type', 'Wally_client', minimum=0, timeout=.1)
    for f in found_streams:
        if not any((clients[s].info().source_id()==f.source_id() for s in clients)):
            h = f.hostname()
            clients[h] = pylsl.StreamInlet(f)
            print(f'client connected: {h} ({f.source_id()})')
            print(f'connected clients: {sorted(clients.keys())}')
    
    if keyboard.is_pressed("q"):
        break
    time.sleep(0.1)
print(f'running with clients: {sorted(clients.keys())}')

# ensure we're properly connected to each client
for h in clients:
    warm_up_bidirectional_comms(to_clients, clients[h])

# get information about the connected eye tracker from each client
to_clients.push_sample(['get_eye_tracker'])
remote_eye_trackers = wait_for_message('eye_tracker', clients)
print(remote_eye_trackers)

# Wait to receive information about calibration results
cal_results = wait_for_message('calibration_done', clients, exit_key='c', verbose=True)
print(cal_results)

# remove clients who dropped out (didn't return a calibration result)
clients = {c:clients[c] for c in clients if cal_results[c] is not None}
print(f'running with clients: {sorted(clients.keys())}')

# Tell clients which other clients they should connect to
for c in clients:
    to_connect = [(cl,*remote_eye_trackers[cl]) for cl in clients if cl!=c]
    msg = f'connect_to,{c},'+json.dumps(to_connect)
    to_clients.push_sample([msg])

# wait for all clients to be ready
wait_for_message('ready_to_go', clients, verbose=True)

# Start experiment
print("Press 'g' to start experiment")
keyboard.wait('g')
to_clients.push_sample(['start_exp'])

# Wait to receive information about search times
search_times = wait_for_message('search_time', clients, exit_key='x', is_json=True, callback=lambda h: tell_to_disconnect(to_clients, h))

# Print reaction times and winners
print('search times:')
print('\n'.join([f'{h}: {t:.2f}{"s" if t and math.isfinite(t) else ""}' for h,t in sorted(search_times.items(), key=lambda item: item[1] or math.inf)]))