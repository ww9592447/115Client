from multiprocessing import Lock
from asyncio import create_task, sleep, gather, CancelledError, Future

from Modules.type import UploadFileData, StateData, Config
from Modules.get_data import SetData
from Modules.Callback import Callback
from API.upload import Upload
from API.directory import Directory


def get_range(size: int) -> dict[str, tuple[int, int]]:
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


class UploadTask:
    def __init__(
            self,
            upload: Upload,
            state: dict[str, UploadFileData],
            lock: Lock,
            directory: Directory,
            config: Config
    ) -> None:
        # 共享數據
        self.state: dict[str, UploadFileData] = state
        # 共享數據鎖
        self.lock: Lock = lock
        # 用戶資料
        self.config: Config = config
        # 上傳API
        self.upload: Upload = upload
        # 115API
        self.directory: Directory = directory
        # 初始化上傳任務
        self.task: dict[str, Future] = {}

    async def upload_task(self, uuid: str) -> None:
        with self.lock:
            state = self.state[uuid].copy()
        # 檢查是否秒傳
        if state['second'] is False:
            result = await self.upload.upload_file_by_sha1(
                state['path'], str(state['file_size']), state['name'], state['cid']
            )
            with SetData(self.state, uuid, self.lock) as state:
                if result['state'] is False:
                    state.update({'start': False, 'state': StateData.ERROR, 'result': result['result']})
                    return
                # 需要上傳
                elif 'sha1_data' in result:
                    sha1_data = result['sha1_data']
                    state.update({
                        'second': True,
                        'bucket': sha1_data['bucket'],
                        'cb': sha1_data['cb'],
                        'upload_key': sha1_data['upload_key']
                    })
                # 秒傳成功
                else:
                    state.update({'start': False, 'state': StateData.COMPLETE, 'result': result['result']})
                    return

        # 檢查是否有url
        if not state['url']:
            # 獲取url
            result = await self.upload.get_url(state['bucket'], state['upload_key'])
            if result['state'] is False:
                with SetData(self.state, uuid, self.lock) as state:
                    state.update({'start': False, 'state': StateData.ERROR, 'result': result['result']})
                return
            url = result['result']
            # 獲取upload_id
            result = await self.upload.get_upload_id(url, state['upload_key'])

            if result['state'] is False:
                with SetData(self.state, uuid, self.lock) as state:
                    state.update({'start': False, 'state': StateData.ERROR, 'result': result['result']})
                return

            upload_id = result['result']

            with SetData(self.state, uuid, self.lock) as state:
                state.update({
                    'url': url,
                    'upload_id': upload_id,
                    'all_range': get_range(state['file_size'])
                })
        with SetData(self.state, uuid, self.lock) as state:
            state['start'] = True

        callback = Callback()
        callback.all_size = state['all_size']
        task_list = []
        # 獲取所有下載index
        all_index = list(state['all_range'].keys())
        for _ in range(self.config['upload_thread_max']):
            task_list.append(create_task(self.upload_all_part(uuid, callback, all_index)))
        result = gather(*task_list)
        self.task[uuid] = result
        create_task(self.set_size(uuid, callback))
        try:
            await result
        except CancelledError:
            for task in task_list:
                task.cancel()
            for task in task_list:
                if not task.done():
                    await task
            with SetData(self.state, uuid, self.lock) as state:
                state.update({'start': False, 'all_size': callback.all_size})
            return
        with self.lock:
            state = self.state[uuid].copy()
        result = await self.upload.combine(
            state['url'],
            state['parts'],
            state['upload_id'],
            state['upload_key'],
            state['cb']
        )

        if result['state'] is True:
            with SetData(self.state, uuid, self.lock) as state:
                state.update({'start': False, 'state': StateData.COMPLETE, 'result': '上傳完成'})
        elif result['state'] is False:
            with SetData(self.state, uuid, self.lock) as state:
                print(state)
                state.update({'start': False, 'state': StateData.ERROR, 'result': result['result']})

    async def upload_all_part(self, uuid: str, callback: Callback, all_index: list[str, ...]) -> None:
        with self.lock:
            state = self.state[uuid].copy()
        with open(state['path'], 'rb') as file:
            while 1:
                if not all_index:
                    return
                index = all_index.pop(0)

                offset, length = state['all_range'][index]
                try:
                    result = await self.upload.upload_part(
                        file,
                        callback,
                        state['url'],
                        state['upload_key'],
                        state['upload_id'],
                        index,
                        offset,
                        length,
                    )
                except CancelledError:
                    return
                with SetData(self.state, uuid, self.lock) as state:
                    if result['state'] is True:
                        del state['all_range'][index]
                        state['parts'][str(index)] = result['result']
                    elif result['state'] is False:
                        state.update({'state': StateData.ERROR, 'result': result['result']})
                        raise CancelledError

    async def set_size(self, uuid: str, callback: Callback) -> None:
        while not self.task[uuid].done():
            with SetData(self.state, uuid, self.lock) as state:
                if state['state'] in (StateData.ERROR, StateData.PAUSE, StateData.CANCEL):
                    self.task[uuid].cancel()
                else:
                    state['all_size'] = callback.all_size
            await sleep(0.1)
        del self.task[uuid]
