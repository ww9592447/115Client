from module import set_state, uuid1, exists, create_task, sleep, pybyte,\
    srequests, popen, MQList, MQtext, getpath


class Qtext(MQtext):
    def __init__(self, state, uuid, lock, queuelist, islist, allqtext, rpc_url, parent=None):
        super().__init__(state, uuid, lock=lock, queuelist=queuelist, islist=islist,
                         allqtext=allqtext, parent=parent)
        # aria2 url
        self.rpc_url = rpc_url
        # aria2 gid
        self.gid = None
        # set_state任務
        self.task = None

    async def set_state(self):
        self.progressText.setText('下載請求中...')
        while 1:
            if self.state[self.uuid]['gid']:
                self.gid = self.state[self.uuid]['gid']
                break
            elif self.gid:
                break
            elif self.state[self.uuid]['state']:
                self.set_switch(False)
                self.progressText.setText(self.state[self.uuid]['state'])
                self.islist.remove(self)
                return
            else:
                await sleep(0.1)
                continue
        while 1:
            result = await self.aria2_rpc(self.gid, 'aria2.tellStatus')
            if result['status'] == 'complete':
                return self.end.emit(self)
            elif result['status'] in ['paused', 'removed']:
                return
            elif result:
                if self.progressText.text not in ['等待暫停中...', '等待關閉中中...']:
                    self.file_size.setText(f'{pybyte(int(result["completedLength"]))}/{pybyte(self.length)}')
                    self.progressText.setText(pybyte(int(result["downloadSpeed"]), s=True))
                    self.progressBar.setValue(int(int(result["completedLength"]) / self.length * 100))
            elif result is False:
                self.set_switch(False)
                self.progressText.setText('aria2_rpc連接失敗')
                self.islist.remove(self)
                return
            await sleep(0.1)

    # 暫停
    async def pause(self):
        if self.progressText.text() != '下載請求中...':
            self.set_switch(False)
            if self in self.islist:
                self.progressText.setText('等待暫停中...')
                self.set_restore.setEnabled(False)
                self.set_closes.setEnabled(False)
                await create_task(self.aria2_rpc(self.gid, 'aria2.pause'))
                self.set_restore.setEnabled(True)
                self.set_closes.setEnabled(True)
                self.islist.remove(self)
            else:
                self.queuelist.remove(self)
            self.progressText.setText('暫停中...')

    # 關閉
    async def closes(self):
        if self.progressText.text() != '下載請求中...':
            self.set_switch(False)
            if self in self.islist:
                self.progressText.setText('等待暫停中...')
                self.set_restore.setEnabled(False)
                self.set_closes.setEnabled(False)
                await create_task(self.aria2_rpc(self.gid, 'aria2.remove'))
                self.set_restore.setEnabled(True)
                self.set_closes.setEnabled(True)
                self.islist.remove(self)
            else:
                self.queuelist.remove(self)
            self.end.emit(self)

    async def aria2_rpc(self, gid, aria2):
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


class QFolder(MQtext):
    def __init__(self, state, uuid, queuelist, islist, allqtext, parent=None):
        super().__init__(state, uuid, file=False, queuelist=queuelist, islist=islist,
                         allqtext=allqtext, parent=parent)
        self.path = state[uuid]['path']
        self.cid = state[uuid]['cid']
        self.index = 0
        self.count = 0

    # 開啟
    def open(self):
        if exists(self.path):
            popen(f'explorer.exe /select, {self.path}')


class Aria2List(MQList):
    def __init__(self, state, allpath, lock, wait, waitlock, config, endlist, refresh, parent=None):
        super().__init__(state, allpath, lock, wait, waitlock, parent)
        # 是否檢查sha1
        self.download_sha1 = config['aria2-rpc'].getboolean('aria2_sha1')
        # rpc_url
        self.rpc_url = config['aria2-rpc']['rpc_url']
        # 最大下載數
        self.download_max = int(config['Download']['最大同時下載數'])
        # 正在下載 sha1 列表
        self.sha1_list = {}
        # 目錄刷新
        self.refresh = refresh
        # 下載完畢窗口
        self.endlist = endlist

        # 開始檢查循環
        create_task(self.set_stop())

    async def set_stop(self):
        while 1:
            if len(self.islist) < self.download_max and self.queuelist:
                # 提取待下載列表第一個
                qtext = self.queuelist.pop(0)
                # 把qtext 轉成下載中
                qtext.set_switch(True)
                # 添加到下載列表
                self.islist.append(qtext)
                # 檢查是否是資料夾
                if qtext.uuid[0] == '3':
                    create_task(self.folder_stop(qtext))
                else:
                    with self.lock:
                        if qtext.gid:
                            with set_state(self.state, qtext.uuid) as state:
                                state.update({'state': None})
                            await create_task(qtext.aria2_rpc(qtext.gid, 'aria2.unpause'))
                        else:
                            with self.waitlock:
                                self.wait.append(qtext.uuid)
                        qtext.task = create_task(qtext.set_state())

            await sleep(0.1)

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
                    data['path'] = qtext.path
                    # 判斷是否是資料夾
                    if data['category'] != '0':
                        self.add(data=data)
                    else:
                        self.folder_add(data=data)
                qtext.count += self.allpath[qtext.cid][qtext.index]['read']
                qtext.index += 1
        self.end(qtext)

    # 添加
    def add(self, data=None, state=None):
        if value := data is not None:
            path = getpath(data["path"])
            uuid = f'2{uuid1().hex}'
            _state = {'length': data['size'], 'ico': data['ico'], 'name': data['name'],
                      'pc': data['pc'], 'size': 0, 'path': path, 'gid': None, 'state': None,
                      'sha1': data['sha1'] if self.download_sha1 else None}
            with self.lock:
                self.state[uuid] = _state
        else:
            with self.lock:
                self.state.update(state)
            uuid = list(state.keys())[0]
            self.sha1_list[state[uuid]['sha1']] = state[uuid]['path']
        qtext = Qtext(
            self.state, uuid, self.lock, self.queuelist, self.islist,
            self.allqtext, self.rpc_url, parent=self.scrollcontents
        )
        self._addtext(qtext, value)

    def folder_add(self, data=None, state=None):
        if value := data is not None:
            path = f'{getpath(data["path"])}\\{data["name"]}'
            uuid = f'3{uuid1().hex}'
            with self.lock:
                self.state[uuid] = {'path': path, 'name': data["name"], 'cid': data['cid'], 'ico': '資料夾'}
        else:
            with self.lock:
                self.state.update(state)
            uuid = list(state.keys())[0]
        qtext = QFolder(
            self.state, uuid, self.queuelist, self.islist, self.allqtext, parent=self.scrollcontents
        )
        self._addtext(qtext, value)

    # 關閉
    def end(self, qtext):
        if qtext.uuid[0] == '0':
            state = self.state[qtext.uuid]
            del self.sha1_list[state['sha1']]
            self.endlist.add(qtext.path, qtext.name, state['ico'], pybyte(state['length']), '下載完成')

        with self.lock:
            del self.state[qtext.uuid]
        self._deltext(qtext)