from multiprocessing import Lock
from asyncio import create_task, sleep
from uuid import uuid1
from typing import Callable, Awaitable

from Modules.get_data import pybyte, get_path, SetData
from Modules.type import Aria2FileData, StateData, DownloadFolderData, GetFolderData, Config
from Modules.image import Image
from Modules import srequests

from PyQt5.Qt import QWidget
from .window import MList, MTextA, MTextB
from .endlist import EndList


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


class QText(MTextA[Aria2FileData]):
    def __init__(
            self,
            state: dict[str, Aria2FileData],
            data: Aria2FileData,
            uuid: str,
            lock: Lock,
            queue_list: list[QWidget, ...],
            transmission_list: list[QWidget, ...],
            all_text: list[QWidget, ...],
            set_transmission_size: Callable[[int], None],
            rpc_url: str,
            parent: QWidget
    ) -> None:
        super().__init__(state, data, uuid, queue_list, lock=lock,
                         transmission_list=transmission_list, all_text=all_text, parent=parent)
        # aria2 url
        self.rpc_url: str = rpc_url
        # aria2 gid
        self.gid: str | None = None
        # 設定所有下載總量
        self.set_transmission_size: Callable[[int], None] = set_transmission_size
        # 目前傳輸大小
        self.size: int = 0
        # 禁止取消任務
        self.cancel = False

    async def stop(self) -> None:
        self.progressText.setText('下載請求中...')
        while not self.gid:
            with self.lock:
                state = self.state[self.uuid].copy()
            if state['gid']:
                self.gid = state['gid']
                break
            elif state['state'] == StateData.ERROR:
                self.set_state(state['state'], state['result'])
                return
            await sleep(0.1)

        while 1:
            with self.lock:
                state = self.state[self.uuid].copy()
            result = await self.aria2_rpc(self.gid, 'aria2.tellStatus')
            if result['status'] == 'complete':
                self.end.emit(self)
                return
            elif result['status'] in ['removed', 'paused']:
                return
            elif state['state'] == StateData.PAUSE:
                await self.aria2_rpc(self.gid, 'aria2.pause')
            elif state['state'] == StateData.CANCEL:
                await self.aria2_rpc(self.gid, 'aria2.remove')
            elif result and self.progressText.text not in ['等待暫停中...', '等待關閉中中...']:
                self.set_transmission_size(int(result["completedLength"]) - self.size)
                self.size = int(result["completedLength"])
                self.file_size.setText(f'{pybyte(int(result["completedLength"]))}/{pybyte(self.length)}')
                self.progressText.setText(pybyte(int(result["downloadSpeed"]), s=True))
                if self.progressBar.value() != (_size := int(int(result["completedLength"]) / self.length * 100)):
                    self.progressBar.setValue(_size)
                    self.progressBar.update()
            elif result is False:
                self.set_state(StateData.ERROR, 'aria2_rpc連接失敗')
                return
            await sleep(0.1)

    async def aria2_rpc(self, gid: str, aria2: str) -> dict[str, str] | bool:
        data = {
            "jsonrpc": "2.0",
            "id": 'sdfg',
            'method': aria2,
            # 檢測狀態
            # aria2.tellStatus
            # 恢復
            # 'method': 'aria2.unpause',
            # 暫停
            # 'method': 'aria2.pause',
            # 刪除
            # 'method': 'aria2.remove',
            'params': [gid]
        }
        response = await srequests.async_post(url=self.rpc_url, json=data)
        if response.status_code == 200:
            return response.json()['result']
        return False


class Aria2List(MList[Aria2FileData | DownloadFolderData]):
    def __init__(
            self,
            state: dict[str, Aria2FileData | DownloadFolderData],
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
        # rpc_url
        self.rpc_url: str = config['aria2_rpc_url']
        # 最大下載數
        self.aria2_rpc_max: int = config['aria2_rpc_max']
        # 正在下載 sha1 列表
        self.sha1list: list[str, ...] = []
        # 獲取資料夾資料
        self.get_folder: Callable[[str], Awaitable[GetFolderData]] = get_folder
        # 下載完畢窗口
        self.end_list: EndList = end_list
        # 開始檢查循環
        create_task(self.stop())

    async def stop(self) -> None:
        while 1:
            if len(self.transmission_list) < self.aria2_rpc_max and self.queue_list:
                # 提取待下載列表第一個
                text = self.queue_list.pop(0)
                # 添加到下載列表
                self.transmission_list.append(text)
                # 把text 轉成下載中
                text.set_switch(True)
                if isinstance(text, QText):
                    if text.gid:
                        with SetData(self.state, text.uuid, self.lock) as state:
                            state.update({'state': StateData.NONE, 'result': ''})
                        await create_task(text.aria2_rpc(text.gid, 'aria2.unpause'))
                    else:
                        with self.wait_lock:
                            self.wait.append(text.uuid)
                text.task = create_task(text.stop())
            await sleep(0.1)

    # 添加
    def add(self, data: dict[str, any], value: bool = True) -> None:
        if data['sha1'] in self.sha1list:
            return
        else:
            self.sha1list.append(data['sha1'])
        if value:
            path = get_path(data["path"])
            data: Aria2FileData = Aria2FileData(
                file_size=data['size'],
                ico=data['ico'],
                name=data['name'],
                pc=data['pc'],
                sha1=data['sha1'],
                all_size=0,
                path=path,
                gid='',
                result='',
                state=StateData.NONE
            )
        uuid = f'4{uuid1().hex}'
        text = QText(
            self.state, data, uuid, self.lock, self.queue_list, self.transmission_list,
            self.all_text, self.set_transmission_size, self.rpc_url, parent=self.scroll_contents
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

    def cancel(self, text: QFolder | QText, data: Aria2FileData | DownloadFolderData) -> None:
        if isinstance(text, QText):
            self.set_transmission_size(-text.size)
            self.sha1list.remove(data['sha1'])

    # 下載完畢回調
    def complete(self, text: QText | QFolder, data: Aria2FileData | DownloadFolderData) -> None:
        if isinstance(text, QText):
            self.sha1list.remove(data['sha1'])
            self.end_list.add(text.path, text.name, data['ico'], pybyte(data['length']), Image.DOWNLOAD_COMPLETED)
