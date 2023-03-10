"""
cron: 0 0 2/3 * * ?
new Env('Tockt挖矿')
"""
import requests

from utils.CommonUtil import get_proxy, log, lock
from utils.QLTask import QLTask, main

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36'
}


class TocktMining(QLTask):
    def __init__(self):
        self.total_count = 0
        self.success_count = 0
        self.wait_count = 0
        self.fail_email = []

    def task(self, index, text, api_url):
        split = text.split('----')
        email = split[0]
        token = split[len(split) - 1]

        lock.acquire()
        self.total_count += 1
        lock.release()

        log.info(f"【{index}】{email}----正在挖矿")
        proxy = get_proxy(api_url)

        for i in range(3):
            try:
                requests.post("https://www.tockt.com:8443/Go/GetPower", data="uid=" + token + "&langu=1", timeout=15,
                              headers=headers, proxies={"https": proxy})
                resp = requests.post("https://www.tockt.com:8443/GO/ClickGo", data="uid=" + token + "&langu=1",
                                     timeout=15, headers=headers, proxies={"https": proxy})
                lock.acquire()
                if resp.text.count('成功') == 0:
                    if resp.text.count('你已启动挖矿请勿重') == 0:
                        lock.release()
                        raise Exception(resp.text)
                    else:
                        log.info(f'【{index}】{email}----未到挖矿时间')
                        self.wait_count += 1
                else:
                    log.info(f'【{index}】{email}----挖矿成功')
                    self.success_count += 1
                lock.release()
                break
            except Exception as ex:
                if i != 2:
                    log.info(f'【{index}】{email}----进行第{i + 1}次重试----挖矿出错：{repr(ex)}')
                    proxy = get_proxy(api_url)
                else:
                    log.info(f'【{index}】{email}----重试完毕----挖矿出错：{repr(ex)}')
                    self.fail_email.append(f'【{index}】{email}----挖矿出错：{repr(ex)}')

    def statistics(self):
        if len(self.fail_email) > 0:
            log.info(f"-----Fail Statistics-----")
            log_data = ''
            for fail in self.fail_email:
                log_data += fail
            log.error(f'\n{log_data}')

    def save(self):
        pass

    def push_data(self):
        return f'总任务数：{self.total_count}\n任务成功数：{self.success_count}\n时间未到数：{self.wait_count}\n任务失败数：{len(self.fail_email)}'


if __name__ == '__main__':
    main('Tockt挖矿', TocktMining(), 'TocktToken')
