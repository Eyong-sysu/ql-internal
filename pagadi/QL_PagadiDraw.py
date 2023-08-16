"""
cron: 0 33 3 * * ?
new Env('Pagadi抽奖')
"""
import requests

from utils.CommonUtil import get_proxy, log, lock
from utils.QLTask import QLTask, main


class PagadiDraw(QLTask):
    def __init__(self):
        self.total_count = 0
        self.success_count = 0
        self.fail_email = []

    def task(self, index, text, api_url):
        split = text.split('----')
        email = split[0]
        token = split[len(split) - 1]

        lock.acquire()
        self.total_count += 1
        lock.release()

        log.info(f"【{index}】{email}----正在抽奖")
        session = requests.session()
        session.headers = {
            'Authorization': 'Bearer ' + token,
            'language': 'cht',
            'get-time-zone': 'Asia/Shanghai',
            'user-agent': 'Mozilla/5.0 (Linux; Android 9; HD1910 Build/PQ3B.190801.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 uni-app Html5Plus/1.0 (Immersed/24.0)'
        }
        proxy = get_proxy(api_url)

        for i in range(3):
            session.proxies = {"https": proxy}
            try:
                resp = session.get("https://www.pagadi.vip/api/raffle/1")
                if resp.text.count('status') and resp.json()['code'] == 200:
                    log.info(f'【{index}】{email}----抽奖成功：' + resp.json()['data']['value'])
                    lock.acquire()
                    self.success_count += 1
                    lock.release()
                    break
                elif resp.text.count('status') and resp.json()['message'] == '抽獎次數不足':
                    log.info(f'【{index}】{email}----抽獎次數不足')
                    break
                elif resp.text.count('message'):
                    raise Exception(resp.json()['message'])
                raise Exception(resp.text)
            except Exception as ex:
                if i != 2:
                    log.error(f'【{index}】{email}----进行第{i + 1}次重试----签到出错：{repr(ex)}')
                    proxy = get_proxy(api_url)
                else:
                    log.error(f'【{index}】{email}----重试完毕----签到出错：{repr(ex)}')
                    self.fail_email.append(f'【{index}】{email}----签到出错：{repr(ex)}')

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
    main('Pagadi抽奖', PagadiDraw(), 'PagadiToken')
