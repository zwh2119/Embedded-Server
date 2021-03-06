import json
import os
import threading
import time
import subprocess
import run_predict
import uuid

running = False

# with open('al/algo.json', 'r') as f:
#     tmp_algo_list = json.load(f)
# cur_algo = list(tmp_algo_list.keys())[0] if list(tmp_algo_list.keys()) != [] else ''



def get_device_status():
    with open('id', 'r') as f:
        dev_id = uuid.UUID(f.read().strip())

    with open('cur_algo.json', 'r') as f:
        cur_algo = json.load(f)
    status = {
        "id": str(dev_id),  # string, the device UUID
        "battery": 90,  # int, percentage of battery
        "charging": True,  # bool, true if power connected
        "algorithm": cur_algo,
        "prediction": run_predict.cur_result,  # string, the current detected motion
    }
    return status


def get_device_model():
    with open('cur_algo.json', 'r') as f:
        cur_algo = json.load(f)

    return f"./device_data/model/{cur_algo['name']}"


def clear_device_model():
    model_dir = './device_data/model'
    for model in os.listdir(model_dir):
        model_path = os.path.join(model_dir, model)
        if os.path.isfile(model_path):
            os.unlink(model_path)
            print(f'delete model {model_path}')
        else:
            print(f'{model_path} error')


# def save_device_model(file):
#     file.save('./device_data/model', overwrite=True)
#     return './device_data/model'


def collect_one_data(motion, duration):
    global running
    running = True
    run_predict.stop()

    print(f'Starting calibrating {motion}')
    file = open(f'./device_data/calibration/{motion}.csv', 'w')
    proc = subprocess.Popen(
        ["/usr/bin/env", "python3", 'collect.py'],
        cwd='db',
        stdin=subprocess.DEVNULL,
        stdout=file,
    )
    time.sleep(duration)
    print(f'Stopping calibrating {motion}')
    while proc.poll() is None:
        proc.terminate()
        time.sleep(0.5)
        proc.kill()
    running = False
    run_predict.start()


def data_collecting(motion, duration):
    if running:
        return False
    threading.Thread(
        target=collect_one_data,
        args=(motion, duration)
    ).start()
    return True


def get_current_motion_data():
    sample = [
        {
            "name": "walk",  # the motion name, [a-z]+
            "duration": 20,  # the duration of recording requested
            "display": "walk",  # the displayed name of motion
            "desc": "Please walk on a firm and level ground"  # the displayed description of motion
        },
        # .....
    ]
    return sample


def check_motion_name(motion):
    return True


def get_zip_collected_data():
    return "server_tmp/desktop.jpg"


def delete_data():
    file_path = './device_data/calibration/'
    for file in os.listdir(file_path):
        if not file.startswith('.'):
            os.unlink(os.path.join(file_path, file))
    if os.path.exists('./device_data/calibration.tar.gz'):
        os.unlink('./device_data/calibration.tar.gz')


def check_algo(algo):
    try:
        with open('al/algo.json', 'r') as f:
            al_list = json.load(f)
            return algo in al_list.keys()
    except:
        return False

