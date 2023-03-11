import base64
import re
from urllib.parse import quote

import requests

session = requests.session()
session.cookies.set('sessionid', 'we41pwz0ayc8x6i11smxzh55upi3ryo1', domain='www.kycport.com', path='/')

resp = session.post('https://www.minesidra.com/api/o/auth/', json={})
if resp.text.count('url') == 0:
    raise Exception('KYC链接获取失败')
resp = session.get(resp.json()['url'], allow_redirects=False)

# print(session.cookies.get('__o_data__'))
# print(re.findall('state: (.*)}:', session.cookies.get('__o_data__')))
# state = re.findall('state: (.*)}:', session.cookies.get('__o_data__'))[0]
# aa = re.findall('}:(.*)"', session.cookies.get('__o_data__'))[0]
# session.cookies.set('__o_data__',
#                     '"{\"response_type\": \"code\"\054 \"client_id\": \"minesidra\"\054 \"redirect_uri\": \"https://www.minesidra.com/api/o/callback/\"\054 \"scope\": \"read\"\054 \"state\": \"' + state + '\"}:' + aa + '"',
#                     domain='www.kycport.com', path='/')
print(session.cookies)
print(repr(resp.headers['Set-Cookie']))
print(repr(resp.cookies.get('__o_data__')))
cookie = re.findall('__o_data__=(.*); Path', repr(resp.headers['Set-Cookie']).replace('\\', '').replace('054', ','))[0]
print(cookie)
session.cookies.set('__o_data__', cookie, domain='www.kycport.com', path='/')
resp = session.get('https://www.kycport.com/o/accept/', allow_redirects=False)
print(resp.headers['Location'])
print(resp.cookies)

resp = requests.get(resp.headers['Location'], allow_redirects=False, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.69'})
print(resp.text)
print(f'headers: {resp.headers}')
print(f'cookies1: {resp.cookies}')
print(f'cookies2: {session.cookies}')
print(f'auth1: {resp.cookies.get("auth")}')
print(f'auth2: {session.cookies.get("auth")}')
