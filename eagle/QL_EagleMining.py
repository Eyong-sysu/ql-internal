"""
cron: 0 30 2/5 * * ?
new Env('Eagle挖矿')
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
    'Content-Type': 'application/json; charset=utf-8',
    'UserAgent': 'android 1.0.65',
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; HD1910 Build/PQ3B.190801.002)',
}

class EagleMining(QLTask):
    def __init__(self):
        self.total_count = 0
        self.success_count = 0
        self.wait_count = 0
        self.fail_email = []

    def task(self, index, text, api_url):
        hd = headers
        split = text.split('----')
        email = split[0]
        hd['AuthToken'] = split[-1]

        lock.acquire()
        self.total_count += 1
        lock.release()

        log.info(f"【{index}】{email}----启动挖矿中")
        proxy = get_proxy(api_url)

        for i in range(3):
            try:
                timestamp = int(time.time() * 1000)
                payload = {}
                resp = requests.post("https://eaglenetwork.app/api/start-mining", json=payload, timeout=15,
                                     headers=headers, proxies={"https": proxy})
                lock.acquire()
                if resp.text.count('start_time') > 0:
                    log.info(f'【{index}】{email}----挖矿成功')
                    self.success_count += 1
                elif resp.text.count('Mining Already Started') > 0:
                    log.info(f'【{index}】{email}----挖矿时间未到')
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
    main('Eagle挖矿', EagleMining(), 'EagleToken')
