from module import pybyte, set_state, getsize,\
    split, sleep, create_task, timedelta, datetime,\
    get_ico, splitext, MQtext1, MQtext2, uuid1, MQList, getdata


class QFolder(MQtext2):
    def __init__(self, state, _state, uuid, queuelist, transmissionlist, search_add_folder, parent=None):
        super().__init__(state, _state, uuid, queuelist=queuelist, transmissionlist=transmissionlist, parent=parent)
        # 搜索資料夾 如果沒有則創建資料夾
        self.search_add_folder = search_add_folder

    async def stop(self):
        self.progressText.setText('查找資料夾中')
        state = self.state[self.uuid]
        async for result in self.search_add_folder(state['cid'], state['dir']):
            self.setdata(result)


class QSha1(MQtext2):
    def __init__(self, state, _state, uuid, lock, queuelist, transmissionlist, allqtext, wait, waitlock, parent=None):
        super().__init__(state, _state, uuid, lock=lock, queuelist=queuelist, transmissionlist=transmissionlist,
                         allqtext=allqtext, parent=parent)
        # 傳送列表
        self.wait = wait
        # 傳送列表鎖
        self.waitlock = waitlock

    async def set_state(self):
        self.progressText.setText('查找資料夾中')
        state = self.state[self.uuid]
        async for result in self.search_add_folder(state['cid'], state['dir']):
            if result['state'] == 'end':
                with self.lock:
                    with set_state(self.state, self.uuid) as state:
                        state.update({'cid': result['result'], 'dir': None})
            else:
                self.setdata(result)
        self.cancel = False
        with self.waitlock:
            self.wait.append(self.uuid)
        self.progressText.setText('上傳請求中...')
        while 1:
            if self.state[self.uuid]['state']:
                self.setdata(getdata(self.state[self.uuid]['state']))
                return
            await sleep(0.1)


class Qupload(MQtext1):
    def __init__(self, state, _state, uuid, lock, queuelist, transmissionlist, allqtext,
                 settransmissionsize, search_add_folder, wait, waitlock,  parent=None):
        super().__init__(state, _state, uuid, lock=lock, queuelist=queuelist, allqtext=allqtext,
                         transmissionlist=transmissionlist, parent=parent)
        # 傳送列表
        self.wait = wait
        # 傳送列表鎖
        self.waitlock = waitlock
        # 搜索資料夾 如果沒有則創建資料夾
        self.search_add_folder = search_add_folder
        # 設定所有下載總量
        self.settransmissionsize = settransmissionsize
        # 上傳檔案路徑
        self.path = _state['path']
        # 目前上傳量
        self.size = _state['size']
        # 計算上傳速度
        self.sample_times, self.sample_values = [], []
        self.INTERVAL, self.samples = timedelta(milliseconds=100), timedelta(seconds=2)

    async def stop(self):
        state = self.state[self.uuid]
        if state['dir']:
            self.progressText.setText('查找資料夾中')
            async for result in self.search_add_folder(state['cid'], state['dir']):
                if result['state'] == 'end':
                    with self.lock:
                        with set_state(self.state, self.uuid) as state:
                            state.update({'cid': result['result'], 'dir': None})
                else:
                    self.setdata(result)
        self.cancel = False
        with self.waitlock:
            self.wait.append(self.uuid)
        self.progressText.setText('上傳請求中...')
        while 1:
            state = self.state[self.uuid]
            if state['stop'] and state['state'] is None:
                self.get_rate(state['size'])
            elif not state['stop'] and state['state']:
                self.setdata(getdata(state['state']))
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
            except (Exception, ):
                pass


