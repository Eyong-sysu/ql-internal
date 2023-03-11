"""
cron: 1 1 1 1 * ?
new Env('CBDC登录')
"""
import json
import random
import string
import time

import requests

from utils.CBDCUtil import encrypt_sign, get_request_data
from utils.CommonUtil import get_proxy, log, lock, write_txt
from utils.QLTask import QLTask, main

headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36'
}


class CBDCLogin(QLTask):
    def __init__(self):
        self.total_count = 0
        self.success_email = []
        self.violation_email = []
        self.fail_email = []

    def task(self, index, text, api_url):
        split = text.split('----')
        email = split[0]
        password = split[1]
        device_id = ''
        if len(split) > 2:
            device_id = split[2]
        if device_id == '':
            device_id = "01006" + ''.join(random.sample(string.digits, 10))

        lock.acquire()
        self.total_count += 1
        lock.release()

        log.info(f"【{index}】{email}----正在登录")
        proxy = get_proxy(api_url)

        for i in range(3):
            try:

                timestamp = int(time.time() * 1000)
                data = {"email": email, "password": password, "version": 101, "facility": "android",
                        "create_time": timestamp, "deviceid": device_id}

                payload = {"timestamp": timestamp, "language": "en",
                           "requestData": get_request_data(json.dumps(encrypt_sign(data)))}
                resp = requests.post("https://www.datacbdc.com/login/loginAccount", json=payload, timeout=15,
                                     headers=headers, proxies={"https": proxy})
                if resp.text.count('Login success') > 0:
                    token = resp.json()['data']
                    self.success_email.append(f'{email}----{password}----{device_id}----{token}')
                    log.info(f'【{index}】{email}----登录成功')
                    break
                else:
                    msg = resp.text
                    if msg.count('msg') > 0:
                        msg = resp.json()['msg']
                    raise Exception(msg)
            except Exception as ex:
                if repr(ex).count('The account cannot be logged') > 0:
                    log.error(f'【{index}】{email}----账号封禁')
                    self.violation_email.append(f'{email}----{password}')
                if i != 2:
                    log.error(f'【{index}】{email}----进行第{i + 1}次重试----登录出错：{repr(ex)}')
                    proxy = get_proxy(api_url)
                else:
                    log.error(f'【{index}】{email}----重试完毕----登录出错：{repr(ex)}')
                    self.fail_email.append(f'{email}----{password}----{device_id}----登录出错：{repr(ex)}')

    def statistics(self):
        if len(self.violation_email) > 0:
            log.info(f"-----Violation Statistics-----")
            log_data = ''
            for violation in self.violation_email:
                log_data += violation + '\n'
            log.error(f'\n{log_data}')

        if len(self.fail_email) > 0:
            log.info(f"-----Fail Statistics-----")
            log_data = ''
            for fail in self.fail_email:
                log_data += fail + '\n'
            log.error(f'\n{log_data}')

    def save(self):
        write_txt("CBDC", '')
        if len(self.success_email) > 0:
            log.info(f"-----Save Success-----")
            for success in self.success_email:
                write_txt("CBDCToken", success + '\n', True)
        if len(self.violation_email) > 0:
            log.info(f"-----Save Blocked-----")
            for violation in self.violation_email:
                write_txt("CBDC已封禁", violation + '\n', True)
        if len(self.fail_email) > 0:
            log.info(f"-----Save Fail-----")
            for fail in self.fail_email:
                write_txt("CBDC登录失败", fail + '\n', True)

    def push_data(self):
        return f'总任务数：{self.total_count}\n任务成功数：{len(self.success_email)}\n封禁账号数：{len(self.violation_email)}\n任务失败数：{len(self.fail_email)}'


if __name__ == '__main__':
    main('CBDC登录', CBDCLogin(), 'CBDC')
