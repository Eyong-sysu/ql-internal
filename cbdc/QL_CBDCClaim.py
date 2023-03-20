"""
cron: 0 0 1/5 * * ?
new Env('CBDC领取')
"""
import json
import random
import string
import time

import requests

from utils.CBDCUtil import encrypt_sign, get_request_data
from utils.CommonUtil import get_proxy, log, lock
from utils.QLTask import QLTask, main

headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36'
}


class CBDCClaim(QLTask):
    def __init__(self):
        self.total_count = 0
        self.success_count = 0
        self.wait_count = 0
        self.fail_email = []

    def task(self, index, text, api_url):
        split = text.split('----')
        email = split[0]
        device_id = ''
        if len(split) > 2:
            device_id = split[2]
        if device_id == '':
            device_id = "01006" + ''.join(random.sample(string.digits, 10))
        token = split[-1]

        lock.acquire()
        self.total_count += 1
        lock.release()

        log.info(f"【{index}】{email}----正在领取")
        proxy = get_proxy(api_url)

        for i in range(3):
            try:

                timestamp = int(time.time() * 1000)
                data = {"version": 101, "facility": "android", "create_time": timestamp, "deviceid": device_id,
                        "token": token}
                payload = {"timestamp": timestamp, "language": "en",
                           "requestData": get_request_data(json.dumps(encrypt_sign(data)))}
                resp = requests.post("https://www.datacbdc.com/user/miningClaim", json=payload, timeout=15,
                                     headers=headers, proxies={"https": proxy})
                lock.acquire()
                if resp.text.count('Receive successfully') > 0:
                    log.info(f'【{index}】{email}----领取成功')
                    self.success_count += 1
                elif resp.text.count('quest load') > 0:
                    log.info(f'【{index}】{email}----领取时间未到')
                    self.wait_count += 1
                elif resp.text.count('is no block to claim') > 0:
                    log.info(f'【{index}】{email}----无可领取奖励')
                    self.wait_count += 1
                else:
                    lock.release()
                    msg = resp.text
                    if msg.count('msg') > 0:
                        msg = resp.json()['msg']
                    raise Exception(msg)
                lock.release()
                break
            except Exception as ex:
                if repr(ex).count('his account has been banned') > 0:
                    log.error(f'【{index}】{email}----账号封禁')
                    return
                if i != 2:
                    log.error(f'【{index}】{email}----进行第{i + 1}次重试----领取出错：{repr(ex)}')
                    proxy = get_proxy(api_url)
                else:
                    log.error(f'【{index}】{email}----重试完毕----领取出错：{repr(ex)}')
                    self.fail_email.append(f'【{index}】{email}----领取出错：{repr(ex)}')

    def statistics(self):
        if len(self.fail_email) > 0:
            log.info(f"-----Fail Statistics-----")
            log_data = ''
            for fail in self.fail_email:
                log_data += fail + '\n'
            log.error(f'\n{log_data}')

    def save(self):
        pass

    def push_data(self):
        return f'总任务数：{self.total_count}\n任务成功数：{self.success_count}\n时间未到数：{self.wait_count}\n任务失败数：{len(self.fail_email)}'


if __name__ == '__main__':
    main('CBDC领取', CBDCClaim(), 'CBDCToken')
