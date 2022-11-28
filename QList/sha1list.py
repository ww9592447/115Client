from pyperclip import copy
from module import create_task, sleep, uuid1, Qt, QTextEdit, Frame, getsize, \
    MyQLabel, MQList, MQtext2, QMessageBox, QFileDialog, getdata, set_state


class QFolder(MQtext2):
    def __init__(self, state, _state, uuid, queuelist, transmissionlist, allqtext,
                 getfolder, add, folder_add,  parent=None):
        super().__init__(state, _state, uuid, queuelist=queuelist, transmissionlist=transmissionlist,
                         allqtext=allqtext, parent=parent)
        # 獲取資料夾資料
        self.getfolder = getfolder
        # 新增檔案函數
        self.add = add
        # 新增資料夾函數
        self.folder_add = folder_add
        # 下載資料夾cid
        self.cid = _state['cid']
        # 保存路徑
        self.dir = _state['dir']

    async def stop(self):
        self.progressText.setText('獲取資料夾資料中...')
        if (result := await self.getfolder(self.cid))[0]:
            # 新增到下載列表
            for data in result[1].values():
                # 判斷是否是資料夾
                if data['category'] == '0':
                    data['dir'] = f"{self.dir}|{data['name']}"
                    self.folder_add(data=data)
                else:
                    data['dir'] = self.dir
                    self.add(data=data)
        else:
            self.setdata(getdata(result[1]))
        self.end.emit(self)

    def open(self):
        pass


class Qtext(MQtext2):
    def __init__(self, state, _state, uuid, queuelist, transmissionlist, allqtext, text, parent=None):
        super().__init__(state, _state, uuid, queuelist=queuelist, transmissionlist=transmissionlist,
                         allqtext=allqtext, parent=parent)
        self.sha1text = text
        # 禁止取消任務
        self.cancel = False

    async def stop(self):
        self.progressText.setText('獲取sha1鏈結中...')
        while 1:
            if not self.state[self.uuid]['stop']:
                state = self.state[self.uuid]
                if self.state[self.uuid]['blockhash']:
                    _sha1 = f"115://{self.name}|{state['length']}|{state['sha1']}|{state['blockhash']}"
                    if self.state[self.uuid]['dir']:
                        _sha1 += f"|{self.state[self.uuid]['dir']}"
                    self.sha1text.append(_sha1)
                    self.end.emit(self)
                else:
                    self.setdata(getdata(state['state']))
                return
            await sleep(0.1)


class Sha1List(MQList):
    def __init__(self, state, lock, wait, waitlock, getfolder, text, parent=None):
        super().__init__(state, lock, wait, waitlock, text, parent)
        # 獲取目錄資料
        self.getfolder = getfolder
        self.sha1text = QTextEdit(self)
        self.sha1text.setAcceptDrops(False)
        self.sha1text.setFocusPolicy(Qt.NoFocus)
        self.sha1text.setLineWrapMode(QTextEdit.NoWrap)
        self.sha1text.setFontPointSize(15)
        self.sha1text.setStyleSheet(
            'border-style:solid;border-top-width:1;border-left-width:1px;border-color: rgba(200, 200, 200, 125)'
        )

        self.copy = MyQLabel('複製全部', (10, 8, 111, 41), fontsize=16, clicked=self._copy, parent=self)
        self.save = MyQLabel('另存新檔', (130, 8, 111, 41), fontsize=16, clicked=self._save, parent=self)
        self.cls = MyQLabel('清空', (250, 8, 111, 41), fontsize=16, clicked=self.sha1text.clear, parent=self)

        # 中間分隔線
        self.frame = Frame(self)

        # 開始檢查循環
        create_task(self.set_stop())

    def _copy(self):
        copy(self.sha1text.toPlainText())
        QMessageBox.about(self, "複製", "複製完畢")

    def _save(self):
        if self.sha1text.toPlainText():
            path, _ = QFileDialog.getSaveFileName(self, "選擇sha1檔案", "/", filter="txt files(*.txt)")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.sha1text.toPlainText())

    async def set_stop(self):
        while 1:
            if self.queuelist and not self.transmissionlist:
                qtext = self.queuelist.pop(0)
                # 把qtext 轉成上傳中
                qtext.set_switch(True)
                # 添加到上傳列表
                self.transmissionlist.append(qtext)
                if qtext.uuid[0] in ['4', '8']:
                    with self.lock:
                        with set_state(self.state, qtext.uuid) as state:
                            # 資料 初始化
                            state.update({'state': None, 'stop': True})
                qtext.task = create_task(qtext.stop())
                with self.waitlock:
                    self.wait.append(qtext.uuid)
            await sleep(0.1)

    # 添加網路檔案
    def add(self, data, value=True):
        if value:
            data = {
                    'pc': data['pc'], 'name': data['name'], 'cid': data['cid'],
                    'ico': data['ico'], 'length': data['size'], 'sha1': data['sha1'],
                    'blockhash': None, 'dir': data['dir'] if 'dir' in data else None,
                    'state': None, 'stop': None
                }
        uuid = f'4{uuid1().hex}'
        qtext = Qtext(
            self.state, data, uuid, self.queuelist, self.transmissionlist, self.allqtext,
            self.sha1text, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 添加網路資料夾檔案
    def folder_add(self, data, value=True):
        if value:
            data = {'name': data["name"], 'cid': data['cid'], 'dir': data['dir'], 'ico': data['ico']}
        uuid = f'5{uuid1().hex}'
        qtext = QFolder(
            self.state, data, uuid, self.queuelist, self.transmissionlist,
            self.allqtext, self.getfolder, self.add, self.folder_add, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 添加本地檔案
    def path_add(self, data, value=True):
        if value:
            data = {
                'path': data['path'], 'name': data["name"], 'cid': '_',
                'ico': data['ico'], 'dir': data['dir'], 'state': False,
                'blockhash': None, 'sha1': None, 'length': getsize(data['path']), 'stop': None
            }
        uuid = f'8{uuid1().hex}'
        qtext = Qtext(
            self.state, data, uuid, self.queuelist, self.transmissionlist,
            self.allqtext, self.sha1text, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 關閉 回調
    def close(self, qtext, state):
        self.allsize -= state['length']
        if self.allsize != 0:
            self.progressbar.setValue(int(self.transmissionsize / self.allsize * 100))

    # 完成 回調
    def complete(self, qtext, state):
        self.settransmissionsize(state['length'])

    # 更改大小事件
    def resizeEvent(self, event):
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
