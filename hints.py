from module import picture, QLabel, Window, QFont, QFrame, sleep, QLineEdit, \
    TextQLabel, QTextEdit, MyIco, MyQLabel, ListDirectory, time, create_task, get_ico, \
    splitext, math, QFileDialog, basename, QListView, QTreeView, QAbstractItemView, QDialogButtonBox
from MyQlist.package import gif
import winsound
import re


def error():
    def decorator(func):
        async def wrap(self=None, *args, state=True, **kwargs):
            while (result := await func(self, *args, **kwargs)) is False:
                if not state or await myerror('網路錯誤', '請問是否重新嘗試') is False:
                    break
            return result
        return wrap
    return decorator


class TitleLabel_1(QFrame):
    # 標題高度  關閉按鈕離邊緣多遠 關閉按鈕高度
    def __init__(self, parent=None):
        super().__init__(parent)
        # 標題設定
        self.label = QLabel(self)
        self.label.setFont(QFont('PMingLiU', 10))
        self.label.move(18, 9)
        self.closure = MyIco('黑色關閉', '藍色關閉', coordinate=(420, 20, 12, 12), state=True,
                             click=self.parent().parent().close, parent=self)

    def resizeEvent(self, event):
        self.closure.move(self.width() - 32, 10)


class TitleLabel_2(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = None
        # self.label.setFont(QFont("細明體", 14))
        # self.label.setGeometry(30, 25, 120, 30)
        # self.label.setText('添加離線鏈結')
        # self.label.show()

    def setdata(self, text, geometry):
        self.label = TextQLabel(text, fontsize=14, geometry=geometry, parent=self)
        self.label.show()


class Error(Window):
    def __init__(self, title, name):
        Window.__init__(self, TitleLabel_1, 30, tracking=False)
        self.titlelabel.label.setText(title)
        # 結果
        self.result = None
        # 灰色背景
        self.frame = QFrame(self.content_widget)
        self.frame.setStyleSheet('QFrame{background-color:rgb(240, 240, 240); border-bottom-style:solid;'
                                 ' border-top-width:1px; border-top-color: rgba(200, 200, 200, 175)}')

        # 警告圖片
        label = QLabel(self.content_widget)
        label.setPixmap(picture('警告'))
        label.move(20, 10)

        TextQLabel(name, fontsize=15, move=(60, 15), parent=self.content_widget)
        self.resize(260, 145)

        MyQLabel('是', (27, 57, 75, 27), qss=2, clicked=lambda:self.end(True), fontsize=16, parent=self.content_widget)
        MyQLabel('否', (132, 57, 75, 27), qss=2, clicked=lambda:self.end(False), fontsize=16, parent=self.content_widget)

    def end(self, result):
        self.result = result
        self.close()

    def resizeEvent(self, event):
        Window.resizeEvent(self, event)
        self.frame.setGeometry(0, self.content_widget.height() - 40, self.content_widget.width(), 40)

    def closeEvent(self, event):
        if self.result is None:
            self.result = False
        event.accept()


class Enter(Window):
    def __init__(self, title, name):
        Window.__init__(self, TitleLabel_1, 30, tracking=False)
        self.titlelabel.label.setText(title)
        # 結果
        self.result = None
        # 灰色背景
        self.content_widget.setStyleSheet('background-color:rgb(240, 240, 240)')

        TextQLabel(name, fontsize=11, move=(11, 10), parent=self.content_widget)

        self.text = QLineEdit(self.content_widget)
        self.text.move(11, 29)
        self.text.setStyleSheet('background-color: rgb(255, 255, 255);')
        self.text.resize(178, 20)

        MyQLabel(
            '是', (27, 57, 75, 27), qss=2, clicked=lambda: self.end(self.text.text()),
            fontsize=16, parent=self.content_widget
        )
        MyQLabel(
            '否', (110, 57, 75, 27), qss=2, clicked=lambda: self.end(False), fontsize=16,
            parent=self.content_widget
         )
        self.resize(228, 146)

    def end(self, result):
        self.result = result
        self.close()

    def closeEvent(self, event):
        if self.result is None:
            self.result = False
        event.accept()


async def myerror(title, name):
    _error = Error(title, name)
    _error.show()
    winsound.PlaySound("SystemQuestion", winsound.SND_ASYNC)
    while 1:
        if _error.result is not None:
            return _error.result
        await sleep(0.1)


async def myenter(title, name):
    _enter = Enter(title, name)
    _enter.show()
    while 1:
        if _enter.result is not None:
            return _enter.result
        await sleep(0.1)


# 離線窗口
async def offline(directory):
    class Offline(Window):
        def __init__(self):
            super().__init__(TitleLabel_2, 75, tracking=False)
            self.titlelabel.setdata('添加離線鏈結', (30, 25, 120, 30))
            self.resize(746, 346)
            self.setStyleSheet('#shadow_widget{background-color:rgb(255,255,255);border-radius:15px}')
            self.cid = ''
            self.text = QTextEdit(self.shadow_widget)
            self.text.setGeometry(30, 75, 660, 175)

            self.savetext = TextQLabel(f'保存到：云下载', fontsize=12, move=(30, 275), parent=self.shadow_widget)

            self.button = MyQLabel(
                '更改目錄', (self.savetext.x() + self.savetext.width() + 10, 269, 80, 30),
                clicked=lambda: create_task(self.folder()), fontsize=12, parent=self.shadow_widget
            )

            MyIco('黑色關閉', '藍色關閉', coordinate=(670, 35, 12, 12), state=True,
                  click=self.close, parent=self.shadow_widget)

            # 開始離線按鈕
            MyQLabel(
                '開始離線下載', (540, 190, 150, 40), clicked=lambda: create_task(self.end()),
                qss=1, fontsize=16, parent=self.content_widget
            )

            # 設定等待灰色窗口
            self.shadow_widget_ = QFrame(self)
            # 設定灰色窗口名稱
            self.shadow_widget_.setObjectName('shadow_widget_')
            # 根據灰色窗口名稱 設定背景顏色
            self.shadow_widget_.setStyleSheet(
                '#shadow_widget_{background-color:rgba(242, 244, 248, 100);border-radius:15px}'
            )
            # 移動到可以完全顯示陰影
            self.shadow_widget_.move(self.padding, self.padding)
            # 灰色窗口隱藏
            self.shadow_widget_.hide()

            # 設定等待GIF
            self.load = gif(self.shadow_widget_, '加載_')
            # 設置 GIF 大小
            self.load.resize(32, 32)

        async def folder(self):
            if data := await folderlist('選擇要保存的資料夾', '保存到這裡', directory):
                self.cid, name = data
                self.savetext.setText(f'保存到：{name}')
                self.savetext.adjustSize()
                self.button.move(self.savetext.x() + self.savetext.width() + 10, 269)

        async def end(self):
            self.shadow_widget_.show()
            self.load.show()
            result = self.text.toPlainText()
            if result.find('\n') != -1:
                _result = []
                for text in result.split('\n'):
                    if text:
                        _result.append(text)
                result = _result
            if result:
                while await directory.add_offline(result, self.cid) is False:
                    if await myerror('網路錯誤', '請問是否重新嘗試') is False:
                        break
            self.close()

        def resizeEvent(self, event):
            Window.resizeEvent(self, event)
            self.shadow_widget_.resize(self.width() - self.padding * 2, self.height() - self.padding * 2)
            self.load.move(
                int((self.shadow_widget_.width() - self.load.width()) / 2),
                int((self.shadow_widget_.height() - self.load.height()) / 2)
            )

    _offline = Offline()
    _offline.show()
    while 1:
        if _offline.isVisible() is False:
            return
        await sleep(0.1)


async def folderlist(text, buttonname, directory):
    class FolderList(Window):
        def __init__(self):
            super().__init__(TitleLabel_2, 75, tracking=False)
            self.titlelabel.setdata(text, (30, 25, 250, 30))
            self.resize(700, 565)
            # 設置 背景空白 圓角邊框
            self.setStyleSheet('#shadow_widget{background-color:rgb(255,255,255);border-radius:15px}')
            # 目前所在目錄
            self.self_path_list = '0'
            self.search_cid = None
            # 所有目錄資料
            self.allpath = {}
            # 上一頁目錄順序
            self.up_page_list = []
            # 下一頁目錄順序
            self.under_page_list = []
            self.listdirectory = ListDirectory(False, self.content_widget)
            self.listdirectory.setStyleSheet(
                'NList{border-style:solid; border-bottom-width:1px; border-color:rgba(200, 200, 200, 125)}'
            )
            # 結果
            self.result = None
            # 設定目錄點擊回調
            self.listdirectory.directory_slot = self.directory_del
            # 設定頁數回調
            self.listdirectory.page_callback = self.setpage
            # 設定上一頁回調
            self.listdirectory.pgup_connect(self.up_page)
            # 設定下一頁回調
            self.listdirectory.pgon_connect(self.under_page)
            # 設定重新整理回調
            self.listdirectory.rectangle_connect(lambda: create_task(self.reorganize()))
            # 設定搜索回調
            self.listdirectory.linedit_connect(self._search_callback)
            self.listdirectory.set_search_all_connect(self._set_search_all_callback)
            self.listdirectory.set_search_name_connect(self._set_search_name_callback)

            # 開始離線按鈕
            self.button = MyQLabel(
                buttonname, (520, 411, 130, 40), clicked=self.end, qss=1, fontsize=16, parent=self.content_widget
            )
            self.folder_button = MyQLabel(
                '新建資料夾', (20, 411, 130, 40), clicked=lambda: create_task(self.get_enter('新建資料夾')),
                fontsize=16, parent=self.content_widget
            )

            # MyIco('黑色關閉', '藍色關閉', coordinate=(620, 35, 12, 12), state=True,
            #       click=self.close, parent=self.shadow_widget)

            create_task(self.network(cid='0', pages=True))

        async def get_enter(self, action):
            if action == '新建資料夾' and self.self_path_list[0:3] != '搜索-':
                if name := await myenter('新建資料夾', '新名稱'):
                    await self.network(self.self_path_list, data=name, action='新建資料夾')

        def _set_search_name_callback(self):
            cid = f'搜索-{self.search_cid[0]}-{self.search_cid[1]}-{self.search_cid[2]}'
            create_task(self.network(cid, pages=False))

        def _set_search_all_callback(self):
            cid = f'搜索-0-{self.search_cid[1]}-{self.search_cid[2]}'
            create_task(self.network(cid, pages=False))

        def _search_callback(self):
            if self.self_path_list[0:3] == '搜索-':
                cid = self.search_cid[0]
                path = self.allpath[self.self_path_list]["path"][-1][0][3:]
            else:
                cid = self.self_path_list
                path = self.allpath[self.self_path_list]["path"][-1][0]
            create_task(self.network(
                f'搜索-{cid}-{path}-'
                f'{self.listdirectory.lineEdit.text()}', pages=True)
            )

        def end(self):
            if self.self_path_list[0:3] != '搜索-':
                self.result = self.self_path_list, self.allpath[self.self_path_list]["path"][-1][0]
                self.close()

        def closeEvent(self, event):
            if self.result is None:
                self.result = False
            event.accept()

        # 搜索
        @error()
        async def search(self, cid, index):
            self.listdirectory.lineEdit.setText('')
            _cid, _, name = re.search('搜索-(.+)-(.+)-(.+)', cid).groups()
            result = await directory.searchfolder(
                name, _cid,
                index * self.listdirectory.pagemax, self.listdirectory.pagemax
            )
            if result:
                if cid not in self.allpath:
                    self.allpath.update(self.dumps(cid, result, index))
                else:
                    self.allpath[cid][index] = self.dumps(cid, result, index)[cid][index]
            return result

        # 重新整理回調
        async def reorganize(self):
            self.listdirectory.refresh_show()
            await self.network(cid=self.self_path_list)
            self.listdirectory.refresh_hide()

        # 上一頁回調
        def up_page(self):
            cid = self.up_page_list.pop()
            self.under_page_list.append(cid)
            if len(self.up_page_list) == 1:
                self.listdirectory.set_pgup(False)
            if not self.listdirectory.get_pgon():
                self.listdirectory.set_pgon(True)
            cid = self.up_page_list[-1]
            create_task(self.network(cid=cid, pages=False))

        # 下一頁回調
        def under_page(self):
            cid = self.under_page_list.pop()
            if not self.under_page_list:
                self.listdirectory.set_pgon(False)
            self.up_page_list.append(cid)
            create_task(self.network(cid=cid, pages=False))

        # 頁數回調
        def setpage(self, index):
            cid = self.self_path_list
            if index not in self.allpath[cid]:
                create_task(self.network(cid=self.self_path_list, index=index))

        # 目錄點擊回調
        def directory_del(self, texts):
            create_task(self.network(cid=texts.data, pages=True))

        async def network(self, cid, index=0, data=None, action=None,  pages=None):
            # self.setCursor(Qt.ArrowCursor)
            self.listdirectory.scrollarea.verticalcontents.setvalue(0)
            self.listdirectory.scrollarea.hrizontalcontents.setvalue(0)
            # 瀏覽目錄清空
            self.listdirectory.directory_cls()
            # 統計數字隱藏
            self.listdirectory.quantity.alltext.hide()
            # 顯示等待動畫
            self.listdirectory.load_show()
            # 禁止操作
            self.prohibit(True)
            if cid[0:3] == '搜索-':
                search = re.search('搜索-(.+)-(.+)-(.+)', cid).groups()
                if self.self_path_list[0:3] != '搜索-':
                    self.search_cid = search
                    if self.search_cid[0] != '0':
                        self.listdirectory.setname(self.search_cid[1])
                else:
                    if search[1] != self.listdirectory.searchbutton.search_name.text():
                        self.listdirectory.setname(search[1])
                    self.listdirectory.searchbutton.hide()
            elif self.self_path_list[0:3] == '搜索-' and cid[0:3] != '搜索-':
                self.listdirectory.searchbutton.hide_()

            # 設定目前所在目錄
            if self.self_path_list != cid:
                self.self_path_list = cid
                # 刪除舊的容器
                self.listdirectory.delete_contents()
                # 新增新容器
                self.listdirectory.new_contents()

            result = True
            if action == '新建資料夾':
                if await self.add_folder(cid, data) is False:
                    result = False

            if pages is True:
                # 下一頁目錄清空
                self.under_page_list = []
                # 下一頁按鈕 不可使用
                self.listdirectory.set_pgon(False)
                # 上一頁加入
                self.up_page_list.append(cid)
            if result:
                if cid[0:3] == '搜索-':
                    await self.search(cid, index)
                else:
                    # 刷新目錄
                    if await create_task(self.refresh(cid, index)) == '0':
                        create_task(self.network(cid='0', pages=True))
                        return
                # 目錄添加到列表
                await create_task(self.add(cid, index, True))
                if cid[0:3] == '搜索-':
                    self.listdirectory.searchbutton.show()
            # 可以操作
            self.prohibit(False)
            # 隱藏等待動畫
            self.listdirectory.load_hide()
            if self.listdirectory.quantity:
                # 統計數字顯示
                self.listdirectory.quantity.alltext.show()

        # 新建資料夾
        @error()
        async def add_folder(self, pid, name):
            return await directory.add_folder(pid, name)

        # 添加到窗口列表
        async def add(self, cid, index, value):
            # 獲取目錄相關資料
            text, data, ico, my_mode, text_mode = self.allpath[cid][index].values()
            path = self.allpath[cid]['path']
            # 查看 上一頁 是否可以顯示可用
            if len(self.up_page_list) != 1 and not self.listdirectory.get_pgup():
                # 設定 上一頁按鈕 成可用
                self.listdirectory.set_pgup(True)
            if index == 0:
                self.listdirectory.page_advance(self.allpath[cid]['page'])
            # 查看是否需要手動添加
            if value:
                # 添加目錄到新的內容窗口
                await self.listdirectory.text_adds(text, index=index, icos=ico, datas=data, my_modes=my_mode, text_modes=text_mode)
            else:
                # 更換舊的內容窗口資料
                self.listdirectory.replace_contents(cid)
            # 添加瀏覽目錄
            for _path in path:
                self.listdirectory.directory_add(_path[0], data=_path[1])

        @error()
        async def refresh(self, cid, index):
            result = await directory.folder(cid, index * self.listdirectory.pagemax, self.listdirectory.pagemax)
            if result:
                if index == 0:
                    self.allpath.update(self.dumps(cid, result, index))
                else:
                    self.allpath[cid][index] = self.dumps(cid, result, index)[cid][index]
            return result

        # 禁止操作
        def prohibit(self, mode):
            # 是否禁止 搜索欄
            self.listdirectory.directorycontainer.setEnabled(not mode)
            # 是否禁止 頁數欄
            self.listdirectory.quantity.pageico.setEnabled(not mode)
            self.button.setEnabled(not mode)
            self.folder_button.setEnabled(not mode)

        # 分析115數據
        def dumps(self, cid, items, index):
            def _getpath(__cid):
                return lambda: create_task(self.network(__cid, pages=True))
            path = {cid: {index: {'text': [], 'data': [], 'ico': [], 'my_mode': [], 'text_mode': []},
                          'path': [], 'page': 0}}

            for data in items['data']:
                if 'te' in data:
                    _time = data['te']
                else:
                    _time = data['t'] if data['t'].isdigit() else int(
                        time.mktime(time.strptime(f"{data['t']}:0", "%Y-%m-%d %H:%M:%S")))
                _Time = time.strftime('%Y-%m-%d %H:%M', time.localtime(int(_time)))
                ico = get_ico(splitext(data['n'])[1] if 'fid' in data else '資料夾')
                size = data['s'] if 's' in data else '0'

                path[cid][index]['text'].append(data['n'])
                _cid = str(data['fid']) if 'fid' in data else str(data['cid'])
                path[cid][index]['data'].append({
                    'name': data['n'],
                    'category': '1' if 'fid' in data else '0',
                    'cid': _cid,
                    'pid': data['pid'] if 'pid' in data else data['cid'],
                    'time': int(_time),
                    'pc': data['pc'],
                    'sha1': data['sha'] if 'sha' in data else None,
                    'size': int(size),
                    'ico': ico,
                    'dp': data['dp'] if 'dp' in data else None,
                })

                path[cid][index]['ico'].append(ico)
                slot = _getpath(_cid)
                my_mode = {'leftclick': [slot], 'cursor': True}
                text_mode = {'leftclick': [slot], 'cursor': True}
                path[cid][index]['my_mode'].append(my_mode)
                path[cid][index]['text_mode'].append(text_mode)

            if index == 0:
                page = math.ceil(items['count'] / self.listdirectory.pagemax)
                path[cid].update({'page': page})
                if 'path' in items:
                    for _path in items['path']:
                        path[cid]['path'].append((_path['name'], str(_path['cid'])))
                # 搜索
                elif 'folder' in items:
                    path[cid]['path'].append(('根目录', '0'))
                    path[cid]['path'].append((f'搜尋-{self.search_cid[1]}', cid))
            return path

        def resizeEvent(self, event):
            Window.resizeEvent(self, event)
            self.listdirectory.resize(self.content_widget.width(), self.content_widget.height() - 70)

    _folderlist = FolderList()
    _folderlist.show()
    while 1:
        if _folderlist.result is not None:
            return _folderlist.result
        await sleep(0.1)


async def sha1save(cid, name, directory):
    class Sha1Save(Window):
        def __init__(self):
            super().__init__(TitleLabel_2, 75, tracking=False)
            self.titlelabel.setdata('添加sha1鏈結', (30, 25, 250, 30))
            self.resize(746, 381)
            # 設置 背景空白 圓角邊框
            self.setStyleSheet('#shadow_widget{background-color:rgb(255,255,255);border-radius:15px}')
            # 顯示保存到哪裡標籤
            self.savetext = TextQLabel(f'保存到：{name}', fontsize=12, move=(30, 235), parent=self.content_widget)
            # 導入sha1鏈結文件標題
            TextQLabel('導入sha1鏈結文件', fontsize=12, move=(30, 195), parent=self.content_widget)
            # 未選擇任何檔案標題
            self.file_label = TextQLabel(f'未選擇任何檔案', fontsize=12, move=(260, 193), parent=self.content_widget)
            self.file_label.setStyleSheet('color: blue')
            MyQLabel('選擇檔案', (170, 187, 80, 30), fontsize=16, clicked=self.open, parent=self.content_widget)
            self.changebutton = MyQLabel(
                '更改目錄', (self.savetext.x() + self.savetext.width() + 10, 227, 80, 30),
                clicked=lambda: create_task(self.folder()), fontsize=16, parent=self.content_widget
            )
            MyQLabel(
                '開始sha1轉存', (540, 220, 150, 40), qss=1, fontsize=19,
                clicked=self.end, parent=self.content_widget
            )
            MyIco('黑色關閉', '藍色關閉', coordinate=(670, 35, 12, 12), state=True, click=self.close, parent=self.titlelabel)
            self.text = QTextEdit(self.content_widget)
            self.text.setGeometry(30, 0, 660, 175)
            self.cid = cid
            self.path = None
            self.result = None

        async def folder(self):
            if data := await folderlist('選擇要保存的資料夾', '保存到這裡', directory):
                self.cid, _name = data
                self.savetext.setText(f'保存到：{_name}')
                self.savetext.adjustSize()
                self.changebutton.move(self.savetext.x() + self.savetext.width() + 10, 269)

        def end(self):
            if text := self.text.toPlainText():
                if text[-1] != '\n':
                    text += '\n'
            if self.path:
                with open(self.path, 'r', encoding='UTF-8') as f:
                    text += f.read()
            if text:
                self.result = self.cid, text
            self.close()

        def open(self):
            self.path, _ = QFileDialog.getOpenFileName(self, "選擇sha1檔案", "/", filter='Text Files (*.txt)')
            if self.path:
                self.file_label.setText(f'{basename(self.path)}')
            else:
                self.file_label.setText('未選擇任何檔案')
            self.file_label.adjustSize()

        def closeEvent(self, event):
            if self.result is None:
                self.result = False
            event.accept()

    _sha1save = Sha1Save()
    _sha1save.show()
    while 1:
        if _sha1save.result is not None:
            return _sha1save.result
        await sleep(0.1)


def myfiledialog(parent):
    class MyFileDialog(QFileDialog):
        def __init__(self):
            super(MyFileDialog, self).__init__(parent)
            self.result = ''
            self.setOption(QFileDialog.DontUseNativeDialog, True)
            self.findChild(QListView, 'listView').setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.findChild(QTreeView, 'treeView').setSelectionMode(QAbstractItemView.ExtendedSelection)
            button = self.findChild(QDialogButtonBox, 'buttonBox')
            button.accepted.disconnect(self.accept)
            button.accepted.connect(lambda: self.setvalue(self.selectedFiles()))
            self.exec()

        def setvalue(self, value):
            self.result = value
            self.close()

    _myfiledialog = MyFileDialog()
    return _myfiledialog.result


if __name__ == '__main__':
    from PyQt5.Qt import QApplication
    import sys
    app = QApplication(sys.argv)
    # widget = Enter('新建資料夾', '新名稱')
    widget = sha1save(0, 0, 0)
    widget.show()
    sys.exit(app.exec_())