from pyperclip import copy
from module import create_task, sleep, backdrop, uuid1, Qt, QTextEdit, Frame, \
    QFrame, exists, MyQLabel, getsize, MQtext, ScrollArea, MQList, QMessageBox, QFileDialog



class QFolder(MQtext):
    def __init__(self, state, uuid, queuelist, islist, allqtext, parent=None):
        super().__init__(state, uuid, file=False, queuelist=queuelist, islist=islist,
                         allqtext=allqtext, parent=parent)
        _state = state[uuid]
        self.cid = _state['cid']
        self.dir = _state['dir']
        self.index = 0
        self.count = 0


class Qtext(MQtext):
    def __init__(self, state, uuid, queuelist, islist, allqtext, text, parent=None):
        super().__init__(state, uuid, file=False, queuelist=queuelist, islist=islist,
                         allqtext=allqtext, parent=parent)
        self.text = text

    async def set_state(self):
        self.progressText.setText('獲取sha1鏈結中...')
        while 1:
            if self.state[self.uuid]['blockhash']:
                blockhash = self.state[self.uuid]['blockhash']
                if blockhash is False:
                    self.progressText.setText('網路異常獲取失敗')
                    self.set_switch(False)
                    self.queue_list.remove(self)
                    return
                sha1 = self.state[self.uuid]['sha1']
                length = self.state[self.uuid]['length']                
                _sha1 = f"115://{self.name}|{length}|{sha1}|{blockhash}"
                if self.state[self.uuid]['dir']:
                    _sha1 += f"|{self.state[self.uuid]['dir']}"
                self.text.append(_sha1)
                self.end.emit(self)
                return
            await sleep(0.1)

    # 暫停
    async def pause(self):
        if self not in self.islist:
            self.set_switch(False)
            self.queuelist.remove(self)
            self.progressText.setText('暫停中...')

    # 關閉
    async def closes(self):
        if self not in self.islist:
            self.end.emit(self)
            return


