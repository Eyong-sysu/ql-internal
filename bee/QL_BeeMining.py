"""
cron: 0 30 1/3 * * ?
new Env('BeeNetwork挖矿')
"""
import requests

from utils.CommonUtil import get_proxy, log, lock
from utils.QLTask import QLTask, main


def get_client_info():
    client_info = {"l": "zh_Hans", "s": "default", "os": "android", "a": "Bee.com", "p": "games.bee.app",
                   "v": "1.7.7.1482", "b": "1482"}
    return client_info


def get_headers(token=None):
    headers = {"cf-country": "HK", "build-number": "1482"}
    if token is not None and token != '':
        headers['Authorization'] = "Bearer {}".format(token)
    return headers


class BeeNetworkMining(QLTask):
    def __init__(self):
        self.total_count = 0
        self.success_count = 0
        self.wait_count = 0
        self.unauthorized = []
        self.fail_email = []

    def task(self, index, text, api_url):
        split = text.split('----')
        email = split[0]
        token = split[len(split) - 1]

        lock.acquire()
        self.total_count += 1
        lock.release()

        log.info(f"【{index}】{email}----正在挖矿")
        headers = get_headers(token)

        proxy = get_proxy(api_url)

        for i in range(3):
            try:
                resp = requests.post("https://api.bee9527.com/v2/user/mine", params={'clientInfo': get_client_info()},
                                     headers=headers, timeout=15, proxies={"https": proxy})
                if resp.text.count('UnauthorizedError') > 0:
                    log.error(f'【{index}】{email}----登录过期----挖矿失败')
                    self.unauthorized.append(f'{email}')
                    return

                if resp.text.count('balance') == 0:
                    raise Exception(resp.text)
                else:
                    lock.acquire()
                    if resp.json()['data']['new']:
                        log.info(f'【{index}】{email}----挖矿成功')
                        self.success_count += 1
                    else:
                        log.info(f'【{index}】{email}----挖矿时间未到')
                        self.wait_count += 1
                    lock.release()
                break
            except Exception as ex:
                if i != 2:
                    log.error(f'【{index}】{email}----进行第{i + 1}次重试----挖矿出错：{repr(ex)}')
                    proxy = get_proxy(api_url)
                else:
                    log.error(f'【{index}】{email}----重试完毕----挖矿出错：{repr(ex)}')
                    self.fail_email.append(f'【{index}】{email}----挖矿出错：{repr(ex)}')

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
        pass

    def push_data(self):
        return f'总任务数：{self.total_count}\n任务成功数：{self.success_count}\n时间未到数：{self.wait_count}\n任务失败数：{len(self.fail_email)}'


if __name__ == '__main__':
    main('BeeNetwork挖矿', BeeNetworkMining(), 'BeeNetworkToken')
