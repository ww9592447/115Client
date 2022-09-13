import httpx
from threading import Thread
from module import set_state, srequests, gather, exists, makedirs, create_task, split, sleep, hashlib


# 檢查檔案
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
            # 檢查檔案是否存在
            detect_file(path)
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state.update({'stop': True})
            # 開始下載
            with open(path, 'rb+') as file:
                key = list(self.state[uuid]['range'].keys())
                if len(key) > 1:
                    task = [self.run(uuid, url, key, file), self.run(uuid, url, key, file)]
                else:
                    task = [self.run(uuid, url, key, file)]
                result = await gather(*task)
            # 下載或者暫停 完畢檢查
            # 下載完畢
            if set(result) == {'end'}:
                # if self.config['Download'].getboolean('Download_sha1'):
                #     return await self.wait_sha1(path, uuid)
                with self.lock:
                    with set_state(self.state, uuid) as state:
                        state.update({'state': 'end', 'stop': False})
            else:
                with self.lock:
                    with set_state(self.state, uuid) as state:
                        state.update({'stop': False})
        else:
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state.update({'state': 'error', 'stop': False})

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
                state.update({'error_sha1': '檢測中', 'stop': False})
        fd = open(path, "rb")
        fd.seek(0)
        line = fd.readline()
        _sha1 = hashlib.sha1()
        _sha1.update(line)
        while line:
            line = fd.readline()
            _sha1.update(line)
        fd.close()
        with self.lock:
            with set_state(self.state, uuid) as state:
                if self.state[uuid]['sha1'] != _sha1.hexdigest().upper():
                    state.update({'error_sha1': True})
                else:
                    state.update({'error_sha1': False})

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

    # 檢查狀態
    def detect_state(self, uuid, status_code):
        state = self.state[uuid]['state']
        # 檢查是否關閉
        if state == 'del':
            return 'del'
        # 檢查是否暫停
        if state == 'pause' or self.closes.value:
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state.update({'pause': True})
                    return 'pause'
        if state == 'error':
            return 'error'
        # 檢查是否錯誤
        if status_code != 206:
            raise

    async def run(self, uuid, url, key, file):
        async with httpx.AsyncClient() as client:
            while 1:
                if key:
                    _key = key.pop(0)
                else:
                    return 'end'
                for stop in range(5):
                    try:
                        size = self.state[uuid]['range'][_key]
                        headers = {**{'Range': 'bytes=%d-%d' % (size[0], size[1])}, **self.download115.headers}
                        async with client.stream('GET', url, headers=headers, timeout=10) as response:
                            async for data in response.aiter_bytes():
                                # 檢查目前狀態
                                if (result := self.detect_state(uuid, response.status_code)) is not None:
                                    return result
                                file.seek(size[0])
                                file.write(data)
                                size[0] += len(data)
                                with self.lock:
                                    with set_state(self.state, uuid) as state:
                                        state['size'] += len(data)
                                        state['range'][_key] = size
                        if size[0] == self.state[uuid]['length'] or size[0] - 1 == size[1]:
                            with self.lock:
                                with set_state(self.state, uuid) as state:
                                    del state['range'][_key]
                            break
                    except:
                        if stop == 4:
                            with self.lock:
                                with set_state(self.state, uuid) as state:
                                    state.update({'state': 'error'})
                            return 'error'

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
        if state['sha1']:
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
        if (url := await self.get_url(self.state[uuid]['pc'])) is False:
            with self.lock:
                with set_state(self.state, uuid) as state:
                    state['blockhash'] = False
            return
        create_task(self.download_sha1(url, uuid))

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
