from module import set_state, uuid1, create_task, sleep, pybyte,\
    srequests, MQList, MQtext1,  MQtext2, getpath, getdata


class Qtext(MQtext1):
    def __init__(self, state, _state, uuid, lock, queuelist, transmissionlist, allqtext, rpc_url, settransmissionsize, parent=None):
        super().__init__(state, _state, uuid, lock=lock, queuelist=queuelist, transmissionlist=transmissionlist,
                         allqtext=allqtext, parent=parent)
        # aria2 url
        self.rpc_url = rpc_url
        # aria2 gid
        self.gid = None
        # 設定所有下載總量
        self.settransmissionsize = settransmissionsize
        # 目前傳輸大小
        self.size = 0
        # set_state任務
        self.task = None
        # 禁止取消任務
        self.cancel = False

    async def stop(self):
        self.progressText.setText('下載請求中...')
        while not self.gid:
            if self.state[self.uuid]['gid']:
                self.gid = self.state[self.uuid]['gid']
                break
            elif self.state[self.uuid]['state']:
                self.setdata(getdata(self.state[self.uuid]['state']))
                return
            await sleep(0.1)

        while 1:
            result = await self.aria2_rpc(self.gid, 'aria2.tellStatus')
            if result['status'] == 'complete':
                self.end.emit(self)
                return
            elif result['status'] in ['removed', 'paused']:
                return
            elif self.state[self.uuid]['state'] == 'pause':
                await self.aria2_rpc(self.gid, 'aria2.pause')
            elif self.state[self.uuid]['state'] == 'close':
                await self.aria2_rpc(self.gid, 'aria2.remove')
            elif result and self.progressText.text not in ['等待暫停中...', '等待關閉中中...']:
                self.settransmissionsize(int(result["completedLength"]) - self.size)
                self.size = int(result["completedLength"])
                self.file_size.setText(f'{pybyte(int(result["completedLength"]))}/{pybyte(self.length)}')
                self.progressText.setText(pybyte(int(result["downloadSpeed"]), s=True))
                if self.progressBar.value() != (_size := int(int(result["completedLength"]) / self.length * 100)):
                    self.progressBar.setValue(_size)
                    self.progressBar.update()
            elif result is False:
                self.setdata(getdata('aria2_rpc連接失敗'))
                return
            await sleep(0.1)

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


class QFolder(MQtext2):
    def __init__(self, state, _state, uuid, queuelist, transmissionlist, allqtext,
                 getfolder, add, folder_add, parent):
        super().__init__(state, _state, uuid, queuelist=queuelist, transmissionlist=transmissionlist,
                         allqtext=allqtext, parent=parent)
        # 獲取資料夾資料
        self.getfolder = getfolder
        # 新增檔案函數
        self.add = add
        # 新增資料夾函數
        self.folder_add = folder_add
        # 下載路徑
        self.path = _state['path']
        # 下載資料夾cid
        self.cid = _state['cid']

    async def stop(self):
        self.progressText.setText('獲取資料夾資料中...')
        if (result := await self.getfolder(self.cid))[0]:
            # 新增到下載列表
            for data in result[1].values():
                data['path'] = self.path
                # 判斷是否是資料夾
                if data['category'] == '0':
                    self.folder_add(data=data)
                else:
                    self.add(data=data)
        else:
            self.setdata(getdata(result[1]))
        self.end.emit(self)


class Aria2List(MQList):
    def __init__(self, state, lock, wait, waitlock, config, endlist, getfolder, text, parent=None):
        super().__init__(state, lock, wait, waitlock, text, parent)
        # rpc_url
        self.rpc_url = config['aria2-rpc']['rpc_url']
        # 最大下載數
        self.download_max = int(config['Download']['最大同時下載數'])
        # 正在下載 sha1 列表
        self.sha1list = []
        # 獲取資料夾資料
        self.getfolder = getfolder
        # 下載完畢窗口
        self.endlist = endlist

        # 開始檢查循環
        create_task(self.set_stop())

    async def set_stop(self):
        while 1:
            if len(self.transmissionlist) < self.download_max and self.queuelist:
                # 提取待下載列表第一個
                qtext = self.queuelist.pop(0)
                # 添加到下載列表
                self.transmissionlist.append(qtext)
                # 把qtext 轉成下載中
                qtext.set_switch(True)
                if qtext.uuid[0] == '2':
                    if qtext.gid:
                        with self.lock:
                            with set_state(self.state, qtext.uuid) as state:
                                state.update({'state': None})
                        await create_task(qtext.aria2_rpc(qtext.gid, 'aria2.unpause'))
                    else:
                        with self.waitlock:
                            self.wait.append(qtext.uuid)
                qtext.task = create_task(qtext.stop())
            await sleep(0.1)

    # 添加
    def add(self, data, value=True):
        if data['sha1'] in self.sha1list:
            return
        else:
            self.sha1list.append(data['sha1'])
        if value:
            path = getpath(data["path"])
            
            data = {'length': data['size'], 'ico': data['ico'], 'name': data['name'],
                    'pc': data['pc'], 'size': 0, 'path': path, 'gid': None, 'state': None,
                    'sha1': data['sha1']}
        uuid = f'2{uuid1().hex}'
        qtext = Qtext(
            self.state, data, uuid, self.lock, self.queuelist, self.transmissionlist,
            self.allqtext, self.rpc_url, self.settransmissionsize, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    def folder_add(self, data, value=True):
        if value:
            path = f'{getpath(data["path"])}\\{data["name"]}'
            data = {'path': path, 'name': data["name"], 'cid': data['cid'], 'ico': '資料夾'}
        uuid = f'3{uuid1().hex}'
        qtext = QFolder(
            self.state, data, uuid, self.queuelist, self.transmissionlist,
            self.allqtext, self.getfolder, self.add, self.folder_add, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 關閉回調
    def close(self, qtext, state):
        self.settransmissionsize(-qtext.size)
        self.sha1list.remove(state['sha1'])

    # 下載完畢回調
    def complete(self, qtext, state):
        self.sha1list.remove(state['sha1'])
        self.endlist.add(qtext.path, qtext.name, state['ico'], pybyte(state['length']), '下載完成')