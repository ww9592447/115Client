from module import datetime, uuid1, exists, create_task, sleep, pybyte, splitext, Union, \
    timedelta, remove, setstate, MQList, MQtext1, MQtext2, getpath, Lock, ConfigParser, QObject, \
    Callable, Awaitable
from .endlist import EndList


class QFolder(MQtext2):
    def __init__(
            self,
            state: dict[str, any],
            data: dict[str, any],
            uuid: str,
            queuelist: list[QObject, ...],
            transmissionlist: list[QObject, ...],
            allqtext: list[QObject, ...],
            getfolder: Callable[[str], Awaitable[tuple[bool, Union[dict[str, dict[str, any]], str]]]],
            add: Callable[[dict[str, any], bool], None],
            folder_add: Callable[[dict[str, any], bool], None],
            parent: QObject
    ) -> None:
        super().__init__(state, data, uuid, queuelist=queuelist, transmissionlist=transmissionlist,
                         allqtext=allqtext, parent=parent)
        # 獲取資料夾資料
        self.getfolder: Callable[[str], Awaitable[tuple[bool, Union[dict[str, dict[str, any]], str]]]] = getfolder
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
        if (result := await self.getfolder(self.cid))[0]:
            # 新增到下載列表
            for data in result[1].values():
                data['path'] = self.path
                # 判斷是否是資料夾
                if data['category'] == '0':
                    self.folder_add(data, True)
                else:
                    self.add(data, True)
        else:
            self.setdata({'state': 'error', 'result': result[1]})
        self.end.emit(self)


class Qtext(MQtext1):
    def __init__(
            self,
            state: dict[str, any],
            data: dict[str, any],
            uuid: str,
            lock: Lock,
            queuelist: list[QObject, ...],
            transmissionlist: list[QObject, ...],
            allqtext: list[QObject, ...],
            settransmissionsize: Callable[[int], None],
            parent: QObject
    ) -> None:
        super().__init__(state, data, uuid, lock=lock, queuelist=queuelist, transmissionlist=transmissionlist,
                         allqtext=allqtext, parent=parent)
        # 下載路徑
        self.path: str = data['path']
        # 目前下載量
        self.size: int = data['size']
        # 設定所有下載總量
        self.settransmissionsize: Callable[[int], None] = settransmissionsize
        # 設置禁止取消任務
        self.cancel: bool = False
        # 計算下載速度
        self.sample_times, self.sample_values = [], []
        self.INTERVAL, self.samples = timedelta(milliseconds=100), timedelta(seconds=2)

    async def stop(self) -> None:
        self.progressText.setText('下載請求中...')
        while 1:
            state = self.state[self.uuid]
            if state['stop']:
                if state['state'] is None and self.size != state['size']:
                    # 設定下載速率
                    self.get_rate(state['size'])
                elif self.progressText.text() != '檢測sha1中...' and state['state'] == '檢測中':
                    self.progressText.setText('檢測sha1中...')
            elif not state['stop'] and state['state']:
                self.size = state['size']
                self.setdata(state)
                return
            await sleep(0.1)

    # 設定進度速率
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
            try:
                if self.progressBar.value() != (_size := int(size / self.length * 100)):
                    self.progressBar.setValue(_size)
                    self.progressBar.update()
                self.settransmissionsize(size - self.size)
                self.size = size
                self.file_size.setText(f'{pybyte(size)}/{pybyte(self.length)}')
                self.progressText.setText(pybyte(speed, s=True))
            except Exception as f:
                print(f)


class DownloadList(MQList):
    def __init__(
            self,
            state: dict[str, any],
            lock: Lock,
            wait: list[str, ...],
            waitlock: Lock,
            config: ConfigParser,
            endlist: EndList,
            getfolder: Callable[[str], Awaitable[tuple[bool, Union[dict[str, dict[str, any]], str]]]],
            setindex: Callable[[int], None],
            parent: QObject
    ) -> None:
        super().__init__(state, lock, wait, waitlock, setindex, parent)
        # 下載目錄
        self.download_path: str = getpath(config['Download']['下載路徑'])
        # 最大下載數
        self.download_max: int = int(config['Download']['最大同時下載數'])
        # 正在傳輸 sha1 列表
        self.sha1list: list[str, ...] = []
        # 獲取目錄資料
        self.getfolder: Callable[[str], Awaitable[tuple[bool, Union[dict[str, dict[str, any]], str]]]] = getfolder
        # 下載完畢窗口
        self.endlist: EndList = endlist
        # 開始檢查循環
        create_task(self.stop())

    async def stop(self) -> None:
        while 1:
            if len(self.transmissionlist) < self.download_max and self.queuelist:
                # 提取待下載列表第一個
                qtext = self.queuelist.pop(0)
                # 添加到下載列表
                self.transmissionlist.append(qtext)
                # 把qtext 轉成下載中
                qtext.set_switch(True)
                with self.lock:
                    with setstate(self.state, qtext.uuid) as state:
                        # 檢查是否是檔案
                        if qtext.uuid[0] == '0':
                            # 資料 初始化
                            state.update({'state': None, 'stop': True})
                            if qtext.progressText.text() == '檔案下載 不完全':
                                if exists(self.path):
                                    remove(self.path)
                                state.update({'size': 0, 'url': None, 'range': {}})
                            with self.waitlock:
                                self.wait.append(qtext.uuid)
                qtext.task = create_task(qtext.stop())
            await sleep(0.1)

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
            # 設置資料
            data = {
                'pc': data['pc'], 'name': name, 'ico': data['ico'], 'length': data['size'],
                'sha1': data['sha1'], 'size': 0, 'url': None, 'range': {},
                'path': path, 'state': None, 'result': None, 'stop': None
            }
        # 獲取 uuid
        uuid = f'0{uuid1().hex}'
        qtext = Qtext(
            self.state, data, uuid, self.lock, self.queuelist, self.transmissionlist,
            self.allqtext, self.settransmissionsize, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 添加資料夾
    def folder_add(self, data: dict[str, any], value: bool = True) -> None:
        if value:
            path = f'{data["path"]}\\{data["name"]}' if 'path' in data else f'{self.download_path}\\{data["name"]}'
            data = {'path': path, 'name': data["name"], 'cid': data['cid'], 'ico': '資料夾'}
        uuid = f'1{uuid1().hex}'
        qtext = QFolder(
            self.state, data, uuid, self.queuelist, self.transmissionlist,
            self.allqtext, self.getfolder, self.add, self.folder_add, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 關閉回調
    def close(self, qtext: QObject, data: dict[str, any]) -> None:
        if exists(qtext.path):
            remove(qtext.path)
        self.settransmissionsize(-qtext.size)
        self.sha1list.remove(data['sha1'])

    # 下載完畢回調
    def complete(self, qtext: QObject, data: dict[str, any]) -> None:
        self.sha1list.remove(data['sha1'])
        self.endlist.add(qtext.path, qtext.name, data['ico'], pybyte(data['length']), '下載完成')
