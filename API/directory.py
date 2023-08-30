from Modules import srequests
from Modules.type import Credential


class Directory:
    def __init__(self, credential: Credential) -> None:
        # 設置115標頭
        self.headers = credential['headers']

    # 獲取115容量
    async def get_size(self) -> tuple[int, int, int] | bool:
        result = await srequests.async_get('https://webapi.115.com/files/index_info', headers=self.headers)
        if result:
            result = result.json()
            space_info = result['data']['space_info']
            return space_info['all_remain']['size'], space_info['all_total']['size'], space_info['all_use']['size']
        return False

    # 新增資料夾
    async def add_folder(self, pid: str, name: str) -> dict[str, any] | bool:
        data = {'pid': pid, 'cname': name}
        url = 'https://webapi.115.com/files/add'
        result = await srequests.async_post(url, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 檢查上傳列表 是否有上傳成功
    async def get_fid(self, filename: str) -> bool:
        url = 'https://webapi.115.com/files?aid=1&cid=%d&o=user_ptime&asc=0&offset=0&show_dir=0&limit=20&natsort=1&format=json'
        result = await srequests.async_get(url, headers=self.headers)
        if result:
            result = result.json()
            for i in result['data']:
                if i['n'] == filename:
                    return True
        return False

    # 重新命名
    async def rename(self, name: str, cid: str) -> bool:
        data = {f'files_new_name[{cid}]': name}
        url = 'https://webapi.115.com/files/batch_rename'
        result = await srequests.async_post(url, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return True
        return False

    # 刪除
    async def delete(self, cid: str | list[str, ...]) -> bool:
        data = {'ignore_warn': 1, 'pid': 0}
        if isinstance(cid, str):
            data['fid[0]'] = cid
        else:
            for i in range(len(cid)):
                data.setdefault(f'fid[{i}]', cid[i])
        url = 'https://webapi.115.com/rb/delete'
        result = await srequests.async_post(url, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return True
        return False

    # 移動
    async def move(self, cid: str | list[str, ...], pid: str) -> bool:
        data = {'move_proid': '1638092739580_-2_0', 'pid': pid}
        if isinstance(cid, str):
            data['fid[0]'] = cid
        else:
            for i in range(len(cid)):
                data.setdefault(f'fid[{i}]', cid[i])
        url = 'https://webapi.115.com/files/move'
        result = await srequests.async_post(url, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return True
        return False

    # 複製貼上
    async def paste(self, cid: str | list[str, ...], pid: str) -> bool:
        data = {'pid': pid}
        if isinstance(cid, str):
            data['fid[0]'] = cid
        else:
            for i in range(len(cid)):
                data.setdefault(f'fid[{i}]', cid[i])
        url = 'https://webapi.115.com/files/copy'
        result = await srequests.async_post(url, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return True
        return False

    # 獲取移動資料夾資料
    async def folder(self, cid: str, offset: int, limit: int) -> dict[str, any] | bool:
        url_a = 'https://webapi.115.com/files?aid=1&cid={}&max_size=&offset={}&limit={}&show_dir=1&o=&asc=&nf=1&qid=0&natsort=1&source=&format=json'
        url_b = 'https://aps.115.com/natsort/files.php?aid=1&cid={}&max_size=&offset={}&limit={}&show_dir=1&o=file_name&asc=1&nf=1&qid=0&natsort=1&source=&format=json&type=&fc_mix=0'
        result = await srequests.async_get(url_a.format(cid, offset, limit), headers=self.headers, timeout=5, retry=5)
        if result:
            if 'cid' not in result.json():
                result = await srequests.async_get(url_b.format(cid, offset, limit), headers=self.headers,
                                                   timeout=5, retry=5)
                if result:
                    return result.json()
                return False
            return result.json()
        return False

    # 搜索資料夾資料
    async def searchfolder(self, search_value: str, cid: str, offset: int, limit: int) -> dict[str, any] | bool:
        url = 'https://webapi.115.com/files/search?aid=1&cid={}&max_size=&offset={}&limit={}&show_dir=1&o=file_name&asc=1&nf=1&qid=0&natsort=1&source=&format=json&type=&fc_mix=0&search_value={}&fc=1'
        result = await srequests.async_get(url.format(cid, offset, limit, search_value), headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 搜尋
    async def search(self, search_value: str, cid: str, offset: int, limit: int) -> dict[str, any] | bool:
        url = 'https://webapi.115.com/files/search?offset={}&limit={}&search_value={}&date=&aid=1&cid={}&pick_code=&type=&source=&format=json'
        result = await srequests.async_get(url.format(offset, limit, search_value, cid), headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 文件目錄
    async def path(self, cid: str, offset: int, limit: int) -> dict[str, any] | bool:
        url = 'https://aps.115.com/natsort/files.php?aid=1&cid={}&o=file_name&asc=1&offset={}&show_dir=1&limit={}&code=&scid=&snap=0&natsort=1&record_open_time=1&source=&format=json&fc_mix=0&type=&star=&is_share=&suffix=&custom_order='
        result = await srequests.async_get(url.format(cid, offset, limit),
                                           headers=self.headers, timeout=5, retry=5)

        if result:
            if result.json()['state'] is False:
                url = 'https://webapi.115.com/files?aid=1&cid={}&o=file_name&asc=1&offset={}&show_dir=1&limit={}&code=&scid=&snap=0&natsort=1&record_open_time=1&source=&format=json&fc_mix=&type=&star=&is_share=&suffix=&custom_order='
                result = await srequests.async_get(url.format(cid, offset, limit),
                                                   headers=self.headers, timeout=5, retry=5)

            return result.json()
        return False
