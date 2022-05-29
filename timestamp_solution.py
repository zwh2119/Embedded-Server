import re
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
import hashlib


def device_cert() -> str:

    with open('device.crt', 'r') as f:
        return f.read().strip()


def device_key() -> SigningKey:
     with open('device.key', 'rb') as f:
        return SigningKey(f.read())


def ca_key() -> VerifyKey:
    with open('ca.pub', 'rb') as f:
        return VerifyKey(f.read())


def hash_file(file: str) -> str:
    h = hashlib.sha256()
    with open(file, 'rb') as f:
        while True:
            chunk = f.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def check_timestamp_format(ts):
    return re.match(r'^[1-9][0-9]*:[0-9a-f]{40}$', ts)


def sign(data: str) -> str:
    return device_key().sign(data.encode(), encoder=HexEncoder).signature.decode()


def get_device_ticket(ts):
    print("device_crt: ", device_cert())
    return ts + ':' + sign(ts) + ':' + device_cert()


def check_signature(file: str, sig: str):
    try:
        ca_key().verify(hash_file(file).encode(), HexEncoder().decode(sig.encode()))
        return True
    except:
        # raise error.SignatureError('Invalid signature for model file')
        return False


def sign_file(file: str) -> str:
    print("device hash file:", hash_file(file))
    return sign(hash_file(file))+':'+device_cert()
