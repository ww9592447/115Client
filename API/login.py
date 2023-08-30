import math
import random
import time
from hashlib import sha1
import base64

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Modules import srequests
from Modules.type import LoginResult, Cookie, QrCode, ChecksCookie


def encrypt_str(text: str) -> str:
    return sha1(text.encode()).hexdigest()


def encrypt(password: str, key: str) -> str:
    rsa_key = RSA.importKey(key)
    cipher = PKCS1_v1_5.new(rsa_key)
    cipher_text = base64.b64encode(cipher.encrypt(password.encode()))
    return cipher_text.decode()


def get_vcode() -> str:
    def _vcode(e: int, t: int) -> str:
        e = hex(e)[2:]
        return e[len(e) - t:] if t < len(e) else (t - len(e))*'0' if t > len(e) else e
    vcode = _vcode(int(int(time.time() * 1000) / 1e3), 8)
    vcode += _vcode(math.floor(123456789 * random.random()) + 1, 5)
    return vcode


def get_ssopw(username: str, password: str, vcode: str) -> str:
    ssopw = sha1((password + username).encode()).hexdigest()
    ssopw += vcode.upper()
    ssopw = sha1(ssopw.encode()).hexdigest()
    return ssopw


def get_pwd_level(password: str) -> int:
    def t(e) -> int:
        _t = 0
        for i in range(4):
            if e & 1:
                _t += 1
            e >>= 1
        return _t

    def o(e) -> int:
        return 1 if 48 <= e <= 57 else 4 if 65 <= e <= 90 else 8

    if len(password) <= 5:
        return 0
    level = 0
    for char in password:
        level |= o(ord(char))
    return t(level) + (1 if len(password) > 8 else 0)


