"""
cron: 0 0 1/3 * * ?
new Env('微信阅读1')
"""
import random
import string
import time

import requests

from utils.CommonUtil import get_proxy, log, lock
from utils.QLTask import QLTask, main

base_url = 'http://m.souzfvy.cn/'
res = requests.get('https://qun.haozhuang.cn.com/fq_url/rk')
if res.text.count('jump'):
    baseUrl = res.json()['jump']
log.info(f'当前BaseUrl: {base_url}')


class WXRead(QLTask):
    def __init__(self):
        self.total_count = 0
        self.success = []
        self.fail = []

    def task(self, index, text, api_url):
        split = text.split('----')
        nickname = split[0]
        cookies = split[-1]
        if cookies.lower().startswith('cookie:'):
            cookies = cookies.split(':')[1]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x6309001c) XWEB/6500',
            'Cookie': cookies.strip()
        }

        lock.acquire()
        self.total_count += 1
        lock.release()

        log.info(f"【{index}】{nickname}----开始完成阅读任务")
        session = requests.session()
        session.headers = headers

        proxy = get_proxy(api_url)
        error_count = 0

        while True:
            for i in range(3):
                try:
                    session.proxies = {"http": proxy, "https": proxy}
                    resp = session.get(base_url + "tuijian/do_read?for=&zs=&pageshow&r=0." + ''.join(
                        random.sample(string.digits + string.digits, 16)))
                    if not resp.text.count('url'):
                        raise Exception('阅读地址获取失败')
                    url = resp.json()['url']
                    if url == '/':
                        log.info(f'【{index}】{nickname}----本小时阅读完成')
                        self.success.append(nickname)
                        return
                    jkey = resp.json()['jkey']
                    if url.count('mp.weixin.qq.com'):
                        session.get(url)
                    else:
                        params = resp.json()['url'].split('Fjumpid%3D')[1]
                        code = '0' + str(random.randint(1, 9)) + ''.join(
                            random.sample(string.digits + string.ascii_letters, 30))
                        session.get(base_url + 'fast_reada/oiejr?code=' + code + '&jumpid=' + params)
                    log.info(f'【{index}】{nickname}----阅读文章中......')
                    time.sleep(5)
                    resp = session.get(base_url + 'tuijian/do_read?for=&zs=&pageshow&r=0.' + ''.join(
                        random.sample(string.digits + string.digits, 16)) + '&jkey=' + jkey)
                    if resp.text.count('success_msg'):
                        log.info(f'【{index}】{nickname}----{resp.json()["success_msg"]}')
                        break
                    msg = resp.text
                    if msg.count('msg'):
                        msg = resp.json()['msg']
                    raise Exception(msg)
                except Exception as ex:
                    error_count += 1
                    if error_count > 10:
                        log.error(f'【{index}】{nickname}----连续10次出错，停止阅读')
                        self.fail.append(f'{nickname}----{repr(ex)}----连续10次出错，停止阅读')
                        return
                    log.error(f'【{index}】{nickname}----1秒后重试----阅读出错：{repr(ex)}')
                    proxy = get_proxy(api_url)
                    time.sleep(1)

    def statistics(self):
        if len(self.fail) > 0:
            log.info(f"-----Fail Statistics-----")
            log_data = ''
            for fail in self.fail:
                log_data += fail
            log.error(f'\n{log_data}')

    def save(self):
        pass

    def push_data(self):
        return f'总任务数：{self.total_count}\n任务成功数：{len(self.success)}\n任务失败数：{len(self.fail)}'


if __name__ == '__main__':
    main('微信阅读1', WXRead(), 'WXRead1')
