from Modules.type import Credential
from Modules import srequests


class Share:
    def __init__(self, credential: Credential) -> None:
        # 設置115標頭
        self.headers = credential['headers']
        # 設置用戶id
        self.uid = credential['user_id']

    # 獲取分享列表
    async def get_share(self, offset: int, limit: int) -> dict[str, any] | bool:
        url = f'https://webapi.115.com/share/slist?user_id=100103052&offset={offset}&limit={limit}'
        result = await srequests.async_get(url, headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 獲取指定分享資料
    async def get_share_data(self, share_code: str) -> dict[str, any] | bool:
        url = f'https://webapi.115.com/share/shareinfo?share_code={share_code}'
        result = await srequests.async_get(url, headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 設置分享
    async def set_share(self, cid: str) -> dict[str, any] | bool:
        url = 'https://webapi.115.com/share/send'

        data = {
            'user_id': self.uid,
            'file_ids': cid,
            'ignore_warn': '1',
            'is_asc': '1',
            'order': 'file_name',
        }
        result = await srequests.async_post(url, data=data, headers=self.headers, timeout=10, retry=5)
        if result:
            return result.json()
        return False

    async def set_share_time(self, share_code: str, share_time: int) -> bool:
        url = 'https://webapi.115.com/share/updateshare'
        if share_time not in (1, 7, -1):
            return False
        data = {
            'share_code': share_code,
            'share_duration': share_time
        }
        result = await srequests.async_post(url, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return True
        return False

    async def set_receive_code(self, share_code: str | list[str, ...], receive_code: str) -> bool:
        if isinstance(share_code, list):
            share_code = ','.join(share_code)
        url = 'https://webapi.115.com/share/updateshare'
        data = {
            'share_code': share_code,
            'receive_code': receive_code,
            'is_custom_code': 1
        }
        result = await srequests.async_post(url, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return True
        return False

    async def switch_receive_code(self, share_code: str, receive_code: str) -> bool:
        url = 'https://webapi.115.com/share/updateshare'
        data = {
            'share_code': share_code,
            'receive_code': receive_code,
        }
        result = await srequests.async_post(url, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return True
        return False

    # 取消分享
    async def cancel_share(self, share_code: str | list[str, ...]) -> bool:
        if isinstance(share_code, list):
            share_code = ','.join(share_code)
        url = 'https://webapi.115.com/share/updateshare'
        data = {
            'share_code': share_code,
            'action': 'cancel'
        }
        result = await srequests.async_post(url, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return True
        return False
