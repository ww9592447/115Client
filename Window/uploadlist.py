from typing import Callable, AsyncIterable
from multiprocessing import Lock
from datetime import timedelta, datetime
from asyncio import create_task, sleep
from os.path import getsize
from uuid import uuid1

from PyQt5.Qt import QWidget

from Modules.get_data import pybyte, SetData
from Modules.type import AllCidData, UploadFileData, UploadFolderData, Config
from Modules.image import Image
from Window.window import MTextA, MTextB, MList, StateData
from .endlist import EndList


class QFolder(MTextB[UploadFolderData]):
    def __init__(
            self,
            state: dict[str, UploadFolderData],
            data: UploadFolderData,
            uuid: str,
            lock: Lock,
            queue_list: list[QWidget, ...],
            transmission_list: list[QWidget, ...],
            all_text: list[QWidget, ...],
            search_add_folder: Callable[[str, str], AsyncIterable[tuple[StateData, str]]],
            parent: QWidget
    ) -> None:
        super().__init__(state, data, uuid, lock=lock, queue_list=queue_list, transmission_list=transmission_list,
                         all_text=all_text, parent=parent)
        # 搜索資料夾 如果沒有則創建資料夾
        self.search_add_folder: Callable[[str, str], AsyncIterable[tuple[StateData, str]]] = search_add_folder

    async def stop(self) -> None:
        self.progressText.setText('查找資料夾中')
        with self.lock:
            state = self.state[self.uuid].copy()
        async for result in self.search_add_folder(state['cid'], state['dir']):
            self.set_state(result[0], result[1])


class QText(MTextA[UploadFileData]):
    def __init__(
            self,
            state: dict[str, UploadFileData],
            data: UploadFileData,
            uuid: str,
            wait: list[str, ...],
            wait_lock: Lock,
            lock: Lock,
            queue_list: list[QWidget, ...],
            transmission_list: list[QWidget, ...],
            all_text: list[QWidget, ...],
            set_transmission_size: Callable[[int], None],
            search_add_folder: Callable[[str, str], AsyncIterable[tuple[StateData, str]]],
            parent: QWidget
    ) -> None:
        super().__init__(state, data, uuid, queue_list, lock=lock,
                         transmission_list=transmission_list, all_text=all_text, parent=parent)
        # 傳送列表
        self.wait: list[str, ...] = wait
        # 傳送列表鎖
        self.wait_lock: Lock = wait_lock
        # 搜索資料夾 如果沒有則創建資料夾
        self.search_add_folder: Callable[[str, str], AsyncIterable[tuple[StateData, str]]] = search_add_folder
        # 設定所有下載總量
        self.set_transmission_size: Callable[[int], None] = set_transmission_size
        # 上傳檔案路徑
        self.path: str = data['path']
        # 目前上傳量
        self.all_size: int = data['all_size']
        # 計算上傳速度
        self.sample_times, self.sample_values = [], []
        self.INTERVAL, self.samples = timedelta(milliseconds=100), timedelta(seconds=2)

    async def stop(self) -> None:
        with self.lock:
            state = self.state[self.uuid].copy()
        if state['dir']:
            self.progressText.setText('查找資料夾中')
            async for result in self.search_add_folder(state['cid'], state['dir']):
                if result[0] == StateData.COMPLETE:
                    with SetData(self.state, self.uuid, self.lock) as state:
                        state.update({'cid': result[1], 'dir': ''})
                else:
                    self.set_state(result[0], result[1])
        self.task_cancel = False
        with self.wait_lock:
            self.wait.append(self.uuid)
        self.progressText.setText('上傳請求中...')
        while 1:
            with self.lock:
                state = self.state[self.uuid].copy()
            if state['start'] and state['state'] == StateData.NONE:
                self.get_rate(state['all_size'])
            elif not state['start'] and state['state'] != StateData.NONE:
                self.get_rate(state['all_size'])
                self.sample_times, self.sample_values = [], []
                self.set_state(state['state'], state['result'])
                return
            await sleep(0.1)

    # 獲取進度速率
    def get_rate(self, size: int) -> None:
        if self.sample_times:
            sample_time = self.sample_times[-1]
        else:
            sample_time = datetime.min
        t = datetime.now()
        if t - sample_time > self.INTERVAL:
            self.sample_times.append(t)
            self.sample_values.append(size)

            minimum_time = t - self.samples
            minimum_value = self.sample_values[-1]
            while (self.sample_times[2:] and minimum_time > self.sample_times[1] and
                   minimum_value > self.sample_values[1]):
                self.sample_times.pop(0)
                self.sample_values.pop(0)

        delta_time = self.sample_times[-1] - self.sample_times[0]
        delta_value = self.sample_values[-1] - self.sample_values[0]
        if delta_time:
            speed = delta_value / delta_time.total_seconds()
            if speed < 0:
                speed = 0
                self.sample_times, self.sample_values = [], []
            try:
                if self.progressBar.value() != (_size := int(size / self.length * 100)):
                    self.progressBar.setValue(_size)
                    self.progressBar.update()
                self.set_transmission_size(size - self.all_size)
                self.all_size = size
                self.file_size.setText(f'{pybyte(size)}/{pybyte(self.length)}')
                self.progressText.setText(pybyte(speed, s=True))
            except (Exception, ):
                pass


