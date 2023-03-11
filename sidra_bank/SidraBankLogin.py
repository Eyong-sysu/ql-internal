"""
cron: 1 1 1 1 * ?
new Env('SidraBank登录')
"""
import base64
import re
import time

import requests

from utils.CommonUtil import get_proxy, log, lock, write_txt, get_env
from utils.QLTask import QLTask, main

client_key = get_env("CLIENT_KEY")

if client_key is None or client_key == '':
    log.info("未设置CLIENT_KEY，请设置环境变量CLIENT_KEY后启动")
    exit()


class SidraBankLogin(QLTask):
    def __init__(self):
        self.total_count = 0
        self.success_email = []
        self.fail_email = []

    def task(self, index, text, api_url):
        split = text.split('----')
        email = split[0]
        password = split[1]

        lock.acquire()
        self.total_count += 1
        lock.release()

        log.info(f"【{index}】{email}----正在登录")
        proxy = get_proxy(api_url)
        session = requests.session()
        session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.69',
        }

        for i in range(3):
            try:
                log.info(f"【{index}】{email}----开始处理人机验证")
                user_agent = ''
                cf_turnstile_response = ''
                while True:
                    payload = {
                        'clientKey': client_key,
                        'task': {
                            'type': 'TurnstileTaskProxylessM1',
                            'websiteURL': 'https://www.kycport.com/o/login/',
                            'websiteKey': '0x4AAAAAAABqS91_SXkhEepF'
                        },
                        'softID': 16796
                    }
                    res = requests.post('https://api.yescaptcha.com/createTask', json=payload)
                    if res.text.count('taskId') == 0:
                        if res.text.count('帐户余额不足') > 0:
                            log.error(f'【{index}】{email}----Yes平台帐户余额不足，请充值后再试！')
                            return
                        log.error(f'【{index}】{email}----taskId获取失败，进行重试')
                        continue
                    taskId = res.json()['taskId']
                    log.info(f"【{index}】{email}----taskId: {taskId}")
                    for j in range(30):
                        payload = {'clientKey': client_key, 'taskId': taskId}
                        res = requests.post('https://api.yescaptcha.com/getTaskResult', json=payload)
                        if res.text.count('userAgent') > 0:
                            cf_turnstile_response = res.json()['solution']['token']
                            user_agent = res.json()['solution']['userAgent']
                            log.info(f"【{index}】{email}----人机验证处理成功")
                            break
                        time.sleep(3)
                    if cf_turnstile_response == '':
                        log.error(f'【{index}】{email}----人机验证处理失败，进行重试')
                    break

                session = requests.session()
                session.headers = {
                    'User-Agent': user_agent,
                }
                session.proxies = {"https": proxy}

                resp = session.post('https://www.minesidra.com/api/o/auth/', json={})
                if resp.text.count('url') == 0:
                    raise Exception('KYC链接获取失败')
                resp = session.get(resp.json()['url'], allow_redirects=False)
                cookie = re.findall('__o_data__=(.*); Path',
                                    repr(resp.headers['Set-Cookie']).replace('\\', '').replace('054', ','))[0]
                session.cookies.set('__o_data__', cookie, domain='www.kycport.com', path='/')

                payload = {"email": email, "password": base64.encodebytes(password.encode('utf-8')).decode('utf-8'),
                           "cf-turnstile-response": cf_turnstile_response}
                resp = session.post("https://www.kycport.com/api/user/login/", json=payload, timeout=15)
                if resp.text.count('message') == 0:
                    raise Exception('KYC登录失败')
                if resp.text.count('Login successful') == 0:
                    raise Exception(f'KYC登录失败: {resp.json()["message"]}')

                resp = session.get('https://www.kycport.com/o/accept/', allow_redirects=False)
                url = resp.headers['Location']
                if url.count('minesidra') == 0:
                    raise Exception('Code获取失败')
                resp = session.get(url, allow_redirects=False)
                token = resp.cookies.get("auth")
                resp = requests.get('https://www.minesidra.com/api/user/',
                                    headers={'User-Agent': user_agent, 'Authorization': 'Token ' + token})
                if resp.text.count('email') > 0:
                    log.info(f'【{index}】{email}----登录成功')
                    self.success_email.append(f'{email}----{password}----{token}')
                    break
                else:
                    raise Exception('登录失败')
            except Exception as ex:
                if i != 2:
                    log.error(f'【{index}】{email}----进行第{i + 1}次重试----登录出错：{repr(ex)}')
                    proxy = get_proxy(api_url)
                else:
                    log.error(f'【{index}】{email}----重试完毕----登录出错：{repr(ex)}')
                    self.fail_email.append(f'{password}')

    def statistics(self):
        if len(self.fail_email) > 0:
            log.info(f"-----Fail Statistics-----")
            log_data = ''
            for fail in self.fail_email:
                log_data += fail + '\n'
            log.error(f'\n{log_data}')

    def save(self):
        write_txt("SidraBank", '')
        if len(self.success_email) > 0:
            log.info(f"-----Save Success-----")
            for success in self.success_email:
                write_txt("SidraBankToken", success + '\n', True)
        if len(self.fail_email) > 0:
            log.info(f"-----Save Fail-----")
            for fail in self.fail_email:
                write_txt("SidraBank登录失败", fail + '\n', True)

    def push_data(self):
        return f'总任务数：{self.total_count}\n任务成功数：{len(self.success_email)}\n任务失败数：{len(self.fail_email)}'


if __name__ == '__main__':
    main('SidraBank登录', SidraBankLogin(), 'SidraBank')
