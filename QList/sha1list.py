from pyperclip import copy
from module import create_task, sleep, uuid1, Qt, QTextEdit, Frame, getsize, \
    MyQLabel, MQList, MQtext2, QMessageBox, QFileDialog, setstate, Lock, \
    QObject, Callable, Awaitable, Union, QResizeEvent


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
        # 下載資料夾cid
        self.cid: str = data['cid']
        # 保存路徑
        self.dir: str = data['dir']

    async def stop(self) -> None:
        self.progressText.setText('獲取資料夾資料中...')
        if (result := await self.getfolder(self.cid))[0]:
            # 新增到下載列表
            for data in result[1].values():
                # 判斷是否是資料夾
                if data['category'] == '0':
                    data['dir'] = f"{self.dir}|{data['name']}"
                    self.folder_add(data, True)
                else:
                    data['dir'] = self.dir
                    self.add(data, True)
        else:
            self.setstate({'state': 'error', 'result': result[1]})
        self.end.emit(self)

    # 設置禁止打開
    def open(self) -> None:
        pass


class Qtext(MQtext2):
    def __init__(
            self,
            state: dict[str, any],
            data: dict[str, any],
            uuid: str,
            lock: Lock,
            queuelist: list[QObject, ...],
            transmissionlist: list[QObject, ...],
            allqtext: list[QObject, ...],
            sha1text: QTextEdit, parent=None):
        super().__init__(state, data, uuid, lock=lock, queuelist=queuelist, transmissionlist=transmissionlist,
                         allqtext=allqtext, parent=parent)
        # 獲取 sha1文本框
        self.sha1text: QTextEdit = sha1text
        # 禁止取消任務
        self.cancel = False

    async def stop(self) -> None:
        self.progressText.setText('獲取sha1鏈結中...')
        while 1:
            state = self.state[self.uuid]
            if not state['stop']:
                if state['blockhash']:
                    _sha1 = f"115://{self.name}|{state['length']}|{state['sha1']}|{state['blockhash']}"
                    if state['dir']:
                        _sha1 += f"|{state['dir']}"
                    self.sha1text.append(_sha1)
                    self.end.emit(self)
                elif state['state']:
                    self.setstate(state)
                return
            await sleep(0.1)


