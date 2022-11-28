import httpx
from threading import Thread
from module import set_state, srequests, gather, exists, makedirs, create_task, split, sleep, hashlib, CancelledError


# 檢查檔案 如果不存在則創建空白檔案
def detect_file(path):
    _path, _ = split(path)
    if not exists(_path):
        makedirs(_path)

    if not exists(path):
        open(path, 'wb').close()


class Download:
    def __init__(self, download115, state, lock, closes, config):
        # 下載API
        self.download115 = download115
        # 共享數據
        self.state = state
        # 共享數據鎖
        self.lock = lock
        # 關閉信號
        self.closes = closes
        # 用戶資料
        self.config = config
        # 所有任務
        self.task = {}

    async def download_task(self, uuid):
        state = self.state[uuid]
        path, name = state['path'], state['name']
        url = await self.detect_url(state['url'], state['pc'])
        if url:
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state['url'] = url
            # 如果沒有分割塊 獲取分割塊
            if not state['range']:
                await self.range(uuid)
            # 檢查檔案 是否存在 如果不存在則創建空白檔案
            detect_file(path)
            # 開始下載
            key = list(self.state[uuid]['range'].keys())
            create_task(self.setsize(uuid))
            if len(key) > 1:
                task = [self.run(uuid, url, key, path), self.run(uuid, url, key, path)]
            else:
                task = [self.run(uuid, url, key, path)]

            result = gather(*task)
            self.task[uuid] = [result, self.state[uuid]['size']]
            try:
                await result
            except CancelledError:
                pass

            if self.state[uuid]['state'] is None:
                if self.config['Download'].getboolean('Download_sha1'):
                    await self.wait_sha1(path, uuid)
            with self.lock:
                with set_state(self.state, uuid) as state:
                    if state['state'] != '檔案下載 不完全':
                        state.update(
                            {
                                'state': state['state'] if state['state'] else 'end',
                                'stop': False
                            }
                        )
        else:
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state.update({'state': '網路異常 下載失敗', 'stop': False})

    # 檢測檔案完整性
    async def wait_sha1(self, path, uuid):
        shs1 = Thread(target=self.check_sha1, args=(path, uuid,))
        shs1.start()
        while 1:
            if shs1.is_alive():
                await sleep(0.1)
                continue
            return

    # 檢測檔案完整性
    def check_sha1(self, path, uuid):
        with self.lock:
            with set_state(self.state, uuid) as state:
                state.update({'state': '檢測中'})
        with open(path, 'rb') as f:
            sha = hashlib.sha1()
            while True:
                data = f.read(1024 * 128)
                if not data:
                    break
                sha.update(data)
            with self.lock:
                with set_state(self.state, uuid) as state:
                    if state['sha1'] != sha.hexdigest().upper():
                        state.update({'state': '檔案下載 不完全'})
                    else:
                        state.update({'state': None})

    # 獲取分割塊
    async def range(self, uuid):
        with self.lock:
            with set_state(self.state, uuid) as state:
                if 409600 < state['length']:
                    _split = int(state['length'] / 7)
                    initial = 0
                    for index in range(7):
                        state['range'][index] = [initial, (initial := _split + initial)]
                    if state['length'] > initial:
                        index += 1
                        state['range'][index] = [initial, state['length']]
                else:
                    state['range'][0] = [0, state['length']]

    # 檢查url是否可用
    async def detect_url(self, url, pc):
        if url:
            response = await srequests.async_head(url, headers=self.download115.headers, retry=2, timeout=5)
            if response.status_code == 200:
                url = url
            else:
                url = await self.get_url(pc)
        else:
            url = await self.get_url(pc)
        return url

    # 獲取url
    async def get_url(self, pc):
        result = await self.download115.CreateDownloadTask(pc)
        if result:
            return result[list(result)[0]]['url']['url']
        else:
            return False

    async def setsize(self, uuid):
        while not self.task[uuid][0].done():
            with self.lock:
                with set_state(self.state, uuid) as state:
                    if state['state']:
                        self.task[uuid][0].cancel()
                    else:
                        state['size'] = self.task[uuid][1]
            await sleep(0.1)
        del self.task[uuid]

    async def run(self, uuid, url, key, path):
        while 1:
            if not key:
                return
            index = key.pop(0)
            sizemin, sizemax = self.state[uuid]['range'][index]
            for stop in range(5):
                try:
                    async with httpx.AsyncClient() as client:
                        headers = {**{'Range': 'bytes=%d-%d' % (sizemin, sizemax)}, **self.download115.headers}
                        with open(path, "rb+") as f:
                            f.seek(sizemin)
                            async with client.stream('GET', url, headers=headers, timeout=10) as response:
                                async for data in response.aiter_bytes():
                                    # 檢查是否錯誤
                                    if response.status_code != 206:
                                        raise
                                    f.write(data)
                                    _data = len(data)
                                    sizemin += _data
                                    self.task[uuid][1] += _data
                            if sizemin == self.state[uuid]['length'] or sizemin - 1 == sizemax:
                                with self.lock:
                                    with set_state(self.state, uuid) as state:
                                        del state['range'][index]
                                break
                except CancelledError:
                    with self.lock:
                        with set_state(self.state, uuid) as state:
                            state['range'][index] = (sizemin, sizemax)
                            state['size'] = self.task[uuid][1]
                    return
                except (Exception, ):
                    if stop == 4:
                        with self.lock:
                            with set_state(self.state, uuid) as state:
                                state.update({'state': 'error'})
                        return

    async def aria2_task(self, uuid):
        if (url := await self.get_url(self.state[uuid]['pc'])) is False:
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state['state'] = '獲取url失敗'
            return
        await create_task(self.aria2_rpc(url, uuid))

    async def aria2_rpc(self, url, uuid):
        state = self.state[uuid]
        data = {
            'jsonrpc': '2.0',
            'id': 'qwer',
            'method': 'aria2.addUri',
            'params': [[url], {'allow-overwrite': 'true', 'dir': f"{state['path']}\\",
                               'header': [f'{i[0]}: {i[1]}' for i in self.download115.headers.items()]}]
        }
        # 是否檢查sha1
        if self.config['aria2-rpc'].getboolean('aria2_sha1'):
            data['params'][1]['checksum'] = f'sha-1={state["sha1"]}'
        response = await srequests.async_post(url=self.config['aria2-rpc']['rpc_url'], json=data)
        with self.lock:
            with set_state(self.state, uuid) as state:
                if response.status_code == 200:
                    result = response.json().get("result", [])
                    state.update({'gid': result})
                else:
                    state.update({'state': '無法調用aria2_rpc'})

    async def sha1_task(self, uuid):
        async def _task():
            if (url := await self.get_url(self.state[uuid]['pc'])) is False:
                with self.lock:
                    with set_state(self.state, uuid) as state:
                        state['state'] = '獲取下載鏈結失敗'
                return
            await self.download_sha1(url, uuid)
        task = create_task(_task())
        while not task.done():
            if self.state[uuid]['state']:
                task.cancel()
                try:
                    await task
                except (BaseException,):
                    pass
                break
            await sleep(0.1)
        with self.lock:
            with set_state(self.state, uuid) as state:
                state['stop'] = False

    async def download_sha1(self, url, uuid):
        for stop in range(5):
            _bytes = b''
            headers = {**{'Range': 'bytes=0-131072'}, **self.download115.headers}
            try:
                async with httpx.AsyncClient() as client:
                    async with client.stream('GET', url, headers=headers, timeout=10) as response:
                        async for data in response.aiter_bytes():
                            _bytes += data
                sha1 = hashlib.sha1()
                sha1.update(_bytes[0: 128 * 1024])
                with self.lock:
                    with set_state(self.state, uuid) as state:
                        state['blockhash'] = sha1.hexdigest().upper()
                return
            except:
                if stop == 4:
                    with self.lock:
                        with set_state(self.state, uuid) as state:
                            state['blockhash'] = False
                    return
