from module import datetime, uuid1, exists, create_task, sleep, pybyte, splitext,\
    timedelta, remove, popen, set_state, MQList, MQtext, getpath


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


class Qtext(MQtext):
    def __init__(self, state, uuid, lock, queuelist, islist, allqtext, parent=None):
        super().__init__(state, uuid, lock=lock, queuelist=queuelist, islist=islist,
                         allqtext=allqtext, parent=parent)
        self.task = None
        self.path = state[uuid]['path']
        # 計算下載速度
        self.sample_times, self.sample_values = [], []
        self.INTERVAL, self.samples = timedelta(milliseconds=100), timedelta(seconds=2)

    async def set_state(self):
        self.progressText.setText('下載請求中...')
        while 1:
            if self.state[self.uuid]['stop'] and self.state[self.uuid]['state'] is None:
                self.get_rate(self.state[self.uuid]['size'])
            elif self.state[self.uuid]['stop'] is False and self.state[self.uuid]['state']:
                state = self.state[self.uuid]['state']
                if state == 'end' or state == 'del':
                    self.end.emit(self)
                elif state == 'error':
                    self.progressText.setText('網路異常 下載失敗')
                    self.set_switch(False)
                    index = self.islist.index(self)
                    self.islist.pop(index)
                return
            await sleep(0.1)

    # 獲取進度速率
    def get_rate(self, size):
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
                self.progressBar.setValue(int(size / self.length * 100))
                self.file_size.setText(f'{pybyte(size)}/{pybyte(self.length)}')
                self.progressText.setText(pybyte(speed, s=True))
            except:
                pass

    # 暫停
    async def pause(self):
        self.set_switch(False)
        with self.lock:
            with set_state(self.state, self.uuid) as state:
                state.update({'state': 'pause'})
        if self in self.islist:
            self.progressText.setText('等待暫停中...')
            self.set_restore.setEnabled(False)
            self.set_closes.setEnabled(False)
            await self.task
            self.set_closes.setEnabled(True)
            self.set_restore.setEnabled(True)
            self.islist.remove(self)
        else:
            self.queuelist.remove(self)
        self.progressText.setText('暫停中...')

    # 關閉
    async def closes(self):
        with self.lock:
            with set_state(self.state, self.uuid) as state:
                state.update({'state': 'del'})
        if self not in self.islist:
            self.set_restore.setEnabled(False)
            self.set_closes.setEnabled(False)
            self.end.emit(self)
            return
        self.progressText.setText('等待關閉中中...')

    # 開啟
    def open(self):
        if exists(self.path):
            popen(f'explorer.exe /select, {self.path}')


class DownloadList(MQList):
    def __init__(self, state, allpath, lock, wait, waitlock, config, endlist, refresh, parent=None):
        super().__init__(state, allpath, lock, wait, waitlock, parent)
        # 下載目錄
        self.download_path = getpath(config['Download']['下載路徑'])
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
                if qtext.uuid[0] == '1':
                    create_task(self.folder_stop(qtext))
                else:
                    with self.lock:
                        with set_state(self.state, qtext.uuid) as state:
                            state.update({'state': None, 'stop': None})
                        qtext.task = create_task(qtext.set_state())
                    with self.waitlock:
                        self.wait.append(qtext.uuid)
            await sleep(0.1)

    async def folder_stop(self, qtext):
        qtext.progressText.setText('獲取資料夾資料中...')
        cid = qtext.cid
        if cid in self.allpath and self.allpath[cid]['refresh']:
            del self.allpath[cid]
        while (cid in self.allpath and qtext.count < self.allpath[cid]['count']) or cid not in self.allpath:
            result = True
            if cid in self.allpath and qtext.count not in self.allpath[cid]:
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

    # 獲取檔案是否存在並返回可添加後輟名
    def get_index(self, path, name, ico, index):
        if exists(f'{path}\\{name}({index}){ico}'):
            return self.get_index(path, name, ico, index + 1)
        else:
            return f'{name}({index}){ico}', f'{path}\\{name}({index}){ico}'

    # 添加
    def add(self, data=None, state=None):
        if value := data is not None:
            path = data["path"] if 'path' in data else self.download_path
            if exists(f'{path}\\{data["name"]}'):
                name, ico = splitext(data['name'])
                name, path = self.get_index(path, name, ico, 0)
            else:
                name = data["name"]
                path = f'{path}\\{data["name"]}'
            uuid = f'0{uuid1().hex}'
            if data['sha1'] in self.sha1_list:
                return
            else:
                self.sha1_list[data['sha1']] = path
            _state = {'pc': data['pc'], 'name': name, 'ico': data['ico'], 'length': data['size'],
                      'sha1': data['sha1'], 'size': 0, 'url': None, 'range': {},
                      'path': path, 'state': None, 'stop': None}
            with self.lock:
                self.state[uuid] = _state
        else:
            with self.lock:
                self.state.update(state)
            uuid = list(state.keys())[0]
            self.sha1_list[state[uuid]['sha1']] = state[uuid]['path']
        qtext = Qtext(
            self.state, uuid, self.lock, self.queuelist, self.islist,
            self.allqtext, parent=self.scrollcontents
        )
        self._addtext(qtext, value)

    # 添加資料夾
    def folder_add(self, data=None, state=None):
        if value := data is not None:
            path = f'{data["path"]}\\{data["name"]}' if 'path' in data else f'{self.download_path}\\{data["name"]}'
            uuid = f'1{uuid1().hex}'
            with self.lock:
                self.state[uuid] = {'path': path, 'name': data["name"], 'cid': data['cid'], 'ico': '資料夾'}
        else:
            with self.lock:
                self.state.update(state)
            uuid = list(state.keys())[0]

        qtext = QFolder(
            self.state, uuid, self.queuelist, self.islist,
            self.allqtext, parent=self.scrollcontents
        )
        self._addtext(qtext, value)

    # 關閉
    def end(self, qtext):
        if qtext.uuid[0] == '0':
            state = self.state[qtext.uuid]
            del self.sha1_list[state['sha1']]
            print(state['state'], exists(qtext.path))
            if state['state'] == 'del':
                if exists(qtext.path):
                    remove(qtext.path)
            else:
                self.endlist.add(qtext.path, qtext.name, state['ico'], pybyte(state['length']), '下載完成')
        with self.lock:
            del self.state[qtext.uuid]
        self._deltext(qtext)
