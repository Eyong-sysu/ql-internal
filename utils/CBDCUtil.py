import base64
import hashlib

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


def encrypt_sign(json):
    data = ''
    keys = sorted(json.keys())

    for key in keys:
        data += f'{key}={json[key]}&'
    sign = hashlib.md5(data[:-1].encode('utf-8')).hexdigest()
    json['sign'] = sign
    return json


def get_request_data(data: str):
    key = 's174ed7841fsdf96'.encode('utf-8')
    iv = 'sdfdf1sd5f1dfs1a'.encode('utf-8')
    aes = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
    padding = pad(data.encode('utf-8'), AES.block_size, style='pkcs7')
    return base64.encodebytes(aes.encrypt(padding)).decode('utf-8')
