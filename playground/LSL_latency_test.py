import numpy as np
import TittaPy
import TittaLSLPy
import time
import pebble

nSamp = 5000

sender = None
def startup():
    global sender
    nTry = 0
    while True:
        et = TittaPy.find_all_eye_trackers()
        if et:
            et = et[0]
            break
        nTry += 1
        time.sleep(1)
        if nTry>4:
            raise RuntimeError('No eye tracker found')

    et = TittaPy.EyeTracker(et['address'])

    # Create a TittaLSLPy sender that makes this eye tracker's gaze data stream available on the network
    sender = TittaLSLPy.Sender(et.address)
    sender.create('gaze')
    own_id = sender.get_stream_source_id('gaze')
    print(f'local: {own_id}')

    search_time = 5

    source_ids = []
    t0 = time.monotonic()
    while time.monotonic()-t0<search_time:
        remote_streams = TittaLSLPy.Receiver.get_streams("gaze")
        for r in remote_streams:
            if r["source_id"] not in source_ids:
                source_ids.append(r["source_id"])

    if False:
        return [s for s in source_ids if s!=own_id], et['address']
    else:
        return source_ids, et.address


def measure_local(et_address):
    et = TittaPy.EyeTracker(et_address)
    et.start('gaze')

    # warm up system_timestamp
    for _ in range(10):
        TittaPy.get_system_timestamp()

    # set up data collection
    dat = np.zeros((nSamp,4),dtype='int64')

    i=0
    while i<nSamp:
        samp = et.consume_N('gaze')
        if samp['device_time_stamp'].size>0:
            dat[i,0] = TittaPy.get_system_timestamp()
            dat[i,1] = samp['system_time_stamp'][0]
            dat[i,2] = samp['device_time_stamp'][0]
            dat[i,3] = samp['device_time_stamp'].size
            i = i+1
    
    dat.tofile(f'local.tsv',sep='\t')

    print(f'local: {(dat[:,0]-dat[:,1]).mean()}')


def measure_remote(source_id):
    print(f'running with {source_id}')
    receiver = TittaLSLPy.Receiver(source_id)
    receiver.start()

    # warm up system_timestamp
    for _ in range(10):
        TittaPy.get_system_timestamp()

    dat = np.zeros((nSamp,5),dtype='int64')
    i=0
    while i<nSamp:
        samp = receiver.consume_N()
        if samp['device_time_stamp'].size>0:
            dat[i,0] = TittaPy.get_system_timestamp()
            dat[i,1] = samp['local_system_time_stamp'][0]
            dat[i,2] = samp['remote_system_time_stamp'][0]
            dat[i,3] = samp['device_time_stamp'][0]
            dat[i,4] = samp['device_time_stamp'].size
            i = i+1

    dat.tofile(f'{source_id[-12:]}.tsv',sep='\t')

    print(f'{source_id}: {(dat[:,0]-dat[:,1]).mean()}')


def task_done(future):
    try:
        future.result()  # blocks until results are ready
    except TimeoutError as error:
        print("unstable_function took longer than %d seconds" % error.args[1])
    except pebble.ProcessExpired as error:
        print("%s. Exit code: %d" % (error, error.exitcode))
    except Exception as error:
        print("unstable_function raised %s" % error)
        print(error.traceback)  # Python's traceback of remote process

if __name__ == "__main__":
    remote_sources, local_et_address = startup()
    print(remote_sources)

    futures = []
    with pebble.ProcessPool(max_workers=len(remote_sources)+1) as pool:
        futures.append(pool.schedule(measure_local, [local_et_address]))
        for r in remote_sources:
            futures.append(pool.schedule(measure_remote, [r]))

        for f in futures:
            f.add_done_callback(task_done)