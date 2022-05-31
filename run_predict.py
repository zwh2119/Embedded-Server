import json
import threading
import subprocess
import os
import device_solution
import time

_task = threading.Thread()
_stop = threading.Event()
cur_result = ''


def predict(algo_inf) -> None:
    global cur_result
    pos_dir = os.path.abspath('./al')
    entry_point = algo_inf['entrypoint']['predict']
    entry_point = [x.replace('$ALGO', pos_dir) for x in entry_point]
    entry_point.append(f'../device_data/model/{algo_inf["name"]}')
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
        entry_point,
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
    with open('al/algo.json', 'r') as f:
        algo_list = json.load(f)
    algo = device_solution.cur_algo
    algo_inf = algo_list[algo] if algo != '' else {}
    if algo == '' or not os.path.exists(f'device_data/model/{algo}'):
        print('-No device model')
        return False
    if device_solution.running:
        print('-Prediction is Running')
        return False
    stop()
    _task = threading.Thread(target=predict, args=(algo_inf,))
    _task.start()
    print('Run predicting')
    return True


def stop() -> None:
    global _task, _stop
    if _task and _task.is_alive():
        _stop.set()
        while _task and _task.is_alive():
            time.sleep(0.1)