class UploadList(MQList):
    def __init__(self, state, lock, wait, waitlock, config, endlist, allpath, search_add_folder, text, parent=None):
        super().__init__(state, lock, wait, waitlock, text, parent)
        # 最大上傳數
        self.upload_max = int(config['upload']['最大同時上傳數'])
        # 所有目錄資料
        self.allpath = allpath
        # 下載完畢窗口
        self.endlist = endlist
        # 搜索資料夾 如果沒有則創建資料夾
        self.search_add_folder = search_add_folder
        # 添加資料夾任務
        self.folder_task = {}
        # 開始檢查循環
        create_task(self.set_stop())

    async def set_stop(self):
        while 1:
            if len(self.transmissionlist) < self.upload_max and self.queuelist:
                # 提取待下載列表第一個
                qtext = self.queuelist.pop(0)
                # 添加到下載列表
                self.transmissionlist.append(qtext)
                # 把qtext 轉成下載中
                qtext.set_switch(True)

                with self.lock:
                    with set_state(self.state, qtext.uuid) as state:
                        # 檢查是否是檔案
                        if qtext.uuid[0] in ['6', '7']:
                            state.update({'state': None, 'stop': None})
                qtext.task = create_task(qtext.stop())
            await sleep(0.1)

    # 添加上傳文件
    def add(self, data, value=True):
        if value:
            length = getsize(data['path'])
            _, name = split(data['path'])
            ico = get_ico(splitext(name)[1])
            data = {'length': length, 'size': 0, 'ico': ico, 'cid': data['cid'], 'second': None,
                    'range': {}, 'cb': None, 'name': name, 'path': data['path'], 'sha1': None,
                    'blockhash': None, 'etag': {}, 'upload_key': None, 'url': None, 'upload_id': None,
                    'state': None, 'bucket': None, 'stop': None, 'dir': data['dir'], 'result': None}
        uuid = f'6{uuid1().hex}'
        qtext = Qupload(
            self.state, data, uuid, self.lock, self.queuelist, self.transmissionlist, self.allqtext
            , self.settransmissionsize, self.search_add_folder, self.wait, self.waitlock, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # sha1添加
    def sha1_add(self, data, value=True):
        if value:
            _data = data['sha1'].split('|')
            length = _data[1]
            sha1 = _data[2]
            blockhash = _data[3]
            ico = get_ico(splitext(_data[0])[1])
            data = {'name': _data[0], 'ico': ico, 'dir': '\\'.join(_data[4:]), 'cid': data['cid'],
                    'length': int(length), 'sha1': sha1, 'blockhash': blockhash, 'state': None, 'result': None}
        uuid = f'7{uuid1().hex}'
        qtext = QSha1(
            self.state, data, uuid, self.lock, self.queuelist, self.transmissionlist,
            self.allqtext, self.wait, self.waitlock, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 新增傳空白資料夾
    def new_folder_add(self, data, value=True):
        if value:
            data = {'cid': data['cid'], 'dir': data['dir'], 'name': data['name'], 'ico': '資料夾'}
        uuid = f'9{uuid1().hex}'
        qtext = QFolder(
            self.state, data, uuid, self.queuelist, self.transmissionlist,
            self.search_add_folder, parent=self.scrollcontents
        )
        self._add(data, uuid, qtext, value)

    # 關閉 回調
    def close(self, qtext, state):
        if qtext.uuid[0] in ['6', '7']:
            self.allsize -= qtext.length
            if qtext.uuid[0] == '6':
                self.transmissionsize -= qtext.size
            if self.allsize != 0:
                self.progressbar.setValue(int(self.transmissionsize / self.allsize * 100))

    # 上傳完成 回調
    def complete(self, qtext, state):
        if 'result' in state and state['result'] == '秒傳完成':
            self.settransmissionsize(self.state[qtext.uuid]['length'])
        if qtext.uuid[0] == '6':
            self.endlist.add(qtext.path, qtext.name, state['ico'], pybyte(int(state['length'])),
                             state['result'], cid=state['cid'])
        elif qtext.uuid[0] == '7':
            if qtext.progressText.text() != '文件大小超出上傳限制':
                self.endlist.add('', qtext.name, state['ico'], pybyte(int(state['length'])), state['result'],
                                 cid=state['cid'])
        if state['cid'] in self.allpath:
            self.allpath[state['cid']]['refresh'] = True
