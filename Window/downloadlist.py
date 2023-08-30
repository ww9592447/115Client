from datetime import timedelta, datetime
from asyncio import create_task, sleep
from os.path import exists, splitext
from os import remove
from uuid import uuid1
from typing import Callable, Awaitable, Self
from multiprocessing import Lock

from PyQt5.Qt import QWidget

from Modules.image import Image
from Modules.get_data import pybyte, get_path, SetData
from Modules.type import DownloadFileData, DownloadFolderData, GetFolderData, StateData, Config
from .endlist import EndList
from .window import MTextA, MTextB, MList


class QFolder(MTextB[DownloadFolderData]):
    def __init__(
            self,
            state: dict[str, DownloadFolderData],
            data: DownloadFolderData,
            uuid: str,
            lock: Lock,
            queue_list: list[QWidget, ...],
            transmission_list: list[QWidget, ...],
            all_text: list[QWidget, ...],
            get_folder: Callable[[str], Awaitable[GetFolderData]],
            add: Callable[[dict[str, any], bool], None],
            folder_add: Callable[[dict[str, any], bool], None],
            parent: QWidget
    ) -> None:
        super().__init__(
            state,
            data,
            uuid,
            lock=lock,
            queue_list=queue_list,
            transmission_list=transmission_list,
            all_text=all_text,
            parent=parent
        )
        # 獲取資料夾資料
        self.get_folder: Callable[[str], Awaitable[GetFolderData]] = get_folder
        # 新增檔案函數
        self.add: Callable[[dict[str, any], bool], None] = add
        # 新增資料夾函數
        self.folder_add: Callable[[dict[str, any], bool], None] = folder_add
        # 下載路徑
        self.path = data['path']
        # 下載資料夾cid
        self.cid: str = data['cid']

    async def stop(self) -> None:
        self.progressText.setText('獲取資料夾資料中...')
        if (result := await self.get_folder(self.cid))['state']:
            # 新增到下載列表
            for data in result['result'].values():
                data['path'] = self.path
                # 判斷是否是資料夾
                if data['category'] == '0':
                    self.folder_add(data, True)
                else:
                    self.add(data, True)
            with SetData(self.state, self.uuid, self.lock) as state:
                state['state'] = StateData.COMPLETE
            self.end.emit(self)
        else:
            with SetData(self.state, self.uuid, self.lock) as state:
                state.update({'state': StateData.ERROR, 'result': result['result']})
            self.set_state(state['state'], result['result'])


class QText(MTextA[DownloadFileData]):
    def __init__(
            self,
            state: dict[str, DownloadFileData],
            data: DownloadFileData,
            uuid: str,
            lock: Lock,
            queue_list: list[Self, ...],
            transmission_list: list[Self, ...],
            all_text: list[Self, ...],
            set_transmission_size: Callable[[int], None],
            parent: QWidget
    ) -> None:
        super().__init__(
            state,
            data,
            uuid,
            queue_list,
            lock=lock,
            transmission_list=transmission_list,
            all_text=all_text,
            parent=parent
        )
        # 下載路徑
        self.path: str = data['path']
        # 目前下載量
        self.currently_size: int = data['all_size']
        # 設定所有下載總量
        self.set_transmission_size: Callable[[int], None] = set_transmission_size
        # 設置禁止取消任務
        self.task_cancel: bool = False
        # 計算下載速度
        self.sample_times, self.sample_values = [], []
        self.INTERVAL, self.samples = timedelta(milliseconds=100), timedelta(seconds=2)

    async def stop(self) -> None:
        self.progressText.setText('下載請求中...')
        while 1:
            with self.lock:
                state = self.state[self.uuid].copy()

            if state['start'] and state['state'] == StateData.NONE:
                # 設定下載速度
                self.get_rate(state['all_size'])
            elif state['state'] == StateData.TEXT and self.progressText.text() != '檢測sha1中...':
                self.progressText.setText('檢測sha1中...')
            elif state['start'] is False and state['state'] != StateData.NONE:
                self.get_rate(state['all_size'])
                self.sample_times, self.sample_values = [], []
                self.currently_size = state['all_size']
                self.set_state(state['state'], state['result'])
                return
            await sleep(0.1)

    # 設定進度速率
    def get_rate(self, size: int) -> None:
        # 查看採樣時間是否有數據
        if self.sample_times:
            # 獲取最新的採樣時間
            sample_time = self.sample_times[-1]
        else:
            # 初始化採樣時間
            sample_time = datetime.min
        # 獲取目前時間
        t = datetime.now()
        # 查看 目前時間-目前採樣時間 是否大於 100毫秒
        if t - sample_time > self.INTERVAL:
            # 添加目前時間到採樣時間列表
            self.sample_times.append(t)
            # 添加目前下載總大小到 樣本列表
            self.sample_values.append(size)
            # 獲取目前時間-2秒之後的值
            minimum_time = t - self.samples
            # 獲取目前下載總大小
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
            try:
                if self.progressBar.value() != (_size := int(size / self.length * 100)):
                    self.progressBar.setValue(_size)
                    self.progressBar.update()
                self.set_transmission_size(size - self.currently_size)
                self.currently_size = size
                self.file_size.setText(f'{pybyte(size)}/{pybyte(self.length)}')
                self.progressText.setText(pybyte(speed, s=True))
            except Exception as f:
                print(f)


