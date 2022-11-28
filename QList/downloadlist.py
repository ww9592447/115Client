from module import datetime, uuid1, exists, create_task, sleep, pybyte, splitext,\
    timedelta, remove, set_state, MQList, MQtext1, MQtext2, getpath, getdata


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


class Qtext(MQtext1):
    def __init__(self, state, _state, uuid, lock, queuelist, transmissionlist,
                 allqtext, settransmissionsize, parent=None):
        super().__init__(state, _state, uuid, lock=lock, queuelist=queuelist, transmissionlist=transmissionlist,
                         allqtext=allqtext, parent=parent)

        # 下載路徑
        self.path = _state['path']
        # 目前下載量
        self.size = _state['size']
        # 設定所有下載總量
        self.settransmissionsize = settransmissionsize
        # 禁止取消任務
        self.cancel = False
        # 計算下載速度
        self.sample_times, self.sample_values = [], []
        self.INTERVAL, self.samples = timedelta(milliseconds=100), timedelta(seconds=2)

    async def stop(self):
        self.progressText.setText('下載請求中...')
        while 1:
            if self.state[self.uuid]['stop']:
                if self.state[self.uuid]['state'] is None and self.size != self.state[self.uuid]['size']:
                    self.get_rate(self.state[self.uuid]['size'])
                elif self.progressText.text() != '檢測sha1中...' and self.state[self.uuid]['state'] == '檢測中':
                    self.progressText.setText('檢測sha1中...')
            elif not self.state[self.uuid]['stop'] and self.state[self.uuid]['state']:
                self.size = self.state[self.uuid]['size']
                self.setdata(getdata(self.state[self.uuid]['state']))
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
    def __init__(self, state, lock, wait, waitlock, config, endlist, getfolder, text, parent=None):
        super().__init__(state, lock, wait, waitlock, text, parent)
        # 下載目錄
        self.download_path = getpath(config['Download']['下載路徑'])
        # 最大下載數
        self.download_max = int(config['Download']['最大同時下載數'])
        # 正在傳輸 sha1 列表
        self.sha1list = []
        # 獲取目錄資料
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
                with self.lock:
                    with set_state(self.state, qtext.uuid) as state:
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
    def get_index(self, path, name, ico, index):
        if exists(f'{path}\\{name}({index}){ico}'):
            return self.get_index(path, name, ico, index + 1)
        else:
            return f'{name}({index}){ico}', f'{path}\\{name}({index}){ico}'

    # 添加
    def add(self, data, value=True):
        if data['sha1'] in self.sha1list:
            return
        else:
            self.sha1list.append(data['sha1'])
        if value:
            path = data["path"] if 'path' in data else self.download_path
            if exists(f'{path}\\{data["name"]}'):
                name, ico = splitext(data['name'])
                name, path = self.get_index(path, name, ico, 0)
            else:
                name = data["name"]
                path = f'{path}\\{data["name"]}'
            data = {
                'pc': data['pc'], 'name': name, 'ico': data['ico'], 'length': data['size'],
                'sha1': data['sha1'], 'size': 0, 'url': None, 'range': {},
                'path': path, 'state': None, 'stop': None
            }
        uuid = f'0{uuid1().hex}'
        qtext = Qtext(
            self.state, data, uuid, self.lock, self.queuelist, self.transmissionlist,
            self.allqtext, self.settransmissionsize, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 添加資料夾
    def folder_add(self, data, value=True):
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
    def close(self, qtext, state):
        if exists(qtext.path):
            remove(qtext.path)
        self.settransmissionsize(-qtext.size)
        self.sha1list.remove(state['sha1'])

    # 下載完畢回調
    def complete(self, qtext, state):
        self.sha1list.remove(state['sha1'])
        self.endlist.add(qtext.path, qtext.name, state['ico'], pybyte(state['length']), '下載完成')
