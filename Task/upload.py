from Callback import Callback
from threading import Thread
import time
import base64
from module import set_state, gather, create_task, uuid1, hashlib, sleep, httpx


def get_slice_md5(bio):
    md5 = hashlib.md5()
    md5.update(bio)
    return base64.b64encode(md5.digest())


class GetSha1(Thread):
    def __init__(self, path):
        Thread.__init__(self)
        self.path = path
        self.result = None

    def run(self):
        with open(self.path, 'rb') as f:
            sha = hashlib.sha1()
            sha.update(f.read(1024 * 128))
            blockhash = sha.hexdigest().upper()
            f.seek(0, 0)
            sha = hashlib.sha1()
            sha.update(f.read())
            sha1 = sha.hexdigest().upper()
        self.result = (blockhash, sha1)

    def get_result(self):
        return self.result


class Upload:
    def __init__(self, upload115, state, lock, closes, directory, config):
        # 共享數據資料
        self.state = state
        # 數據鎖
        self.lock = lock
        # 關閉信號
        self.closes = closes
        # 用戶數據
        self.config = config
        # 初始化上傳任務
        self.task = None
        # 上傳API
        self.upload115 = upload115
        # 115API
        self.directory = directory

    def cls_task(self, task):
        self.task = None

    def range(self, size):
        upload = {}
        i = 0
        if size > 4194304:
            for i in range(size // 4194304):
                upload[str(i + 1)] = (i * 4194304, 4194304)
            if size % 4194304 != 0:
                i += 1
                upload[str(i + 1)] = (i * 4194304, size - (i * 4194304))
        else:
            return {'1': (0, size)}
        return upload

    async def sha1_task(self, uuid):
        if self.upload115.user_id is None:
            if self.task is None:
                self.task = create_task(self.upload115.getuserkey())
                self.task.add_done_callback(self.cls_task)
            if await self.task is False:
                return 'error獲取key失敗'

        if self.state[uuid]['sha1'] is None:
            getsha1 = GetSha1(self.state[uuid]['path'])
            getsha1.start()
            while getsha1.is_alive():
                await sleep(0.1)
            blockhash, sha1 = getsha1.get_result()
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state.update({'sha1': sha1, 'blockhash': blockhash})
        state = self.state[uuid]
        result = await self.upload115.upload_file_by_sha1(
            state['blockhash'], state['sha1'], state['length'],
            state['name'], state['cid']
        )
        _result = await self.detect_upload(result, state)
        if _result is None:
            _result = '秒傳失敗'
        with self.lock:
            with set_state(self.state, uuid) as state:
                state.update({'stop': False, 'state': _result})

    async def upload_task(self, uuid):
        result = await self.upload(uuid)
        with self.lock:
            with set_state(self.state, uuid) as state:
                if self.state[uuid]['state'] is None:
                    state.update({'stop': False, 'state': result})
                else:
                    state.update({'stop': False})

    async def upload(self, uuid):
        if self.upload115.user_id is None:
            if self.task is None:
                self.task = create_task(self.upload115.getuserkey())
                self.task.add_done_callback(self.cls_task)
            if await self.task is False:
                return 'error獲取key失敗'

        if self.state[uuid]['sha1'] is None:
            getsha1 = GetSha1(self.state[uuid]['path'])
            getsha1.start()
            while getsha1.is_alive():
                await sleep(0.1)
            blockhash, sha1 = getsha1.get_result()
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state.update({'sha1': sha1, 'blockhash': blockhash})
        state = self.state[uuid]
        result = {}
        if self.state[uuid]['second'] is None:
            result = await self.upload115.upload_file_by_sha1(
                state['blockhash'], state['sha1'], state['length'],
                state['name'], state['cid']
            )
            # 檢查秒傳結果
            if (_result := await self.detect_upload(result, state)) is not None:
                return _result

            with self.lock:
                with set_state(self.state, uuid) as state:
                    state.update({'second': False})

        if 'gettokenurl' not in self.upload115.token:
            if self.task is None:
                self.task = create_task(self.upload115.getinfo())
                self.task.add_done_callback(self.cls_task)
            if await self.task is False:
                return '獲取info失敗'

        if 'SecurityToken' not in self.upload115.token:
            if self.task is None:
                self.task = create_task(self.upload115.gettoken())
                self.task.add_done_callback(self.cls_task)
            if await self.task is False:
                return '獲取token失敗'

        if time.time() - self.upload115.token['time'] >= 3000:
            if self.task is None:
                self.task = create_task(self.upload115.gettoken())
                self.task.add_done_callback(self.cls_task)
            if await self.task is False:
                return '獲取token失敗'
        if not state['cb']:
            # 獲取上傳url
            try:
                url = self.upload115.get_url(self.upload115.token['endpoint'], result['bucket'], result['object'])
            except Exception as f:
                print('------------')
                print(f)
                print(result)
                raise f
            # 獲取上傳key名稱
            upload_key = result['object']
            # 獲取uploadid
            if (upload_id := await self.upload115.get_upload_id(url, upload_key)) is False:
                with self.lock:
                    with set_state(self.state, uuid) as state:
                        state.update({'state': '獲取uploadid失敗'})
                return
            cb = {"x-oss-callback": base64.b64encode(result['callback']['callback'].encode()).decode(),
                  "x-oss-callback-var": base64.b64encode(result['callback']['callback_var'].encode()).decode()}
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state.update({'url': url, 'upload_key': upload_key, 'upload_id': upload_id,
                                  'range': self.range(state['length']), 'cb': cb})
        with self.lock:
            with set_state(self.state, uuid) as state:
                state.update({'stop': True})

        if not state['range']:
            result = await self.upload115.combine(
                state[uuid]['etag'], state['url'],
                state['upload_key'], state['upload_id'], state['cb']
            )
            return await self.detect_upload(result, state)

        callback = Callback()
        callback.all_size = state['size']

        with open(state['path'], 'rb') as obj:
            get_upload = []
            key = list(state['range'].keys())
            for _ in range(4 if len(state['range']) >= 4 else len(state['range'])):
                _upload = self.run(
                    uuid, key, obj, callback
                )
                get_upload.append(_upload)
            result = await gather(*get_upload)
        result = list(set(result))
        if result == ['end']:
            result = await self.upload115.combine(
                self.state[uuid]['etag'], state['url'],
                state['upload_key'], state['upload_id'], state['cb']
            )
            return await self.detect_upload(result, state)
        else:
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state.update({'size': callback.all_size})
            return self.state[uuid]['state']

    async def detect_upload(self, result, state):
        if result is False:
            return '網路異常 上傳失敗'
        if 'status' in result:
            # 違規內容重新命名秒傳
            if result['status'] is False and result['statusmsg'] == '上传失败，含违规内容':
                filename = uuid1().hex
                result = await self.upload115.upload_file_by_sha1(state['blockhash'], state['sha1'],
                                                                  state['length'], filename, state['cid'])
                if result is False:
                    return '網路異常 上傳失敗'
                if result['status'] == 2:
                    cid = await self.directory.get_fid(filename)
                    if cid is False:
                        return '網路異常 上傳失敗'
                    result = await self.directory.rename(state['name'], cid)
                    if result is False:
                        return '更名錯誤'
                    else:
                        return '上傳完成'
                else:
                    return '秒傳出現錯誤3'
            elif result['statusmsg'] == '文件大小超出单文件上传最大限制，无法上传本文件。':
                return '文件大小超出上傳限制'
            elif result['status'] == 2:
                return '秒傳完成'
        elif 'state' in result and result['state'] is True:
            return '上傳完成'

    def set_size(self, uuid, size):
        if self.state[uuid]['state']:
            raise UserWarning(self.state[uuid]['state'])
        with self.lock:
            with set_state(self.state, uuid) as state:
                state['size'] = size

    async def run(self, uuid, key, obj, callback):
        while 1:
            state = self.state[uuid]
            if state['state']:
                return state['state']
            elif key:
                _key = key.pop(0)
            else:
                return 'end'
            if time.time() - self.upload115.token['time'] >= 3000:
                if self.task is None:
                    self.task = create_task(self.upload115.gettoken())
                    self.task.add_done_callback(self.cls_task)
                if await self.task is False:
                    with self.lock:
                        with set_state(self.state, uuid) as state:
                            state['state'] = '獲取token失敗'
                    return '獲取token失敗'

            size = state['range'][_key]
            for i in range(5):
                params = {'uploadId': state['upload_id'], 'partNumber': str(_key)}
                obj.seek(size[0])
                bio = obj.read(size[1])
                md5 = get_slice_md5(bio)
                _callback = callback(bio, callback=lambda all_size: self.set_size(uuid, all_size))
                try:
                    async with httpx.AsyncClient() as client:
                        headers = self.upload115.get_headers(
                            'PUT', state['upload_key'], {'x-oss-security-token': self.upload115.token['SecurityToken']},
                            params=params
                        )
                        result = await client.put(state['url'], params=params, data=_callback.async_read(),
                                                  headers=headers, timeout=30)
                        result = result.headers
                        if result['content-md5'] != md5.decode():
                            raise
                        if self.state[uuid]['state']:
                            return self.state[uuid]['state']
                        with self.lock:
                            with set_state(self.state, uuid) as state:
                                del state['range'][str(_key)]
                                state['etag'][str(_key)] = result['etag']
                        break
                except UserWarning as f:
                    _callback.delete()
                    return str(f)
                except Exception as f:
                    if i == 4:
                        with self.lock:

                            with set_state(self.state, uuid) as state:
                                state['state'] = '網路異常 上傳失敗'
                        return '網路異常 上傳失敗'
                    _callback.delete()