class DownloadList(MList[DownloadFileData | DownloadFolderData]):
    def __init__(
            self,
            state: dict[str, DownloadFileData | DownloadFolderData],
            lock: Lock,
            wait: list[str, ...],
            wait_lock: Lock,
            config: Config,
            end_list: EndList,
            get_folder: Callable[[str], Awaitable[GetFolderData]],
            set_index: Callable[[int], None],
            parent: QWidget
    ) -> None:
        super().__init__(state, lock, wait, wait_lock, set_index, parent)
        # 下載目錄
        self.download_path: str = get_path(config['download_path'])
        # 最大下載數
        self.download_max: int = config['download_max']
        # 正在傳輸 sha1 列表
        self.sha1list: list[str, ...] = []
        # 獲取目錄資料
        self.get_folder: Callable[[str], Awaitable[GetFolderData]] = get_folder
        # 下載完畢窗口
        self.end_list: EndList = end_list
        # 開始檢查循環
        create_task(self.stop())

    async def stop(self) -> None:
        while 1:
            if len(self.transmission_list) < self.download_max and self.queue_list:
                # 提取待下載列表第一個
                text = self.queue_list.pop(0)
                # 添加到下載列表
                self.transmission_list.append(text)
                # 把text 轉成下載中
                text.set_switch(True)
                with SetData(self.state, text.uuid, self.lock) as state:
                    # 檢查是否是檔案
                    if isinstance(text, QText):
                        # 資料 初始化
                        state.update({'start': False, 'state': StateData.NONE, 'result': ''})
                        if text.progressText.text() == '檔案下載 不完全':
                            if exists(self.path):
                                remove(self.path)
                            state.update({'all_size': 0, 'url': '', 'all_range': {}})
                        with self.wait_lock:
                            self.wait.append(text.uuid)
                text.task = create_task(text.stop())
            await sleep(0.5)

    # 獲取檔案是否存在並返回可添加後輟名
    def get_index(self, path: str, name: str, ico: str, index: int) -> tuple[str, str]:
        if exists(f'{path}\\{name}({index}){ico}'):
            return self.get_index(path, name, ico, index + 1)
        else:
            return f'{name}({index}){ico}', f'{path}\\{name}({index}){ico}'

    # 添加
    def add(self, data: dict[str, any], value: bool = True) -> None:
        # 查看是否重複添加
        if data['sha1'] in self.sha1list:
            # 如果重複添加則退出
            return
        else:
            # 不是重複添加 則加入
            self.sha1list.append(data['sha1'])
        # 查看是否是第一次新增
        if value:
            # 獲取 下載路徑
            path = data["path"] if 'path' in data else self.download_path
            # 查看 下載路徑檔案是否存在
            # 如果存在則在後面新增 數字
            if exists(f'{path}\\{data["name"]}'):
                # 獲取 名稱 後輟
                name, ico = splitext(data['name'])
                # 獲取 更改名稱後的 檔案名稱 路徑+檔案名稱
                name, path = self.get_index(path, name, ico, 0)
            else:
                # 獲取檔案名稱
                name = data["name"]
                # 獲取路徑+檔案名稱
                path = f'{path}\\{data["name"]}'

            data: DownloadFileData = DownloadFileData(
                start=False,
                pc=data['pc'],
                name=name,
                ico=data['ico'],
                sha1=data['sha1'],
                path=path,
                file_size=data['size'],
                url='',
                all_size=0,
                all_range={},
                state=StateData.NONE,
                result=''
            )
        # 獲取 uuid
        uuid = f'2{uuid1().hex}'
        text = QText(
            self.state, data, uuid, self.lock, self.queue_list, self.transmission_list,
            self.all_text, self.set_transmission_size, parent=self.scroll_contents
        )
        self._add(data, uuid, text, value)

    # 添加資料夾
    def folder_add(self, data: dict[str, any], value: bool = True) -> None:
        if value:
            path = f'{data["path"]}\\{data["name"]}' if 'path' in data else f'{self.download_path}\\{data["name"]}'
            data = DownloadFolderData(
                state=StateData.NONE,
                path=path,
                name=data['name'],
                cid=data['cid'],
                ico=Image.MIN_FOLDER,
                result=''
            )
        uuid = f'_{uuid1().hex}'
        text = QFolder(
            self.state, data, uuid, self.lock, self.queue_list, self.transmission_list,
            self.all_text, self.get_folder, self.add, self.folder_add, parent=self.scroll_contents
        )
        self._add(data, uuid, text, value)

    def cancel(self, text: QText | QFolder, data: DownloadFileData | DownloadFolderData) -> None:
        if isinstance(text, QText):
            if exists(text.path):
                remove(text.path)
            self.set_transmission_size(-text.currently_size)
            self.sha1list.remove(data['sha1'])

    # 下載完畢回調
    def complete(self, text: QText | QFolder, data: DownloadFileData | DownloadFolderData) -> None:
        if isinstance(text, QText):
            self.sha1list.remove(data['sha1'])
            self.end_list.add(text.path, text.name, data['ico'], pybyte(data['file_size']), Image.DOWNLOAD_COMPLETED)
