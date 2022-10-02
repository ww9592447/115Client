from module import pybyte, set_state, exists, getsize,\
    split, sleep, create_task, timedelta, datetime, popen,\
    get_ico, splitext, MQtext, uuid1, MQList


class QFolder(MQtext):
    def __init__(self, state, uuid, queuelist, islist, allqtext, parent=None):
        super().__init__(state, uuid, file=False, queuelist=queuelist, islist=islist,
                         allqtext=allqtext, parent=parent)

    # 開啟
    def open(self):
        if exists(self.path):
            popen(f'explorer.exe /select, {self.path}')

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


class QSha1(MQtext):
    def __init__(self, state, uuid, lock, queuelist, islist, allqtext, parent=None):
        super().__init__(state, uuid, file=False, lock=lock, queuelist=queuelist, islist=islist,
                         allqtext=allqtext, parent=parent)
        self.task = None

    async def set_state(self):
        self.progressText.setText('上傳請求中...')
        while 1:
            if self.state[self.uuid]['state']:
                if self.state[self.uuid]['state'] == '秒傳完成':
                    self.end.emit(self)
                else:
                    self.progressText.setText(self.state[self.uuid]['state'])
                    self.set_switch(False)
                    self.queuelist.remove(self)
                return

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


class Qupload(MQtext):
    def __init__(self, state, uuid, lock, queuelist, islist, allqtext, parent=None):
        super().__init__(state, uuid, lock=lock, queuelist=queuelist, islist=islist,
                         allqtext=allqtext, parent=parent)
        self.task = None
        self.path = state[uuid]['path']
        # 計算上傳速度
        self.sample_times, self.sample_values = [], []
        self.INTERVAL, self.samples = timedelta(milliseconds=100), timedelta(seconds=2)

    async def set_state(self):
        self.progressText.setText('上傳請求中...')
        while 1:
            if self.state[self.uuid]['stop'] and self.state[self.uuid]['state'] is None:
                self.get_rate(self.state[self.uuid]['size'])
            elif self.state[self.uuid]['stop'] is False and self.state[self.uuid]['state']:
                state = self.state[self.uuid]['state']
                if state in ['上傳完成', '秒傳完成', 'del']:
                    self.end.emit(self)
                elif state != 'pause':
                    self.progressText.setText(state)
                    self.set_switch(False)
                    self.islist.remove(self)
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
            self.set_restore.setEnabled(False)
            self.set_closes.setEnabled(False)
            with set_state(self.state, self.uuid) as state:
                state.update({'state': 'del'})
        if self not in self.islist:
            self.end.emit(self)
            return
        self.progressText.setText('等待關閉中中...')

    # 開啟
    def open(self):
        if exists(self.path):
            popen(f'explorer.exe /select, {self.path}')