class Login:
    def __init__(self) -> None:
        self.headers = {
            'Origin': 'https://115.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
        }

    # 獲取 cookie 是否有效
    async def checks_cookie(self, cookie: str) -> ChecksCookie:
        headers = self.headers.copy()
        headers.update({'Cookie': cookie})
        url = 'https://proapi.115.com/app/uploadinfo'
        result = await srequests.async_get(url, headers=headers)
        if result is False:
            return ChecksCookie(state=-1, user_id='')
        if result.json()['state'] is False:
            return ChecksCookie(state=0, user_id='')
        return ChecksCookie(state=1, user_id=str(result.json()['user_id']))

    async def login(self, username: str, password: str, usersessionid: str) -> LoginResult:
        headers = self.headers.copy()
        if usersessionid:
            headers['Cookie'] = f'USERSESSIONID={usersessionid}'
        url = 'https://passportapi.115.com/app/1.0/web/5.0.1/login/getKey'
        result = await srequests.async_get(url, headers=headers)
        if result is False:
            return LoginResult(state=False)
        key = result.json()['data']['key']

        _username = encrypt_str(username)
        _password = encrypt_str(password)
        vcode = get_vcode()
        ssopw = get_ssopw(_username, _password, vcode)
        data_time = str(int(time.time()))
        data = {
            'login[ssoent]': 'A1',
            'login[version]': '2.0',
            'login[ssoext]': vcode,
            'login[ssoln]': username,
            'login[pwd_level]': get_pwd_level(password),
            'login[ssovcode]': vcode,
            'login[ssopw]': ssopw,
            'login[safe]': '1',
            'login[time]': '0',
            'login[safe_login]': '0',
            'goto': 'https://115.com/',
            'login[country]': '',
            'country': '',
            'from_browser': '1',
            'cipher_ver': '2',
            'account': username,
            'passwd': encrypt(f'{_password}_{data_time}', base64.b64decode(key).decode('UTF-8')),
            'time': data_time
        }
        url = 'https://passportapi.115.com/app/1.0/web/1.0/login/login'
        result = await srequests.async_post(url, data=data, headers=headers)
        if result is False:
            return LoginResult(state=False)
        data = result.json()
        if data['state'] == 0:
            return LoginResult(
                state=True,
                user_id=data['data']['user_id'],
                mobile=data['data']['mobile'],
                usersessionid=result.cookies['USERSESSIONID'] if 'USERSESSIONID' in result.cookies else usersessionid
            )
        elif data['state'] == 1:
            cookie = data['data']['cookie']
            return LoginResult(
                state=True,
                cookie=Cookie(
                    uid=cookie['UID'],
                    cid=cookie['CID'],
                    seid=cookie['SEID'],
                ),
                user_id=data['data']['user_id'],
            )

        # {'state': 0, 'error': '已开启两步验证登录！', 'errno': 40101010, 'message': '已开启两步验证登录！', 'code': 40101010, 'data': {'user_id': 100103052, 'mobile': '189******89'}}
        # {'state': 1, 'data': {'user_id': 359303516, 'user_name': '359303516', 'email': 'z9592447@qq.com', 'mobile': '886-0987303394', 'country': 'TW', 'is_vip': 1511065375, 'mark': 0, 'alert': '', 'is_chang_passwd': 0, 'is_first_login': 0, 'bind_mobile': 0, 'face': {'face_l': 'https://avatars.115.com/01/30sn3d_l.jpg?v=1692288195', 'face_m': 'https://avatars.115.com/01/30sn3d_m.jpg?v=1692288195', 'face_s': 'https://avatars.115.com/01/30sn3d_s.jpg?v=1692288195'}, 'passwd_reset': 1, 'cookie': {'UID': '359303516_A1_1692288195', 'CID': '82d1a857f58569b9db33d643efe2488d', 'SEID': '72dde8dd103957084c006f2a545f44f5d67a0b2971b7e12973fd71a400452b1a3623d572dd0c0e890b811f5639be33c7bbeac79a12b22509cf1dee58'}}, 'goto': 'https://115.com/'}
        # return res.json()['data']['user_id']

    async def send_code(self, user_id: str) -> bool:
        url = 'https://passportapi.115.com/app/1.0/web/1.0/code/sms/login'
        data = {
            'tpl': 'login_from_two_step',
            'user_id': user_id,
            'cv21': 2
        }
        result = await srequests.async_post(url, data=data, headers=self.headers)
        if result:
            return True
        # {'state': 0, 'error': '已开启两步验证登录！', 'errno': 40101010, 'message': '已开启两步验证登录！', 'code': 40101010, 'data': {'user_id': 100103052, 'mobile': '189******89'}}
        return False

    async def login_verify(self, user_id: str, code: str) -> LoginResult:
        url = 'https://passportapi.115.com/app/1.0/web/1.0/login/vip'
        data = {
            'account': user_id,
            'code': code
        }
        result = await srequests.async_post(url, data=data, headers=self.headers)
        if result is False:
            return LoginResult(state=False)
        data = result.json()
        if data['state'] == 0:
            return LoginResult(state=True, user_id='')
        elif data['state'] == 1:
            cookie = result.cookies
            return LoginResult(
                state=True,
                cookie=Cookie(
                    uid=cookie['UID'],
                    cid=cookie['CID'],
                    seid=cookie['SEID'],
                ),
                user_id=user_id
            )

        # {'state': 0, 'error': '短信验证码错误', 'errno': 40103003, 'message': '短信验证码错误', 'code': 40103003}
        # {'state': 1, 'data': {'user_id': 359303516, 'user_name': '359303516', 'email': 'z9592447@qq.com', 'mobile': '886-0987303394', 'country': 'TW', 'is_vip': 1511065375, 'mark': 0, 'alert': '', 'is_chang_passwd': 0, 'is_first_login': 0, 'bind_mobile': 0, 'face': {'face_l': 'https:\\/\\/avatars.115.com\\/01\\/30sn3d_l.jpg?v=1692675913', 'face_m': 'https:\\/\\/avatars.115.com\\/01\\/30sn3d_m.jpg?v=1692675913', 'face_s': 'https:\\/\\/avatars.115.com\\/01\\/30sn3d_s.jpg?v=1692675913'}, 'passwd_reset': 1, 'cookie': {'UID': '359303516_A1_1692675913', 'CID': 'e37fd45f5556b8d775c58d70e3bd627b', 'SEID': 'db32cd7032500660f5e2f0b80f0ec26b973f317556de605c51461c54654548df8fdad96cadb60e19b6f049cdf33a428e94bfaeef9e9a07e4681d2388'}}}

    async def get_qr_code(self) -> QrCode:
        url = 'https://qrcodeapi.115.com/api/1.0/web/1.0/token'
        result = await srequests.async_get(url, headers=self.headers)
        if result is False:
            return QrCode(state=False)
        data = result.json()['data']
        return QrCode(
            state=True,
            uid=data['uid'],
            time=data['time'],
            sign=data['sign'],
            url=data['qrcode'],
        )

    async def get_qr_code_status(self, qr_code: QrCode) -> int:
        url = 'https://qrcodeapi.115.com/get/status/'
        data = {
            'uid': qr_code['uid'],
            'time': qr_code['time'],
            'sign': qr_code['sign'],
            '_': int(time.time())
        }
        result = await srequests.async_get(url, params=data, headers=self.headers, timeout=35)
        if result is False:
            return -1
        data = result.json()
        if data['state'] == 0:
            return 0
        elif data['state'] == 1 and data['data'] == {}:
            return 1
        elif data['state'] == 1 and data['data']['status'] == 1:
            return 2
        elif data['state'] == 1 and data['data']['status'] == 2:
            return 3

    async def qr_code_login(self, account: str) -> LoginResult:
        url = 'https://passportapi.115.com/app/1.0/web/1.0/login/qrcode'
        data = {
            'account': account,
            'app': 'web'
        }
        result = await srequests.async_post(url, data=data, headers=self.headers)
        if result is False:
            return LoginResult(state=True)
        data = result.json()
        return LoginResult(
            state=True,
            usersessionid=result.cookies['USERSESSIONID'],
            cookie=Cookie(
                uid=data['data']['cookie']['UID'],
                cid=data['data']['cookie']['CID'],
                seid=data['data']['cookie']['SEID'],
            ),
            user_id=data['data']['user_id'],

        )
