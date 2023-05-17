import hashlib
import random
import string
import time
from urllib.parse import quote

import requests


def get_params(mac: str, did: str, data: str = None):
    params = "os=android&download_channel=GooglePlay&timezone=GMT%2B08%3A00&ui_lang=zh_Hans&ntype=WIFI&pkg=com.meta.avive&version=1.1.1&vcode=21&mac=" + quote(
        mac) + "&operator=CHINA+MOBILE&os_v=28&ede_valid=1&app_channel=GooglePlay&dse_valid=0&open_session=" + quote(
        did) + str(int(time.time())) + "&android_id=" + quote(
        did) + "&brand=OnePlus&device=HD1910&aid=&code_by_sim=CN&did=" + quote(did)
    if data is not None:
        params += "&r_bd_md5=" + hashlib.md5(data.encode('utf-8')).hexdigest()
    return params


def get_headers(url: str, token: str):
    timestamp = str(int(time.time()))
    nonce = "".join(random.sample(string.ascii_letters + string.digits, 20))
    headers = {
        'Authorization': 'HIN ' + token,
        'Request-Sgv': '2',
        'Host': 'api.avive.world',
        'User-Agent': 'okhttp/4.6.0',
        'timestamp': timestamp,
        'nonce': nonce
    }
    payload = {"url": url}
    res = requests.post("https://xiaobooooo.com/avive/api/getHostEnv?timestamp=" + timestamp + "&nonce=" + nonce,
                        json=payload)
    if res.text.count('hostEnv'):
        host_env = res.json()['data']['hostEnv']
        sid = res.json()['data']['sid']
        sig = res.json()['data']['sig']
        headers["Request-Sig"] = sig
        headers["Request-Sid"] = sid
        headers["Host-Env"] = str(host_env)
    return headers