class UploadList(MQList):
    def __init__(self, state, allpath, lock, wait, waitlock, config, endlist, refresh, add_folder, parent=None):
        super().__init__(state, allpath, lock, wait, waitlock, parent)
        # 最大上傳數
        self.upload_max = int(config['upload']['最大同時上傳數'])
        # 目錄刷新
        self.refresh = refresh
        # 下載完畢窗口
        self.endlist = endlist
        # 新建資料夾
        self.add_folder = add_folder
        # 添加資料夾任務
        self.folder_task = {}
        # 開始檢查循環
        create_task(self.set_stop())

    async def set_stop(self):
        while 1:
            if len(self.islist) < self.upload_max and self.queuelist:
                qtext = self.queuelist.pop(0)
                # 把qtext 轉成上傳中
                qtext.set_switch(True)
                # 添加到上傳列表
                self.islist.append(qtext)
                with self.lock:
                    with set_state(self.state, qtext.uuid) as state:
                        state.update({'state': None, 'stop': None})
                if self.state[qtext.uuid]['dir']:
                    create_task(self.folder_stop(qtext))
                else:
                    qtext.task = create_task(qtext.set_state())
                    with self.waitlock:
                        self.wait.append(qtext.uuid)
            await sleep(0.1)

    # 添加
    async def add(self, data=None, state=None):
        if value := data is not None:
            length = getsize(data['path'])
            _, name = split(data['path'])
            ico = get_ico(splitext(name)[1])
            uuid = f'6{uuid1().hex}'
            _state = {'length': length, 'size': 0, 'ico': ico, 'cid': data['cid'], 'second': None,
                      'range': {}, 'cb': None, 'name': name, 'path': data['path'], 'sha1': None,
                      'blockhash': None, 'etag': {}, 'upload_key': None, 'url': None, 'upload_id': None,
                      'state': None, 'stop': None, 'dir': data['dir']}

            with self.lock:
                self.state[uuid] = _state
        else:
            with self.lock:
                self.state.update(state)
            uuid = list(state.keys())[0]
        qtext = Qupload(
            self.state, uuid, self.lock, self.queuelist, self.islist,
            self.allqtext, parent=self.scrollcontents
        )
        self._addtext(qtext, value)

    # 添加
    async def sha1_add(self, data=None, state=None):
        if value := data is not None:
            _data = data['sha1'].split('|')
            length = _data[1]
            sha1 = _data[2]
            blockhash = _data[3]
            ico = get_ico(splitext(_data[0])[1])
            uuid = f'7{uuid1().hex}'
            _state = {'name': _data[0], 'ico': ico, 'dir': '\\'.join(_data[4:]), 'cid': data['cid'], 'length': length,
                      'sha1': sha1, 'blockhash': blockhash, 'state': None}
            with self.lock:
                self.state[uuid] = _state
        else:
            with self.lock:
                self.state.update(state)
            uuid = list(state.keys())[0]
        qtext = QSha1(
            self.state, uuid, self.lock, self.queuelist, self.islist,
            self.allqtext, parent=self.scrollcontents
        )
        self._addtext(qtext, value)

    # 上傳空白資料夾
    async def new_folder_add(self, data=None, state=None):
        if value := data is not None:
            uuid = f'9{uuid1().hex}'
            with self.lock:
                self.state[uuid] = {'cid': data['cid'], 'dir': data['dir'], 'name': data['name'], 'ico': '資料夾'}
        else:
            with self.lock:
                self.state.update(state)
            uuid = list(state.keys())[0]
        qtext = QFolder(
            self.state, uuid, self.queuelist, self.islist, self.allqtext, parent=self.scrollcontents
        )
        self._addtext(qtext, value)

    # 新增資料夾
    async def folder_add(self, cid, name):
        result = await self.add_folder(cid, name, state=False)
        # 查看新增資料夾是否失敗
        if result:
            self.allpath[cid]['refresh'] = True
            self.allpath[cid]['folder'][name] = str(result['cid'])
        del self.folder_task[cid]['name'][name]
        return result

    def task_callback(self, task, cid):
        self.folder_task[cid]['task'] = None

    # 獲取資料夾資料 或者 創建資料夾
    async def folder_stop(self, qtext):
        state = self.state[qtext.uuid]
        cid = state['cid']
        qtext.progressText.setText(f'查找資料夾中')
        for name in state['dir'].split('\\'):
            task = None
            if cid not in self.folder_task:
                self.folder_task[cid] = {'task': None, 'name': {}}
            while 1:
                if cid in self.allpath and name in self.allpath[cid]['folder']:
                    cid = self.allpath[cid]['folder'][name]
                    break
                elif cid in self.allpath and name not in self.folder_task[cid]['name']\
                        and self.allpath[cid]['folder_read']:
                    task = create_task(self.folder_add(cid, name))
                    task.set_name('創建資料夾失敗')
                    self.folder_task[cid]['name'][name] = task
                elif self.folder_task[cid]['task'] is None and name not in self.folder_task[cid]['name']:
                    index = self.allpath[cid]['_page'][0] if cid in self.allpath else 0
                    task = create_task(self.refresh(cid, index, state=False))
                    task.set_name('獲取資料夾資料失敗')
                    task.add_done_callback(lambda _task: self.task_callback(_task, cid))
                    if cid in self.folder_task:
                        self.folder_task[cid].update({'task': task})
                    else:
                        self.folder_task[cid] = {'task': task, 'name': {}}

                elif self.folder_task[cid]['task']:
                    task = self.folder_task[cid]['task']
                elif name in self.folder_task[cid]['name']:
                    task = self.folder_task[cid]['name'][name]
                if task:
                    _name = task.get_name()
                    if _name == '創建資料夾失敗':
                        qtext.progressText.setText(f'創建資料夾中')
                    result = await task
                    if result is False or result == '0':
                        text = '資料夾不存在' if result == '0' else _name
                        qtext.progressText.setText(text)
                        qtext.set_switch(False)
                        self.islist.remove(qtext)
                        return
                    task = None
        if qtext.uuid[0] == '9':
            self.end(qtext)
        elif qtext.uuid[0] == '!':
            with self.lock:
                with set_state(self.state, qtext.uuid) as state:
                    state.update({'cid': cid, 'dir': None})
            qtext.task = create_task(qtext.set_state())

        else:
            with self.lock:
                with set_state(self.state, qtext.uuid) as state:
                    state.update({'cid': cid, 'dir': None})
            qtext.task = create_task(qtext.set_state())
            with self.waitlock:
                self.wait.append(qtext.uuid)

    def end(self, qtext):
        state = self.state[qtext.uuid]
        if qtext.uuid[0] == '6':
            if state['state'] != 'del':
                self.endlist.add(qtext.path, qtext.name, state['ico'], pybyte(int(state['length'])),
                                 state['state'], cid=state['cid'])
                if state['cid'] in self.allpath:
                    self.allpath[state['cid']]['refresh'] = True
        elif qtext.uuid[0] == '7':
            if qtext.progressText.text() != '文件大小超出上傳限制':
                self.endlist.add('', qtext.name, state['ico'], pybyte(int(state['length'])), state['state'],
                                 cid=state['cid'])
                if state['cid'] in self.allpath:
                    self.allpath[state['cid']]['refresh'] = True
        with self.lock:
            del self.state[qtext.uuid]
        self._deltext(qtext)
