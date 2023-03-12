"""
cron: 0 30 2/3 * * ?
new Env('SidraBank挖矿')
"""
import time

import requests

from utils.CommonUtil import get_proxy, log, lock, write_txt
from utils.QLTask import QLTask, main


class SidraBankMining(QLTask):
    def __init__(self):
        self.total_count = 0
        self.success_count = 0
        self.unauthorized = []
        self.wait_count = 0
        self.fail_email = []

    def task(self, index, text, api_url):
        split = text.split('----')
        email = split[0]
        password = split[1]
        token = split[-1]
        headers = {
            'Authorization': 'Token ' + token,
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36 Edg/110.0.1587.69'
        }

        lock.acquire()
        self.total_count += 1
        lock.release()

        log.info(f"【{index}】{email}----正在领取")
        proxy = get_proxy(api_url)

        for i in range(3):
            session = requests.session()
            session.headers = headers
            session.proxies = {"https": proxy}
            try:
                resp = session.get("https://www.minesidra.com/api/blockchain/mine/request/", timeout=15)
                print(resp.text)
                if resp.text.count('success') > 0:
                    blockchain_id = resp.json()['data']['id']
                    payload = {"type": 2, "data": {"id": blockchain_id}}
                    res = session.post("https://www.minesidra.com/api/blockchain/mine/submit/", json=payload,
                                       timeout=15)
                    if res.text.count('status') > 0 or res.json()['status'] == 'success':
                        lock.acquire()
                        self.success_count += 1
                        lock.release()
                        break
                    else:
                        msg = resp.text
                        if msg.count('error') > 0:
                            msg = resp.json()['error']
                        raise Exception(msg)
                if resp.text.count('code') > 0 or resp.text.count('code') == 'token_not_valid':
                    self.unauthorized.append(f'{email}----{password}')
                    log.error(f'【{index}】{email}----登录过期')
                    return
                elif resp.text.count('status') > 0 and resp.json()['data']['last_click'] is not None:
                    lock.acquire()
                    self.wait_count += 1
                    lock.release()
                elif resp.text.count('status') == 0 or resp.text.count('status') != 'busy':
                    time.sleep(1)
                    raise Exception('系统繁忙')
                else:
                    msg = resp.text
                    if msg.count('error') > 0:
                        msg = resp.json()['error']
                    raise Exception(msg)
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
        if len(self.unauthorized) > 0:
            log.info(f"-----Unauthorized Statistics-----")
            log_data = ''
            for unauthorized in self.unauthorized:
                log_data += unauthorized + '\n'
            log.error(f'\n{log_data}')

    def save(self):
        if len(self.unauthorized) > 0:
            log.info(f"-----Save Success-----")
            write_txt("SidraBank登录过期", '')
            for unauthorized in self.unauthorized:
                write_txt("SidraBank登录过期", unauthorized + '\n', True)

    def push_data(self):
        return f'总任务数：{self.total_count}\n任务成功数：{self.success_count}\n时间未到数：{self.wait_count}\n登录过期数：{len(self.unauthorized)}\n任务失败数：{len(self.fail_email)}'


if __name__ == '__main__':
    main('SidraBank挖矿', SidraBankMining(), 'SidraBankToken')