class UploadList(MList[UploadFileData | UploadFolderData]):
    def __init__(
            self,
            state: dict[str, UploadFileData | UploadFolderData],
            lock: Lock,
            wait: list[str, ...],
            wait_lock: Lock,
            config: Config,
            end_list: EndList,
            set_index: Callable[[int], None],
            all_cid_data: dict[str, AllCidData],
            search_add_folder: Callable[[str, str], AsyncIterable[tuple[StateData, str]]],
            parent: QWidget
    ) -> None:
        super().__init__(state, lock, wait, wait_lock, set_index, parent)
        # 最大上傳數
        self.upload_max: int = config['upload_max']
        # 所有目錄資料
        self.all_cid_data: dict[str, AllCidData] = all_cid_data
        # 下載完畢窗口
        self.end_list: EndList = end_list
        # 搜索資料夾 如果沒有則創建資料夾
        self.search_add_folder: Callable[[str, str], AsyncIterable[tuple[StateData, str]]] = search_add_folder
        # 添加資料夾任務
        self.folder_task = {}
        # 開始檢查循環
        create_task(self.stop())

    async def stop(self) -> None:
        while 1:
            if len(self.transmission_list) < self.upload_max and self.queue_list:
                # 提取待下載列表第一個
                text = self.queue_list.pop(0)
                # 添加到下載列表
                self.transmission_list.append(text)
                # 把text 轉成下載中
                text.set_switch(True)
                # 檢查是否是檔案
                if isinstance(text, QText):
                    with SetData(self.state, text.uuid, self.lock) as state:
                        state.update({'state': StateData.NONE, 'start': False, 'result': ''})
                text.task = create_task(text.stop())
            await sleep(0.1)

    # 添加上傳文件
    def add(self, data: dict[str, any], value: bool = True) -> None:
        if value:
            data = UploadFileData(
                bucket='',
                upload_key='',
                cb={},
                url='',
                upload_id='',
                path=data['path'],
                all_size=0,
                all_range={},
                parts={},
                file_size=getsize(data['path']),
                ico=data['ico'],
                cid=data['cid'],
                dir=data['dir'],
                second=False,
                state=StateData.NONE,
                name=data['name'],
                sha1='',
                result='',
                start=False
            )
        uuid = f'3{uuid1().hex}'

        text = QText(
            self.state, data, uuid, self.wait, self.wait_lock, self.lock, self.queue_list,
            self.transmission_list, self.all_text, self.set_transmission_size,
            self.search_add_folder, self.scroll_contents
        )
        self._add(data, uuid, text, value)

    # 新增傳空白資料夾
    def new_folder_add(self, data: dict[str, any], value: bool = True) -> None:
        if value:
            data = UploadFolderData(
                cid=data['cid'],
                dir=data['dir'],
                name=data['name'],
                ico=Image.MIN_FOLDER
            )
        uuid = f'_{uuid1().hex}'
        text = QFolder(
            self.state, data, uuid, self.lock, self.queue_list, self.transmission_list, self.all_text,
            self.search_add_folder, parent=self.scroll_contents
        )
        self._add(data, uuid, text, value)

    def cancel(self, text: QText | QFolder, data: UploadFileData) -> None:
        if isinstance(text, QText):
            self.all_size -= text.length
            self.transmission_size -= text.all_size
            if self.all_size != 0:
                self.progressbar.setValue(int(self.transmission_size / self.all_size * 100))

    # 上傳完成 回調
    def complete(self, text: QText | QFolder, data: UploadFileData) -> None:
        with self.lock:
            state = self.state[text.uuid].copy()
        if data['state'] == StateData.CANCEL:
            self.set_transmission_size(state['file_size'])
        if data['result'] == '上傳完成':
            image = Image.UPLOAD_COMPLETED
        else:
            image = Image.COMPLETED

        if isinstance(text, QText):
            self.end_list.add(
                text.path,
                text.name,
                data['ico'],
                pybyte(int(data['file_size'])),
                image,
                cid=data['cid'])

        if state['cid'] in self.all_cid_data:
            self.all_cid_data[state['cid']]['refresh'] = True
