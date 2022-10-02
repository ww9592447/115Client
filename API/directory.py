import time
from module import  srequests
from asyncio import sleep


class Directory:
    def __init__(self, config):
        self.headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': config['設定'].get('cookie', raw=True),
                "User-Agent": 'Mozilla/5.0  115disk/11.2.0'
            }
        # 文件目錄url
        self.filesurl = 'https://aps.115.com/natsort/files.php?aid=1&cid={}&o=file_name&asc=1&offset={}&show_dir=1&limit={}&code=&scid=&snap=0&natsort=1&record_open_time=1&source=&format=json&type=&star=&is_share=&suffix=&custom_order=&fc_mix=0'
        # 新增文件夾url
        self.folderurl = 'https://webapi.115.com/files/add'
        # 重新命名url
        self.renameurl = 'https://webapi.115.com/files/batch_rename'
        # 刪除url
        self.delurl = 'https://webapi.115.com/rb/delete'
        # 移動url
        self.moveurl = 'https://webapi.115.com/files/move'
        # 獲取移動資料夾url
        self.open_folder = 'https://webapi.115.com/files?aid=1&cid={}&max_size=&offset={}&limit={}&show_dir=1&o=&asc=&nf=1&qid=0&natsort=1&source=&format=json'
        # 搜索資料夾
        self.searchfolderurl = 'https://webapi.115.com/files/search?aid=1&cid={}&max_size=&offset={}&limit={}&show_dir=1&o=file_name&asc=1&nf=1&qid=0&natsort=1&source=&format=json&type=&fc_mix=0&search_value={}&fc=1'
        # 複製貼上url
        self.pasteurl = 'https://webapi.115.com/files/copy'
        # 搜尋url
        self.searchurl = 'https://webapi.115.com/files/search?offset={}&limit={}&search_value={}&date=&aid=1&cid={}&pick_code=&type=&source=&format=json'
        # 獲取已上傳列表 url
        self.listFileURL = 'https://webapi.115.com/files?aid=1&cid=%d&o=user_ptime&asc=0&offset=0&show_dir=0&limit=%d&natsort=1&format=json'
        # 獲取離線下載所需資料
        self.sign_and_timeurl = 'https://115.com/?ct=offline&ac=space'
        # 獲取離線uid
        self.uidurl = 'https://my.115.com/?ct=ajax&ac=get_user_aq'
        # 添加離線任務
        self.offlineurl = 'https://115.com/web/lixian/?ct=lixian&ac=add_task_url'
        # 離線進度
        self.offline_scheduleurl = 'https://115.com/web/lixian/?ct=lixian&ac=task_lists'
        # 刪除離線
        self.offline_delurl = 'https://115.com/web/lixian/?ct=lixian&ac=task_del'
        # 清空離線
        self.offline_clearurl = 'https://115.com/web/lixian/?ct=lixian&ac=task_clear'
        # 驗證碼
        self.securityurl = 'https://captchaapi.115.com/?ac=security_code&type=web&cb={}'
        self.verification_codeurl = 'https://captchaapi.115.com/?ct=index&ac=code&ctype=0&_t=1656170363734'
        self.verification_mapurl = 'https://captchaapi.115.com/?ct=index&ac=code&t=all&_t=1656170364075'
        self.captchaurl = 'https://webapi.115.com/user/captcha'

        self.uid = None
        self.sign = None
        self.time = None

    async def get_sign_and_time(self):
        result = await srequests.async_get(self.sign_and_timeurl, headers=self.headers)
        try:
            result = result.json()
        except:
            raise
        if not result['state'] or not result['sign'] or not result['time']:
            raise
        self.sign = result['sign']
        self.time = result['time']
        return result['sign'], result['time']

    async def get_uid(self):
        result = await srequests.async_get('https://my.115.com/?ct=ajax&ac=get_user_aq', headers=self.headers)
        try:
            result = result.json()
        except:
            raise
        if not result['state'] or not result['data'] or not result['data']['uid']:
            raise
        self.uid = result['data']['uid']
        return self.uid

    async def security(self):
        cb = f'Close911_{int(time.time() * 1000)}'
        await srequests.async_get(self.securityurl.format(cb), headers=self.headers)
        return cb

    # 獲取要輸入的圖片文字
    async def verification_code(self):
        result = await srequests.async_get(self.verification_codeurl, headers=self.headers)


    async def verification_map(self):
        result = await srequests.async_get(self.verification_mapurl, headers=self.headers)

    # 提交驗證
    async def captcha(self):
        data = {
            'code': '9612',
            'sign': 'cod9k43t484d3833lutp5nvado',
            'ac': 'security_code',
            'type': 'web',
            'cb': 'Close911_1656170362944',
        }
        result = await srequests.async_post(self.captchaurl, headers=self.headers, data=data)

    # 添加離線任務
    async def add_offline(self, url, cid=''):
        try:
            if self.sign is None:
                await self.get_sign_and_time()
                await self.get_uid()
        except:
            return False
        form_data = {
            'savepath': '',
            'wp_path_id': cid,
            'uid': self.uid,
            'sign': self.sign,
            'time': self.time,
        }

        if isinstance(url, str):
            form_data.update({'url': url})
            result = await srequests.async_post(self.offlineurl, headers=self.headers, data=form_data)
            print(result)
            print(result.text)
            # < Response[200
            # OK] >
            # {"state": false, "errno": 911, "errcode": 911, "error_msg": "请验证账号"}
            #  Set-Cookie: PHPSESSID=cod9k43t484d3833lutp5nvado; path=/
            # 獲取驗證
            # https://captchaapi.115.com/?ct=index&ac=code&ctype=0&_t=1656170363734
            # https://captchaapi.115.com/?ct=index&ac=code&t=all&_t=1656170364075
            # https://webapi.115.com/user/captcha

            # code: 9612
            # sign: cod9k43t484d3833lutp5nvado
            # ac: security_code
            # type: web
            # cb: Close911_1656170362944


        else:
            for index, _url in zip(range(len(url)), url):
                form_data.update({f'url[{index}]': _url})
            result = await srequests.async_post(self.offlineurl + 's', headers=self.headers, data=form_data)
        try:
            return result.json()
        except:
            return False

    # 刪除單個離線
    async def offline_delete(self, _hash):
        try:
            if self.sign is None:
                await self.get_sign_and_time()
                await self.get_uid()
        except:
            return False
        data = {'hash[0]': _hash, 'uid': self.uid, 'sign': self.sign, 'time': self.time}
        result = await srequests.async_post(self.offline_delurl, headers=self.headers, data=data)
        try:
            return result.json()
        except:
            return False

    # 刪除全部離線
    async def offline_clear(self):
        data = {'flag': 1}
        result = await srequests.async_post(self.offline_clearurl, headers=self.headers, data=data)
        try:
            return result.json()
        except:
            return False

    # 離線進度
    async def offline_schedule(self):
        result = await srequests.async_get(self.offline_scheduleurl, headers=self.headers)
        try:
            return result.json()
            # return result.text
        except:
            return False


    # 新增資料夾
    async def add_folder(self, pid, name):
        data = {'pid': pid, 'cname': name}
        result = await srequests.async_post(self.folderurl, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    async def get_fid(self, filename):
        for _ in range(2):
            result = await srequests.async_get(self.listFileURL, headers=self.headers)
            if result:
                result = result.json()
                for i in result['data']:
                    if i['n'] == filename:
                        return i['fid']
                print(filename)
                print(result)
                print('----------------------------------')
            await sleep(1)
        return False

    # 重新命名
    async def rename(self, name, cid):
        data = {f'files_new_name[{cid}]': name}
        result = await srequests.async_post(self.renameurl, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 刪除
    async def delete(self, cid):
        data = {'ignore_warn': 1, 'pid': 0}
        if type(cid) == list:
            for i in range(len(cid)):
                data.setdefault(f'fid[{i}]', cid[i])
        else:
            data['fid[0]'] = cid
        result = await srequests.async_post(self.delurl, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 移動
    async def move(self, cid, pid):
        data = {'move_proid': '1638092739580_-2_0', 'pid': pid}
        if type(cid) == list:
            for i in range(len(cid)):
                data.setdefault(f'fid[{i}]', cid[i])
        else:
            data['fid[0]'] = cid
        result = await srequests.async_post(self.moveurl, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 複製貼上
    async def paste(self, cid, pid):
        data = {'pid': pid}
        if type(cid) == list:
            for i in range(len(cid)):
                data.setdefault(f'fid[{i}]', cid[i])
        else:
            data['fid[0]'] = cid
        result = await srequests.async_post(self.pasteurl, data=data, headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 獲取移動資料夾資料
    async def folder(self, cid, offset, limit):
        result = await srequests.async_get(self.open_folder.format(cid, offset, limit), headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 獲取移動資料夾資料
    async def searchfolder(self, search_value, cid, offset, limit):
        result = await srequests.async_get(self.searchfolderurl.format(cid, offset, limit, search_value), headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False

    # 搜尋
    async def search(self, search_value, cid, offset, limit):
        result = await srequests.async_get(self.searchurl.format(offset, limit, search_value, cid), headers=self.headers, timeout=5, retry=5)
        try:
            if result:
                return result.json()
            return False
        except:
            print(result.text)

    # 文件目錄
    async def path(self, cid, offset, limit):
        result = await srequests.async_get(self.filesurl.format(cid, offset, limit), headers=self.headers, timeout=5, retry=5)
        if result:
            return result.json()
        return False
