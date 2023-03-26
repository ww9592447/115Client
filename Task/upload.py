from .Callback import Callback
from threading import Thread
import time
import base64
from module import setstate, gather, create_task, uuid1, hashlib, sleep, httpx, CancelledError, Lock, ConfigParser
from API.upload115 import Upload115
from API.directory import Directory


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
            while True:
                data = f.read(1024 * 128)
                if not data:
                    break
                sha.update(data)
            sha1 = sha.hexdigest().upper()
        self.result = sha1

    def get_result(self):
        return self.result


class Upload:
    def __init__(self, upload115: Upload115, state: dict[str, any],
                 lock: Lock, directory: Directory, config: ConfigParser) -> None:
        # 共享數據
        self.state: dict[str, any] = state
        # 共享數據鎖
        self.lock: Lock = lock
        # 用戶資料
        self.config: ConfigParser = config
        # 上傳API
        self.upload115: Upload115 = upload115
        # 115API
        self.directory: Directory = directory
        # 初始化上傳任務
        self.task = {}

    def range(self, size: int) -> dict[str, tuple[int, int]]:
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
        # 檢查是否有key
        if await self.checktoken() is not None:
            with self.lock:
                with setstate(self.state, uuid) as state:
                    state.update({'state': '獲取key失敗'})
            return

        if self.state[uuid]['sha1'] is None:
            getsha1 = GetSha1(self.state[uuid]['path'])
            getsha1.start()
            while getsha1.is_alive():
                await sleep(0.1)
            blockhash, sha1 = getsha1.get_result()
            with self.lock:
                with setstate(self.state, uuid) as state:
                    state.update({'sha1': sha1, 'blockhash': blockhash})
        state = self.state[uuid]
        result = await self.upload115.upload_file_by_sha1(
            state['blockhash'], state['sha1'], state['length'],
            state['name'], state['cid']
        )
        result = await self.detect_upload(result, state)

        with self.lock:
            with setstate(self.state, uuid) as state:
                if result == '秒傳完成':
                    state.update({'state': 'end', 'result': '秒傳完成'})
                else:
                    state.update({'state': result})

    async def upload_task(self, uuid):
        result = await self.upload(uuid)
        with self.lock:
            with setstate(self.state, uuid) as state:
                if self.state[uuid]['state'] is None:
                    if result in ['上傳完成', '秒傳完成']:
                        state.update({'stop': False, 'state': 'end', 'result': result})
                    else:
                        state.update({'stop': False, 'state': result})
                else:
                    state.update({'stop': False})

    # 檢查token是否失效
    async def checktoken(self, key=True):
        if key:
            if self.upload115.user_id == '':
                if 'key' not in self.task:
                    self.task['key'] = create_task(self.upload115.getuserkey())
                    self.task['key'].add_done_callback(lambda task: self.task.update({'token': None}))
                if await self.task['key'] is False:
                    return '獲取key失敗'
        else:
            if 'gettokenurl' not in self.upload115.token:
                if 'info' not in self.task:
                    self.task['info'] = create_task(self.upload115.getinfo())
                    self.task['info'].add_done_callback(lambda task: self.task.update({'info': None}))
                if await self.task['info'] is False:
                    return '獲取info失敗'

            if time.time() - self.upload115.token['time'] >= 3000:
                if 'token' not in self.task or self.task['token'] is None:
                    self.task['token'] = create_task(self.upload115.gettoken())
                    self.task['token'].add_done_callback(lambda task: self.task.update({'token': None}))
                if await self.task['token'] is False:
                    return '獲取token失敗'

    async def upload(self, uuid):
        # 檢查是否有key
        if (result := await self.checktoken()) is not None:
            return result

        if self.state[uuid]['sha1'] is None:
            getsha1 = GetSha1(self.state[uuid]['path'])
            getsha1.start()
            while getsha1.is_alive():
                await sleep(0.1)
            sha1 = getsha1.get_result()
            with self.lock:
                with setstate(self.state, uuid) as state:
                    state.update({'sha1': sha1})
        state = self.state[uuid]
        # 檢查是否已經秒傳過
        if self.state[uuid]['second'] is None:
            result = await self.upload115.upload_file_by_sha1(
                state['path'], state['sha1'], state['length'],
                state['name'], state['cid']
            )
            # 檢查秒傳結果
            if (_result := await self.detect_upload(result, state)) is not None:
                return _result
            cb = {"x-oss-callback": base64.b64encode(result['callback']['callback'].encode()).decode(),
                  "x-oss-callback-var": base64.b64encode(result['callback']['callback_var'].encode()).decode()}

            with self.lock:
                with setstate(self.state, uuid) as state:
                    state.update({'second': False, 'bucket': result['bucket'],
                                  'upload_key': result['object'], 'cb': cb})

        # 檢查token是否失效
        if (result := await self.checktoken(key=False)) is not None:
            return result

        if not state['url']:
            # 獲取上傳url
            url = self.upload115.get_url(self.upload115.token['endpoint'], state['bucket'], state['upload_key'])
            # 獲取uploadid
            if (upload_id := await self.upload115.get_upload_id(url, state['upload_key'])) is False:
                return '獲取uploadid失敗'
            print(upload_id, state['name'])
            with self.lock:
                with setstate(self.state, uuid) as state:
                    state.update({'url': url, 'upload_id': upload_id, 'range': self.range(state['length'])})

        with self.lock:
            with setstate(self.state, uuid) as state:
                state.update({'stop': True})

        callback = Callback()
        callback.all_size = state['size']

        get_upload = []
        key = list(state['range'].keys())
        create_task(self.setsize(uuid))
        for _ in range(4 if len(state['range']) >= 4 else len(state['range'])):
            _upload = self.run(
                uuid, key, state['path'], callback
            )
            get_upload.append(_upload)
        result = gather(*get_upload)
        self.task[uuid] = {'task': result, 'size': state['size']}
        try:
            await result
        except CancelledError:
            pass

        state = self.state[uuid]
        if state['state'] is None:
            result = await self.upload115.combine(
                state['etag'], state['url'],
                state['upload_key'], state['upload_id'], state['cb']
            )
            # return await self.detect_upload(result, state)
            if result:
                return await self.detect_upload(result, state)
            else:
                # print(state['name'], '異常')
                if not await self.directory.get_fid(state['name']):
                    return '上傳失敗 需要重新上傳'
        else:
            with self.lock:
                with setstate(self.state, uuid) as state:
                    state.update({'size': callback.all_size})
            return state['state']

    async def setsize(self, uuid):
        while not self.task[uuid]['task'].done():
            with self.lock:
                with setstate(self.state, uuid) as state:
                    if state['state']:
                        self.task[uuid]['task'].cancel()
                    else:
                        state['size'] = self.task[uuid]['size']
            await sleep(0.1)
        del self.task[uuid]

    async def run(self, uuid, key, path, callback):
        while 1:
            if not key:
                return
            index = key.pop(0)

            # 檢查token是否失效
            if await self.checktoken(key=False) is not None:
                with self.lock:
                    with setstate(self.state, uuid) as state:
                        state['state'] = '獲取token失敗'
                return

            state = self.state[uuid]
            size = state['range'][index]
            with open(path, 'rb') as obj:
                for i in range(5):
                    params = {'uploadId': state['upload_id'], 'partNumber': str(index)}
                    obj.seek(size[0])
                    bio = obj.read(size[1])
                    md5 = get_slice_md5(bio)
                    _callback = callback(bio, callback=lambda all_size: self.task[uuid].update({'size': all_size}))
                    try:
                        async with httpx.AsyncClient() as client:
                            headers = self.upload115.get_headers(
                                'PUT', state['upload_key'],
                                {'x-oss-security-token': self.upload115.token['SecurityToken']},
                                params=params
                            )
                            result = await client.put(state['url'], params=params, data=_callback.async_read(),
                                                      headers=headers, timeout=30)
                            result = result.headers
                            if result['content-md5'] != md5.decode():
                                raise
                            with self.lock:
                                with setstate(self.state, uuid) as state:
                                    del state['range'][str(index)]
                                    state['etag'][str(index)] = result['etag']
                            break
                    except CancelledError:
                        _callback.delete()
                        return
                    except (Exception, ):
                        if i == 4:
                            with self.lock:
                                with setstate(self.state, uuid) as state:
                                    state['state'] = '網路異常 上傳失敗'
                            return
                        _callback.delete()

    async def detect_upload(self, result, state):
        if result is False:
            return '網路異常 上傳失敗'
        if 'status' in result:
            # 違規內容重新命名秒傳
            if result['status'] is False and result['statusmsg'] == '上传失败，含违规内容':
                filename = uuid1().hex
                try:
                    result = await self.upload115.upload_file_by_sha1(state['blockhash'], state['sha1'],
                                                                      state['length'], filename, state['cid'])
                except self.upload115.ErrInvalidEncodedData():
                    return '數據驗證錯誤'
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
