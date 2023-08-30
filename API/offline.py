import time

from Modules.type import Credential
from Modules import srequests


class Offline:
    def __init__(self, credential: Credential) -> None:
        # 設置115標頭
        self.headers = credential['headers']
        # 設置用戶id
        self.user_id: str = credential['user_id']
        self.sign: str | None = None
        self.time: str | None = None

    # 獲取離線下載所需資料
    async def get_sign_and_time(self) -> bool:
        result = await srequests.async_get('https://115.com/?ct=offline&ac=space', headers=self.headers)
        if result:
            result = result.json()
            self.sign = result['sign']
            self.time = result['time']
            return True
        return False

    # 添加離線任務
    async def add_offline(self, url: str | list[str, ...], cid: str = '') -> int:
        if self.sign is None:
            if await self.get_sign_and_time() is False:
                return False
        form_data = {
            'savepath': '',
            'wp_path_id': cid,
            'uid': self.user_id,
            'sign': self.sign,
            'time': self.time,
        }
        offline_url = 'https://115.com/web/lixian/?ct=lixian&ac=add_task_url'
        if isinstance(url, str):
            form_data.update({'url': url})
            result = await srequests.async_post(offline_url, headers=self.headers, data=form_data)
        else:
            for index, _url in zip(range(len(url)), url):
                form_data.update({f'url[{index}]': _url})
            result = await srequests.async_post(offline_url + 's', headers=self.headers, data=form_data)
        if result is False:
            return -1
        data = result.json()
        if data['state'] is False:
            return 0
        elif data['state'] is True:
            return 1

    # 刪除單個離線
    async def offline_delete(self, _hash: str) -> bool:
        if self.sign is None:
            if await self.get_sign_and_time() is False:
                return False
        data = {'hash[0]': _hash, 'uid': self.user_id, 'sign': self.sign, 'time': self.time}
        url = 'https://115.com/web/lixian/?ct=lixian&ac=task_del'
        result = await srequests.async_post(url, headers=self.headers, data=data)
        if result:
            return True
        return False

    async def security(self) -> tuple[str, str] | bool:
        cb = f'Close911_{int(time.time() * 1000)}'
        url = f'https://captchaapi.115.com/?ac=security_code&type=web&cb={cb}'
        result = srequests.get(url, headers=self.headers)
        if result:
            for cookie in result.cookies:
                sign = cookie.value
                self.headers['Cookie'] += f'; PHPSESSID={sign}'
                return cb, sign
        return False

    # 獲取要輸入的圖片文字
    async def verification_code(self) -> bytes | bool:
        url = f'https://captchaapi.115.com/?ct=index&ac=code&ctype=0&_t={int(time.time() * 1000)}'
        result = await srequests.async_get(url, headers=self.headers)
        if result:
            return result.content
        return False

    async def verification_map(self) -> bytes | bool:
        url = f'https://captchaapi.115.com/?ct=index&ac=code&t=all&_t={int(time.time() * 1000)}'
        result = await srequests.async_get(url, headers=self.headers)
        if result:
            return result.content
        return False

    # 提交驗證
    async def captcha(self, code: str, sign: str, cb: str) -> int:
        data = {
            'code': code,
            'sign': sign,
            'ac': 'security_code',
            'type': 'web',
            'cb': cb,
        }
        url = 'https://webapi.115.com/user/captcha'
        result = await srequests.async_post(url, headers=self.headers, data=data)
        if result is False:
            return -1
        data = result.json()
        if data['state'] is False:
            return 0
        elif data['state'] is True:
            return 1

    # 刪除全部離線
    async def offline_clear(self) -> bool:
        data = {'flag': 1}
        url = 'https://115.com/web/lixian/?ct=lixian&ac=task_clear'
        result = await srequests.async_post(url, headers=self.headers, data=data)
        if result:
            return True
        return False

    # 離線進度
    async def offline_schedule(self) -> dict[str, any] | bool:
        url = 'https://115.com/web/lixian/?ct=lixian&ac=task_lists'
        result = await srequests.async_get(url, headers=self.headers)
        if result:
            return result.json()
        return False