class Sha1List(MQList):
    def __init__(self, state, allpath, lock, wait, waitlock, refresh, parent=None):
        super().__init__(state, allpath, lock, wait, waitlock, parent)
        # 目錄刷新
        self.refresh = refresh

        self.text = QTextEdit(self)
        self.text.setAcceptDrops(False)
        self.text.setFocusPolicy(Qt.NoFocus)
        self.text.setLineWrapMode(QTextEdit.NoWrap)
        self.text.setFontPointSize(15)
        self.text.setStyleSheet(
            'border-style:solid;border-top-width:1;border-left-width:1px;border-color: rgba(200, 200, 200, 125)'
        )

        self.copy = MyQLabel('複製全部', (10, 8, 111, 41), fontsize=16, clicked=self._copy, parent=self)
        self.save = MyQLabel('另存新檔', (130, 8, 111, 41), fontsize=16, clicked=self._save, parent=self)
        self.cls = MyQLabel('清空', (250, 8, 111, 41), fontsize=16, clicked=self.text.clear, parent=self)

        # 中間分隔線
        self.frame = Frame(self)

        # 開始檢查循環
        create_task(self.set_stop())

    def _copy(self):
        copy(self.text.toPlainText())
        QMessageBox.about(self, "複製", "複製完畢")

    def _save(self):
        if self.text.toPlainText():
            path, _ = QFileDialog.getSaveFileName(self, "選擇sha1檔案", "/", filter="txt files(*.txt)")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.text.toPlainText())

    async def set_stop(self):
        while 1:
            if self.queuelist and not self.islist:
                qtext = self.queuelist.pop(0)
                # 把qtext 轉成上傳中
                qtext.set_switch(True)
                # 添加到上傳列表
                self.islist.append(qtext)
                if qtext.uuid[0] in ['4', '8']:
                    with self.waitlock:
                        self.wait.append(qtext.uuid)
                    create_task(qtext.set_state())
                elif qtext.uuid[0] == '5':
                    create_task(self.folder_stop(qtext))
            await sleep(0.1)

    # 添加
    def add(self, data=None, state=None):
        if value := data is not None:
            with self.lock:
                uuid = f'4{uuid1().hex}'
                self.state[uuid] = {'pc': data['pc'],
                                    'name': data['name'],
                                    'cid': data['cid'],
                                    'ico': data['ico'],
                                    'length': data['size'],
                                    'sha1': data['sha1'],
                                    'blockhash': None,
                                    'dir': data['dir'] if 'dir' in data else None,
                                    }
        else:
            with self.lock:
                self.state.update(state)
            uuid = list(state.keys())[0]

        qtext = Qtext(
            self.state, uuid, self.queuelist, self.islist, self.allqtext,
            self.text, parent=self.scrollcontents
        )
        self._addtext(qtext, value)

    def path_add(self, data=None, state=None):
        if value := data is not None:
            with self.lock:
                uuid = f'8{uuid1().hex}'
                self.state[uuid] = {
                    'path': data['path'],
                    'name': data["name"],
                    'cid': '_',
                    'ico': data['ico'],
                    'dir': data['dir'],
                    'state': False,
                    'blockhash': None,
                    'sha1': None,
                    'length': None,
                }
        else:
            with self.lock:
                self.state.update(state)
            uuid = list(state.keys())[0]
        qtext = Qtext(
            self.state, uuid, self.queuelist, self.islist,
            self.allqtext, self.text, parent=self.scrollcontents
        )
        self._addtext(qtext, value)

    def folder_add(self, data=None, state=None):
        if value := data is not None:
            uuid = f'5{uuid1().hex}'
            with self.lock:
                self.state[uuid] = {'name': data["name"], 'cid': data['cid'], 'dir': data['dir'], 'ico': data['ico']}
        else:
            with self.lock:
                self.state.update(state)
            uuid = list(state.keys())[0]
        qtext = QFolder(
            self.state, uuid, self.queuelist, self.islist,
            self.allqtext, parent=self.scrollcontents
        )
        self._addtext(qtext, value)

    async def folder_stop(self, qtext):
        qtext.progressText.setText('獲取資料夾資料中...')
        cid = qtext.cid
        while (cid in self.allpath and qtext.count < self.allpath[cid]['count']) or cid not in self.allpath:
            result = await self.refresh(qtext.cid, qtext.index, state=False)
            if result is False or result == '0':
                text = '資料夾不存在' if result == '0' else '獲取資料夾資料失敗'
                # 顯示網路錯誤
                qtext.progressText.setText(text)
                # qtext 轉成暫停
                qtext.set_switch(False)
                # 刪除正在下載列表
                self.islist.remove(qtext)
                break
            else:
                # 新增到下載列表
                for data in self.allpath[qtext.cid][qtext.index]['data']:
                    # 判斷是否是資料夾
                    if data['category'] != '0':
                        data['dir'] = qtext.dir
                        self.add(data=data)
                    else:
                        data['dir'] = f"{qtext.dir}|{data['name']}"
                        self.folder_add(data=data)
                qtext.count += self.allpath[qtext.cid][qtext.index]['read']
                qtext.index += 1
        self.end(qtext)

    def end(self, qtext):
        with self.lock:
            del self.state[qtext.uuid]
        self._deltext(qtext)

    # 更改大小事件
    def resizeEvent(self, e):
        height = int((self.height() - 55) / 2)
        self.scrollarea.setGeometry(0, 55, self.width(), height)
        self.scrollcontents.setGeometry(0, 0, self.width() - 2, self.scrollcontents.height())
        self.text.setGeometry(0, height + 55, self.width(), height)
        self.frame.setGeometry(0, 55, self.width(), 1)
        for qtext in self.allqtext:
            qtext.setGeometry(0, qtext.y(), self.width() - 2, 56)


# if __name__ == '__main__':
#     import sys
#     from PyQt5.Qt import QApplication
#     app = QApplication(sys.argv)
#     w = GetSha1()
#     w.show()
#     sys.exit(app.exec_())
