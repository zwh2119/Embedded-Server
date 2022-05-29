import threading
import subprocess
import os
import device_solution
import time

_task = threading.Thread()
_stop = threading.Event()
cur_result = ''


def predict(algo) -> None:
    global cur_result
    print('Starting collecting')
    proc_data = subprocess.Popen(
        ["/usr/bin/env", "python3" 'collect.py'],
        cwd='db',
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        bufsize=0,
    )
    print('Starting predicting')
    proc_algo = subprocess.Popen(
        ['/usr/bin/env', 'python3', 'predict.py', f'../device_data/model/{algo}'],
        cwd='al',
        stdin=proc_data.stdout,
        stdout=subprocess.PIPE,
        bufsize=0,
    )
    assert proc_algo.stdout
    for line in proc_algo.stdout:
        cur_result = line.decode().strip()
        if _stop.is_set():
            _stop.clear()
            break
    print('Stopping predicting')
    while proc_algo.poll() is None:
        proc_algo.terminate()
        time.sleep(0.5)
        proc_algo.kill()
    print('Stopping collecting')
    while proc_data.poll() is None:
        proc_data.terminate()
        time.sleep(0.5)
        proc_data.kill()


def start() -> bool:
    global _task
    algo = device_solution.cur_algo
    if algo == '' or not os.path.exists(f'device_data/model/{algo}'):
        return False
    if device_solution.running:
        return False
    stop()
    _task = threading.Thread(target=predict, args=(algo,))
    _task.start()
    return True


def stop() -> None:
    global _task, _stop
    if _task and _task.is_alive():
        _stop.set()
        while _task and _task.is_alive():
            time.sleep(0.1)