class Sha1List(MQList):
    def __init__(
            self,
            state: dict[str, any],
            lock: Lock,
            wait: list[str, ...],
            waitlock: Lock,
            getfolder: Callable[[str], Awaitable[tuple[bool, Union[dict[str, dict[str, any]], str]]]],
            setindex: Callable[[int], None],
            parent: QObject
    ) -> None:
        super().__init__(state, lock, wait, waitlock, setindex, parent)
        # 獲取目錄資料
        self.getfolder: Callable[[str], Awaitable[tuple[bool, Union[dict[str, dict[str, any]], str]]]] = getfolder
        # 設置sha1文本框
        self.sha1text: QTextEdit = QTextEdit(self)
        # 設置sha1文本框 禁止輸入
        self.sha1text.setAcceptDrops(False)
        # 設置sha1文本框 不能點擊
        self.sha1text.setFocusPolicy(Qt.NoFocus)
        # 設置sha1文本框 禁止換行
        self.sha1text.setLineWrapMode(QTextEdit.NoWrap)
        # 設置sha1文本框 字體大小
        self.sha1text.setFontPointSize(15)
        # 設置sha1文本框 設置qss
        self.sha1text.setStyleSheet(
            'border-style:solid;border-top-width:1;border-left-width:1px;border-color: rgba(200, 200, 200, 125)'
        )
        # 設置複製全部按鈕
        self.copy: MyQLabel = MyQLabel('複製全部', (10, 8, 111, 41), fontsize=16, clicked=self._copy, parent=self)
        # 設置另存新檔按鈕
        self.save: MyQLabel = MyQLabel('另存新檔', (130, 8, 111, 41), fontsize=16, clicked=self._save, parent=self)
        # 設置清空按鈕
        self.cls: MyQLabel = MyQLabel('清空', (250, 8, 111, 41), fontsize=16, clicked=self.sha1text.clear, parent=self)

        # 中間分隔線
        self.frame: Frame = Frame(self)
        # 開始檢查循環
        # create_task(self.stop())

    async def stop(self) -> None:
        while 1:
            if self.queuelist and not self.transmissionlist:
                qtext = self.queuelist.pop(0)
                # 把qtext 轉成上傳中
                qtext.set_switch(True)
                # 添加到上傳列表
                self.transmissionlist.append(qtext)
                if qtext.uuid[0] in ['4', '8']:
                    with self.lock:
                        with setstate(self.state, qtext.uuid) as state:
                            # 資料 初始化
                            state.update({'state': None, 'stop': True})
                qtext.task = create_task(qtext.stop())
                with self.waitlock:
                    self.wait.append(qtext.uuid)
            await sleep(0.1)

    def _copy(self) -> None:
        copy(self.sha1text.toPlainText())
        QMessageBox.about(self, "複製", "複製完畢")

    def _save(self) -> None:
        if self.sha1text.toPlainText():
            path, _ = QFileDialog.getSaveFileName(self, "選擇sha1檔案", "/", filter="txt files(*.txt)")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.sha1text.toPlainText())

    # 添加網路檔案
    def add(self, data: dict[str, any], value: bool = True) -> None:
        if value:
            data = {
                    'pc': data['pc'], 'name': data['name'], 'cid': data['cid'],
                    'ico': data['ico'], 'length': data['size'], 'sha1': data['sha1'],
                    'blockhash': None, 'dir': data['dir'] if 'dir' in data else None,
                    'state': None, 'stop': None
                }
        uuid = f'4{uuid1().hex}'
        qtext = Qtext(
            self.state, data, uuid, self.lock, self.queuelist, self.transmissionlist, self.allqtext,
            self.sha1text, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 添加網路資料夾
    def folder_add(self, data: dict[str, any], value: bool = True) -> None:
        if value:
            data = {'name': data["name"], 'cid': data['cid'], 'dir': data['dir'], 'ico': data['ico']}
        uuid = f'5{uuid1().hex}'
        qtext = QFolder(
            self.state, data, uuid, self.queuelist, self.transmissionlist,
            self.allqtext, self.getfolder, self.add, self.folder_add, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 添加本地檔案
    def path_add(self, data: dict[str, any], value: bool = True) -> None:
        if value:
            data = {
                'path': data['path'], 'name': data["name"], 'cid': '_',
                'ico': data['ico'], 'dir': data['dir'], 'state': None,
                'blockhash': None, 'sha1': None, 'length': getsize(data['path']), 'stop': None
            }
        uuid = f'8{uuid1().hex}'
        qtext = Qtext(
            self.state, data, uuid, self.lock, self.queuelist, self.transmissionlist,
            self.allqtext, self.sha1text, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 關閉 回調
    def close(self, qtext: QObject, data: dict[str, any]) -> None:
        self.allsize -= data['length']
        if self.allsize != 0:
            self.progressbar.setValue(int(self.transmissionsize / self.allsize * 100))

    # 完成 回調
    def complete(self, qtext: QObject, data: dict[str, any]) -> None:
        self.settransmissionsize(data['length'])

    # 更改大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        y = 90 if self.allqtext else 55
        height = int((self.height() - y) / 2)
        self.scrollarea.setGeometry(0, y, self.width(), height)
        self.scrollcontents.setGeometry(0, 0, self.width() - 2, self.scrollcontents.height())
        self.progresscontents.setGeometry(0, 55, self.width(), 35)
        self.buttons.setGeometry(self.width() - 290, 5, 256, 24)
        self.progressbar.setGeometry(88, 10, self.width() - 459, 14)

        self.sha1text.setGeometry(0, height + 55, self.width(), height)
        self.frame.setGeometry(0, 55, self.width(), 1)
        for qtext in self.allqtext:
            qtext.setGeometry(0, qtext.y(), self.width() - 2, 56)
