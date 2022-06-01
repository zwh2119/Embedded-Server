import shutil
import tarfile

from bottle import *
import json
import device_solution
import timestamp_solution
import os
import run_predict

device_server = Bottle()


def get_error(code, text):
    res = HTTPResponse()
    res.status = code
    res.content_type = 'application/json'
    res.body = json.dumps({'error': text})
    return res


def get_success(dict_content=None):
    res = HTTPResponse()
    res.status = 200
    # print("dict:", dict_content)
    if dict_content is None:
        res.body = 'success'
    else:
        res.content_type = 'application/json'
        res.body = json.dumps(dict_content)
    return res


# @hook('after_request')
# def enable_cors():
#     response.headers['Access-Control-Allow-Origin'] = request.headers.get("Origin")
#     response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,PATCH,HEAD,CONNECT,OPTIONS,TRACE'
#     response.headers[
#         'Access-Control-Allow-Headers'] = 'Origin,Content-Type,Accept,User-Agent,Cookie,Authorization,X-Auth-Token,X-Requested-With'
#     response.headers['Access-Control-Allow-Credentials'] = "true"
#     response.headers['Allow-Control-Expose-Headers'] = 'Signature'
#
#
# @hook('before_request')
# def validate():
#     REQUEST_METHOD = request.environ.get('REQUEST_METHOD')
#
#     HTTP_ACCESS_CONTROL_REQUEST_METHOD = request.environ.get('HTTP_ACCESS_CONTROL_REQUEST_METHOD')
#     if REQUEST_METHOD == 'OPTIONS' and HTTP_ACCESS_CONTROL_REQUEST_METHOD:
#         request.environ['REQUEST_METHOD'] = HTTP_ACCESS_CONTROL_REQUEST_METHOD
#

@device_server.route('/', method='HEAD')
def confirm_link():
    return get_success()


@device_server.get('/')
def get_status_device():
    return get_success(device_solution.get_device_status())


@device_server.get('/ticket')
def get_device_ticket():
    ts = request.params.ts
    # print(ts)
    if ts is None or not timestamp_solution.check_timestamp_format(ts):
        return get_error(400, 'Invalid timestamp')
    auth = timestamp_solution.get_device_ticket(ts)
    # print("auth:", auth)
    return get_success(auth)


@device_server.get('/model')
def get_model():
    model_file = device_solution.get_device_model()
    if not os.path.isfile(model_file):
        return get_error(404, 'No device model')

    file_name = os.path.split(model_file)[1]
    path = os.path.split(model_file)[0]

    download_file = static_file(file_name, root=path, download=True , mimetype='application/octet-stream')

    return download_file


@device_server.put('/model/<algo>')
def put_model(algo):

    if not device_solution.check_algo(algo):
        return get_error(404, 'Algorithm not found')

    signature = request.headers.get("Signature")
    file = request.files.get('model')

    if file is None:
        return get_error(400, 'Invalid request content')

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, 'model')
    # file_name = device_solution.save_device_model(file)
    file.save(temp_path, overwrite=True)
    # print('file:',file_name)
    # print('sig:', signature)
    if signature is None or not timestamp_solution.check_signature(temp_path, signature):
        return get_error(400, 'Invalid signature')

    file.save(f'./device_data/model/{algo}', overwrite=True)
    shutil.rmtree(temp_dir)

    with open('al/algo.json', 'r') as af:
        algo_list = json.load(af)
        cur_algo = algo_list[algo]
    # device_solution.cur_algo = algo
    with open('cur_algo.json', 'w') as f:
        json.dump(cur_algo, f)

    run_predict.start()

    file_type = request.headers.get('Content-Type')

    # if file_type.split(';')[0] != 'multipart/form-data':
    #     return get_error(400, 'Invalid request content')

    return get_success()


@device_server.delete('/model')
def delete_local_model():
    device_solution.clear_device_model()
    return get_success()


@device_server.get('/calibration/pending')
def get_metadata_pending_calibrations():
    with open('al/motions.json', 'r') as file:
        motions = json.load(file)
    result = []
    for motion in motions:
        if not os.path.exists(f'./device_data/calibration/{motion.get("name")}.csv'):
            result.append(motion)

    return get_success(result)


@device_server.post('/calibration/<motion>')
def calibrate_motion(motion):

    with open('al/motions.json', 'r') as file:
        motions = json.load(file)

    for i in motions:
        if i.get('name') == motion:
            duration = i.get('duration', 10)
            break
    else:
        return get_error(400, 'Invalid motion')

    if not device_solution.data_collecting(motion, duration):
        return get_error(409, 'Previous calibration is not finished')

    # device_solution.data_collecting(motion, duration)

    return get_success()


@device_server.get('/calibration')
def get_calibration_data():

    # file = device_solution.get_zip_collected_data()

    if not [x for x in os.listdir('./device_data/calibration') if not x.startswith('.')]:
        return get_error(404, 'No data is collected')
    tar_file = './device_data/calibration.tar.gz'
    with tarfile.open(tar_file, "w:gz") as tar:
        for motion in os.listdir('./device_data/calibration'):
            if not motion.startswith('.'):
                tar.add(name='./device_data/calibration/'+motion, arcname=motion)

    # if file is None:
    #     return get_error(404, 'No data is collected')

    # response.add_header('Signature', timestamp_solution.sign_file(tar))

    download_file = static_file('calibration.tar.gz', root='./device_data', download=True, mimetype='application/x-tar+gzip')
    download_file.set_header('Signature', timestamp_solution.sign_file(tar_file))

    return download_file


@device_server.delete('/calibration')
def delete_calibration_data():

    device_solution.delete_data()

    return get_success()


@device_server.get('/test')
def test_device():
    print(timestamp_solution.hash_file('/root/embedded_server/device_data/calibration.tar.gz'))
    download_file = static_file('calibration.tar.gz', root='/root/embedded_server/device_data', download=True, mimetype='application/x-tar+gzip')
    return download_file


if not run_predict.start():
    print('Predicting program not running..')


if __name__ == '__main__':
    device_server.run(host='0.0.0.0', port=8088, debug=True)
