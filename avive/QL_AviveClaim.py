"""
cron: 0 0 8/8 * * ?
new Env('Avive领取空投')
"""
import requests

from utils.AviveUtil import get_params, get_headers
from utils.CommonUtil import get_proxy, log, lock
from utils.QLTask import QLTask, main


class AviveClaim(QLTask):
    def __init__(self):
        self.total_count = 0
        self.success_count = 0
        self.fail_email = []

    def task(self, index, text, api_url):
        split = text.split('----')
        email = split[0]
        mac = split[-3]
        did = split[-2]
        token = split[-1]

        lock.acquire()
        self.total_count += 1
        lock.release()

        log.info(f"【{index}】{email}----正在领取")
        proxy = get_proxy(api_url)

        for i in range(3):
            try:
                url = "https://api.avive.world/v1/mint/collect/?" + get_params(mac, did)
                resp = requests.post(url, headers=get_headers(url, token), proxies={"https": proxy})
                lock.acquire()
                if resp.text.count('code') and resp.json()['code'] == 0 and resp.text.count('{}'):
                    log.info(f'【{index}】{email}----开启成功')
                    self.success_count += 1
                else:
                    lock.release()
                    msg = resp.text
                    if msg.count('err_msg') > 0:
                        msg = resp.json()['err_msg']
                    raise Exception(msg)
                lock.release()
                break
            except Exception as ex:
                if i != 2:
                    log.error(f'【{index}】{email}----进行第{i + 1}次重试----开启出错：{repr(ex)}')
                    proxy = get_proxy(api_url)
                else:
                    log.error(f'【{index}】{email}----重试完毕----开启出错：{repr(ex)}')
                    self.fail_email.append(f'【{index}】{email}----开启出错：{repr(ex)}')

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
        return f'总任务数：{self.total_count}\n任务成功数：{self.success_count}\n任务失败数：{len(self.fail_email)}'


if __name__ == '__main__':
    main('Avive领取空投', AviveClaim(), 'AviveToken')
