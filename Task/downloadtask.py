import hashlib
from os import makedirs
from os.path import exists, split
from mprocess import Lock
from asyncio import create_task, sleep, CancelledError, gather, Future
from threading import Thread
from typing import TypedDict

import httpx

from Modules.get_data import SetData
from Modules import srequests
from Modules.type import DownloadFileData, StateData, Aria2FileData, Config
from API.download import Download, Result


class TaskData(TypedDict):
    task: Future
    all_size: int
    size: dict[int, int]


# 檢查檔案 如果不存在則創建空白檔案
def detect_file(path) -> None:
    _path, _ = split(path)
    if not exists(_path):
        makedirs(_path)

    if not exists(path):
        open(path, 'wb').close()


class DownloadTask:
    def __init__(
            self,
            download: Download,
            state: dict[str, DownloadFileData | Aria2FileData],
            lock: Lock,
            config: Config
    ) -> None:
        # 下載API
        self.download: Download = download
        # 共享數據
        self.state: dict[str, DownloadFileData | Aria2FileData] = state
        # 共享數據鎖
        self.lock: Lock = lock
        # 用戶資料
        self.config: Config = config
        # 所有任務
        self.task: dict[str, TaskData] = {}

    # 檢測檔案完整性
    def check_sha1(self, path: str, uuid: str) -> None:
        with open(path, 'rb') as f:
            sha = hashlib.sha1()
            while True:
                data = f.read(1024 * 128)
                if not data:
                    break
                sha.update(data)
            with SetData(self.state, uuid, self.lock) as state:
                if state['sha1'] != sha.hexdigest().upper():
                    state.update({'state': StateData.ERROR, 'result': '檔案下載 不完全',  'start': False})
                else:
                    state.update({'state': StateData.COMPLETE, 'result': '', 'start': False})

    # 檢測檔案完整性
    async def wait_sha1(self, path: str, uuid: str) -> None:
        with SetData(self.state, uuid, self.lock) as state:
            state.update({'state': StateData.TEXT, 'result': 'sha1檢測中'})
        shs1 = Thread(target=self.check_sha1, args=(path, uuid,))
        shs1.start()
        while 1:
            if shs1.is_alive():
                await sleep(0.1)
                continue
            return

    async def download_task(self, uuid: str) -> None:
        with self.lock:
            state: DownloadFileData = self.state[uuid].copy()
        result = await self.get_url(state['url'], state['pc'])
        if result['state']:
            url = result['result']
            path, name = state['path'], state['name']
            with SetData(self.state, uuid, self.lock) as state:
                state['url'] = url
            # 如果沒有分割塊 獲取分割塊
            if not state['all_range']:
                await self.set_range(uuid)
            # 檢查檔案 是否存在 如果不存在則創建空白檔案
            detect_file(path)
            # 獲取所有下載index
            with self.lock:
                all_index = list(self.state[uuid]['all_range'].keys())
            task_list = []
            create_task(self.set_size(uuid))
            with SetData(self.state, uuid, self.lock) as state:
                state['start'] = True
            for index in range(2):
                task_list.append(create_task(self.download_all_part(uuid, all_index, index)))
            result = gather(*task_list)
            self.task[uuid] = TaskData(task=result, all_size=state['all_size'], size={0: 0, 1: 0})
            try:
                await result
            except CancelledError:
                for task in task_list:
                    task.cancel()
                for task in task_list:
                    if not task.done():
                        await task
                with SetData(self.state, uuid, self.lock) as state:
                    state['start'] = False
                    state['all_size'] -= (self.task[uuid]['size'][0] + self.task[uuid]['size'][1])
                return
            if self.config['download_sha1']:
                await self.wait_sha1(path, uuid)
            else:
                with SetData(self.state, uuid, self.lock) as state:
                    state.update({'state': StateData.COMPLETE, 'result': '', 'start': False})
            return
        with SetData(self.state, uuid, self.lock) as state:
            state.update({
                'state': StateData.ERROR,
                'result': result['result'],
                'start': False
            })

    async def set_size(self, uuid: str) -> None:
        while not self.task[uuid]['task'].done():
            with SetData(self.state, uuid, self.lock) as state:
                if state['state'] in (StateData.ERROR, StateData.PAUSE, StateData.CANCEL):
                    self.task[uuid]['task'].cancel()
                else:
                    state['all_size'] = self.task[uuid]['all_size']
            await sleep(0.1)
        del self.task[uuid]

    # 獲取分割塊
    async def set_range(self, uuid: str) -> None:
        with SetData(self.state, uuid, self.lock) as state:
            part = 11000000
            index = 0
            if state['file_size'] > part:
                for index in range(state['file_size'] // part):
                    size = index * 11000000
                    state['all_range'][str(index)] = (index * part, size + part - 1)
                if state['file_size'] % part != 0:
                    index += 1
                    state['all_range'][str(index)] = (index * part, state['file_size'])
            else:
                state['all_range']['0'] = (0, state['file_size'])

    # 獲取 url or 檢查url是否可用
    async def get_url(self, url: str, pc: str) -> Result:
        if url:
            response = await srequests.async_head(url, headers=self.download.headers, retry=2, timeout=5)
            if response.status_code == 200:
                return Result(state=True, result=url)

        result = await self.download.get_url(pc)
        if result['state']:
            return Result(state=True, result=result['result'])
        return Result(state=False, result='網路異常 獲取url失敗')

    async def download_all_part(self, uuid: str, all_index: list[str, ...], index: int) -> None:
        def size_callback(size: int) -> None:
            self.task[uuid]['size'][index] += size
            self.task[uuid]['all_size'] += size

        with self.lock:
            state = self.state[uuid].copy()
        with open(state['path'], 'rb+') as file:
            while 1:
                if not all_index:
                    return
                _index = all_index.pop(0)
                self.task[uuid]['size'][index] = 0
                offset, length = state['all_range'][_index]
                try:
                    result = await self.download.download_part(
                        state['file_size'],
                        state['url'],
                        offset,
                        length,
                        size_callback
                    )
                except CancelledError:
                    return

                if result['state'] is True:
                    file.seek(offset)
                    file.write(result['data'])
                    with SetData(self.state, uuid, self.lock) as state:
                        del state['all_range'][_index]
                elif result['state'] is False:
                    with SetData(self.state, uuid, self.lock) as state:
                        state.update({
                            'state': StateData.ERROR,
                            'result': result['result'],
                        })
                        raise CancelledError

    async def run_download_range(self, url: str, offset: int, length: int, file_size: int) -> bytearray | None:
        _data = bytearray()
        for stop in range(5):
            _offset = offset
            try:
                async with httpx.AsyncClient() as client:
                    headers = {**{'Range': 'bytes=%d-%d' % (offset, length)}, **self.download.headers}
                    async with client.stream('GET', url, headers=headers, timeout=10) as response:
                        async for data in response.aiter_raw():
                            # 檢查是否錯誤
                            if response.status_code != 206:
                                raise
                            _data += data
                            _offset += len(data)
                if _offset == file_size or _offset - 1 == length:
                    return _data
                else:
                    print('---------', _offset, file_size, offset + length)
                    raise

            except CancelledError:
                print('aaaaaaaaaa')
                return
            except Exception as f:
                print('hhhhhhhhhhhhhhhh', f)
                if stop == 4:
                    return

    async def aria2_task(self, uuid: str) -> None:
        with self.lock:
            state: Aria2FileData = self.state[uuid].copy()
        result = await self.get_url('', state['pc'])
        if result['state']:
            url = result['result']
        else:
            with SetData(self.state, uuid, self.lock) as state:
                state.update({
                    'state': StateData.ERROR,
                    'result': result['result'],
                })
            return
        await create_task(self.aria2_rpc(url, uuid))

    async def aria2_rpc(self, url: str, uuid: str) -> None:
        with self.lock:
            state: Aria2FileData = self.state[uuid].copy()
        data = {
            'jsonrpc': '2.0',
            'id': 'qwer',
            'method': 'aria2.addUri',
            'params': [[url], {'allow-overwrite': 'true', 'dir': f"{state['path']}\\",
                               'header': [f'{i[0]}: {i[1]}' for i in self.download.headers.items()]}]
        }
        # 是否檢查sha1
        if self.config['aria2_sha1']:
            data['params'][1]['checksum'] = f'sha-1={state["sha1"]}'
        response = await srequests.async_post(url=self.config['aria2_rpc_url'], json=data)
        with SetData(self.state, uuid, self.lock) as state:
            if response.status_code == 200:
                result = response.json().get("result", [])
                state.update({'gid': result})
            else:
                state.update({
                    'state': StateData.ERROR,
                    'result': '無法調用aria2_rpc',
                })
