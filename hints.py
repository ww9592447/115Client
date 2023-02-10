from module import picture, QLabel, Window, QFont, QFrame, sleep, QLineEdit, gif, Optional, Callable, \
    TextQLabel, QTextEdit, MyIco, MyQLabel, ListDirectory, time, create_task, get_ico, \
    splitext, math, QFileDialog, basename, QListView, QTreeView, QAbstractItemView, QDialogButtonBox, \
    MyTextSave, NTextSave, Union, AllNPath, QResizeEvent, QCloseEvent, QApplication, QObject, Qt
import winsound
import re
from API.directory import Directory


def error():
    def decorator(func):
        async def wrap(self=None, *args, state=True, **kwargs):
            while (result := await func(self, *args, **kwargs)) is False:
                if state and await myerror('網路錯誤', '請問是否重新嘗試') is False:
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

    def setdata(self, text, geometry):
        self.label = TextQLabel(text, fontsize=14, geometry=geometry, parent=self)
        self.label.show()


class Error(Window):
    def __init__(self, title, name) -> None:
        Window.__init__(self, TitleLabel_1, 30, tracking=False)
        self.titlelabel.label.setText(title)
        # 結果
        self.result: Optional[bool] = None
        # 灰色背景容器
        self.frame = QFrame(self.content_widget)
        # 灰色背景qss
        self.frame.setStyleSheet('QFrame{background-color:rgb(240, 240, 240); border-bottom-style:solid;'
                                 ' border-top-width:1px; border-top-color: rgba(200, 200, 200, 175)}')

        # 設置警告容器
        label: QLabel = QLabel(self.content_widget)
        # 設置警告圖片
        label.setPixmap(picture('警告'))
        # 設置警告圖片位置
        label.move(20, 10)
        # 設置錯誤文字
        TextQLabel(name, fontsize=15, move=(60, 15), parent=self.content_widget)
        # 設置 是 按鈕
        MyQLabel('是', (27, 57, 75, 27), qss=2, clicked=lambda: self.end(True), fontsize=16, parent=self.content_widget)
        # 設置 否 按鈕
        MyQLabel('否', (132, 57, 75, 27), qss=2, clicked=lambda: self.end(False), fontsize=16, parent=self.content_widget)
        self.resize(260, 145)

    # 關閉事件
    def end(self, result: bool) -> None:
        # 設置結果
        self.result = result
        # 關閉
        self.close()

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        Window.resizeEvent(self, event)
        self.frame.setGeometry(0, self.content_widget.height() - 40, self.content_widget.width(), 40)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.result is None:
            self.result = False
        event.accept()


class Enter(Window):
    def __init__(self, title, name) -> None:
        Window.__init__(self, TitleLabel_1, 30, tracking=False)
        self.titlelabel.label.setText(title)
        # 結果
        self.result = None
        # 灰色背景
        self.content_widget.setStyleSheet('background-color:rgb(240, 240, 240)')

        TextQLabel(name, fontsize=11, move=(11, 10), parent=self.content_widget)

        self.text: QLineEdit = QLineEdit(self.content_widget)
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

    def end(self, result: bool) -> None:
        self.result = result
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.result is None:
            self.result = False
        event.accept()


async def myerror(title, name) -> None:
    _error = Error(title, name)
    _error.show()
    winsound.PlaySound("SystemQuestion", winsound.SND_ASYNC)
    while 1:
        if _error.result is not None:
            return _error.result
        await sleep(0.1)


async def myenter(title, name) -> str:
    _enter = Enter(title, name)
    _enter.show()
    while 1:
        if _enter.result is not None:
            return _enter.result
        await sleep(0.1)


# 瀏覽窗口
class FolderList(Window):
    def __init__(self, directory: Directory):
        super().__init__(TitleLabel_2, 75, tracking=False)
        self.resize(700, 565)
        # 所有目錄資料
        self.allpath: dict[str, AllNPath] = {}
        # 目錄操作
        self.directory: Directory = directory
        # 目前所在目錄
        self.self_path_list: str = '0'
        # 目前搜索cid
        self.search_cid: str = ''
        # 上一頁目錄順序
        self.up_page_list: list[str, ...] = []
        # 下一頁目錄順序
        self.on_page_list: list[str, ...] = []
        # 獲取瀏覽視窗
        self.listdirectory = ListDirectory(False, self.content_widget)
        self.listdirectory.setStyleSheet(
            'NList{border-style:solid; border-bottom-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )
        # 結果
        self.result: Optional[tuple[str, str]] = None
        # 設定重新整理回調
        self.listdirectory.rectangle_connect(lambda: create_task(self.reorganize()))
        # 設定搜索回調
        self.listdirectory.linedit_connect(self._search_callback)
        # 設定搜索全部回調
        self.listdirectory.searchcontents.set_search_all_callback(self._set_search_all_callback)
        # 設定搜索名稱回調
        self.listdirectory.searchcontents.set_search_name_callback(self._set_search_name_callback)
        # 設定頁數回調
        self.listdirectory.page_callback = self.setpage
        # 設定目錄點擊回調
        self.listdirectory.directory_slot = lambda text: create_task(self.network(text.data))
        # 設定上一頁回調
        self.listdirectory.pgup_connect(self.up_page)
        # 設定下一頁回調
        self.listdirectory.pgon_connect(self.under_page)
        # 設定右鍵回調
        self.listdirectory.menu_callback = self.menu_callback
        # 禁止橫滾動條出現
        self.listdirectory.scrollarea.sethrizontal(False)
        # 設置 背景空白 圓角邊框
        self.setStyleSheet('#shadow_widget{background-color:rgb(255,255,255);border-radius:15px}')
        # 設置確認按鈕
        self.yesbutton: MyQLabel = MyQLabel(
            '', (520, 411, 130, 40), clicked=self.end, qss=1, fontsize=16, parent=self.content_widget
        )
        # 設置 新增文件夾 按鈕
        MyQLabel(
            '新建資料夾', (20, 411, 130, 40), clicked=lambda: create_task(self.get_enter('新建資料夾')),
            fontsize=16, parent=self.content_widget
        )
        # 設置 關閉按鈕
        MyIco('黑色關閉', '藍色關閉', coordinate=(620, 35, 12, 12), state=True,
              click=self.close, parent=self.shadow_widget)

    async def stop(self, titletext: str, text: str, parent: QObject) -> tuple[str, str]:
        # 初始化結果
        self.result: Optional[tuple[str, str]] = None
        # 初始化所有目錄資料
        self.allpath.clear()
        # 初始化目前所在目錄
        self.self_path_list: str = '0'
        # 初始化目前搜索cid
        self.search_cid: str = ''
        # 初始化上一頁目錄順序
        self.up_page_list.clear()
        # 初始化下一頁目錄順序
        self.on_page_list.clear()
        # 初始化所有介面的頁數資料
        self.listdirectory.savecontents.clear()
        # 設置標題名稱
        self.titlelabel.setdata(titletext, (30, 25, 250, 30))
        # 設置確定按鈕名稱
        self.yesbutton.setText(text)
        # 獲取桌面訊息
        desktop = QApplication.desktop()
        # 獲取自身所在螢幕座標
        rect = desktop.screenGeometry(desktop.screenNumber(parent))
        # 置中窗口
        self.move(rect.left() + (rect.width() - self.width()) / 2, (rect.height() - self.height()) / 2)
        # 顯示窗口
        self.show()
        create_task(self.network('0'))
        while 1:
            if self.result is not None:
                return self.result
            await sleep(0.1)

    def end(self) -> None:
        if self.self_path_list[0:3] != '搜索-':
            self.result = self.self_path_list, self.allpath[self.self_path_list]["path"][-1][0]
            self.close()

    # 網路
    async def network(self, cid: str, page: int = 1, action: Optional[Callable] = None, add: bool = True) -> None:
        # 瀏覽目錄清空
        self.listdirectory.directory_cls()
        # 顯示等待動畫
        self.listdirectory.set_load_visible(True)
        # 查看cid是否是搜索
        if cid[0:3] == '搜索-':
            # 分割 cid 獲取資料
            search = re.search('搜索-(.+)-(.+)-(.+)', cid).groups()
            # 查看上一頁是不是搜索
            #  上一頁不是搜索
            if self.self_path_list[0:3] != '搜索-':
                # 設定目前搜索 cid資料
                self.search_cid = search
                # 查看 搜索cid 是不是根目錄
                if self.search_cid[0] != '0':
                    # 設定搜索名稱按鈕
                    self.listdirectory.searchcontents.setname(self.search_cid[1])
            # 上一頁是搜索
            else:
                # 查看 搜索cid 是不是 根目錄 and 查看目前搜索名稱 是不是跟 上一頁 搜索名稱不一致
                if search[0] != '0' and search[1] != self.listdirectory.searchcontents.search_name.text():
                    # 重新設定搜索名稱按鈕
                    self.listdirectory.searchcontents.setname(search[1])
                # 搜索按鈕全部影藏
                self.listdirectory.searchcontents.hide()
        # 目前不是搜索 and 上一頁是搜索
        elif self.self_path_list[0:3] == '搜索-':
            # 搜索按鈕初始化
            self.listdirectory.searchcontents.hide_()

        # 查看是否要新增 上一頁目錄
        if add is True:
            # 下一頁目錄清空
            self.on_page_list.clear()
            # 下一頁按鈕 不可使用
            self.listdirectory.set_pgon(False)
            # 上一頁加入
            self.up_page_list.append(cid)

        result = True
        if action or (cid in self.allpath and self.allpath[cid]['refresh']):
            if action:
                self.listdirectory.cls()
                if await action() is False:
                    result = False
            if result:
                del self.allpath[cid]
                del self.listdirectory.savecontents[cid]

        if cid not in self.listdirectory.savecontents:
            self.listdirectory.new(cid)

        if result:
            if cid not in self.allpath or page not in self.allpath[cid]['data']:
                if cid[0:3] == '搜索-':
                    await self.search(cid, page)
                else:
                    # 刷新目錄
                    if await create_task(self.refresh(cid, page)) == '0':
                        create_task(self.network('0'))
                        return
            self.add(cid, page)
            if cid[0:3] == '搜索-':
                self.listdirectory.searchcontents.show()
        # 關閉等待動畫
        self.listdirectory.set_load_visible(False)

    # 添加到窗口列表
    def add(self, cid: str, page: int) -> None:
        # 查看 上一頁 是否可以顯示可用
        if len(self.up_page_list) != 1 and not self.listdirectory.get_pgup():
            # 設定 上一頁按鈕 成可用
            self.listdirectory.set_pgup(True)

        # 添加瀏覽目錄
        for _path in self.allpath[cid]['path']:
            self.listdirectory.directory_add(_path[0], data=_path[1])

        # 查看 目前目錄是否發生變化
        if self.self_path_list != cid:
            # 查看上一頁是否是搜索
            if self.self_path_list[0:3] == '搜索-':
                # 如果是則把上一頁搜索設定成需要刷新
                self.allpath[self.self_path_list]['refresh'] = True
            # 設定目前所在目錄
            self.self_path_list = cid

            if cid in self.listdirectory.savecontents:
                self.listdirectory.switch(cid)
                if self.listdirectory.textall != 0:
                    return

        # 查看是否需要增加頁數
        if self.listdirectory.quantity.pagemax != self.allpath[cid]['page']:
            self.listdirectory.addallpage(self.allpath[cid]['page'])
            if page != self.listdirectory.quantity.page:
                self.listdirectory.quantity.setpage(page, callback=False)

        # 添加內容
        self.listdirectory.textadds(
            self.allpath[cid]['data'][page]
        )

    # 刷新目錄
    @error()
    async def refresh(self, cid: str, page: int) -> Union[str, bool]:
        result = await self.directory.folder(cid, (page - 1) * self.listdirectory.pagemax, self.listdirectory.pagemax)
        if result:
            if cid != str(result['cid']):
                return '0'
            # 格式化115數據
            self.dumps(result, cid, page)
            return True
        return False

    # 搜索
    @error()
    async def search(self, cid: str, page: int) -> bool:
        self.listdirectory.lineEdit.setText('')
        _cid, _, name = re.search('搜索-(.+)-(.+)-(.+)', cid).groups()
        result = await self.directory.searchfolder(
            name, _cid,
            (page - 1) * self.listdirectory.pagemax, self.listdirectory.pagemax
        )
        if result:
            # 格式化115數據
            self.dumps(result, cid, page)
            return True
        return False

    # 頁數回調
    def setpage(self, page: int) -> None:
        cid = self.self_path_list
        if page not in self.allpath[cid]['data'] or self.allpath[cid]['refresh'] or self.listdirectory.textall == 0:
            create_task(self.network(cid=cid, page=page, add=False))

    # 格式化115數據
    def dumps(self, items: dict, cid: str, page: int) -> None:
        def _getpath(__cid):
            return lambda: create_task(self.network(__cid))

        index: dict[str, dict[str, any]] = {}
        textsavelist: list[NTextSave, ...] = []
        for data in items['data']:
            textsave: NTextSave = NTextSave(text={}, data=None, ico=None, leftclick=None, doubleclick=None)
            # 獲取 檔案 or 資料夾 修改日期時間戳 並轉換成正常日期
            if 'te' in data:
                _time = data['te']
            else:
                _time = data['t'] if data['t'].isdigit() else int(
                    time.mktime(time.strptime(f"{data['t']}:0", "%Y-%m-%d %H:%M:%S")))
            _Time = time.strftime('%Y-%m-%d %H:%M', time.localtime(int(_time)))
            # 獲取是否是檔案還是資料夾 ico
            ico = get_ico(splitext(data['n'])[1] if 'fid' in data else '資料夾')
            # 獲取檔案大小
            size = data['s'] if 's' in data else '0'
            # 獲取檔案cid
            _cid = str(data['fid']) if 'fid' in data else str(data['cid'])
            # 獲取點擊回調
            slot = _getpath(_cid)
            if ico == '資料夾':
                text: MyTextSave = MyTextSave(text=data['n'], leftclick=[slot], color=((0, 0, 0), (6, 168, 255)))
            else:
                text: MyTextSave = MyTextSave(text=data['n'], leftclick=None, color=None)
            textsave['text'] = text
            textsave['data'] = {
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
            }
            textsave['ico'] = ico
            textsave['doubleclick'] = [slot] if ico == '資料夾' else None
            index[data['n']] = textsave['data']
            textsavelist.append(textsave)

        if cid not in self.allpath:
            if 'path' in items:
                path = [(i['name'], str(i['cid'])) for i in items['path']]
            else:
                path = [('根目录', '0'), (f'搜尋-{self.search_cid[1]}', cid)]
            self.allpath.update(
                {
                    cid:
                        {
                            'data': {page: textsavelist},
                            'path': path,
                            'index': index,
                            'refresh': False,
                            'count': items['count'],
                            'page': math.ceil(items['count'] / self.listdirectory.pagemax),
                        }

                }
            )
        else:
            self.allpath[cid]['data'][page] = textsavelist
            self.allpath[cid]['index'].update(index)

    # 上一頁回調
    def up_page(self) -> None:
        # 獲取上一頁最後一cid
        cid = self.up_page_list.pop()
        # cid 添加到下一頁
        self.on_page_list.append(cid)
        # 查看 上一頁 是否只有一個
        if len(self.up_page_list) == 1:
            # 如果只有一個 設定 上一頁按鈕 關閉
            self.listdirectory.set_pgup(False)
        # 查看 下一頁按鈕 是否關閉
        if not self.listdirectory.get_pgon():
            # 如果關閉 則啟動
            self.listdirectory.set_pgon(True)
        # 獲取上一頁最後一個cid
        cid = self.up_page_list[-1]
        # 進入上一頁最後一個cid
        create_task(self.network(cid=cid, add=False))

    # 下一頁回調
    def under_page(self) -> None:
        # 獲取 下一頁 最後一個 cid
        cid = self.on_page_list.pop()
        # 查看 下一頁 是否還有
        if not self.on_page_list:
            # 如果沒有 則把 下一頁按鈕 關閉
            self.listdirectory.set_pgon(False)
        # cid 添加到 上一頁
        self.up_page_list.append(cid)
        # 進入 cid
        create_task(self.network(cid=cid, add=False))

    # 重新整理回調
    async def reorganize(self) -> None:
        self.listdirectory.set_refresh_gif_visible(True)
        self.allpath[self.self_path_list]['refresh'] = True
        await create_task(self.network(cid=self.self_path_list, page=self.listdirectory.quantity.page))
        self.listdirectory.set_refresh_gif_visible(False)

    # 右鍵回調
    def menu_callback(self, menu: Callable) -> None:
        if len(self.listdirectory.currentclick) > 1:
            self.listdirectory.set_menu_visible('重新命名', False)
        menu()
        self.listdirectory.set_menu_visible('重新命名', True)

    # 搜索回調
    def _search_callback(self) -> None:
        if self.self_path_list[0:3] == '搜索-':
            cid = self.search_cid[0]
            path = self.allpath[self.self_path_list]['path'][-1][0][3:]
        else:
            cid = self.self_path_list
            path = self.allpath[self.self_path_list]['path'][-1][0]
        create_task(self.network(
            f'搜索-{cid}-{path}-'
            f'{self.listdirectory.lineEdit.text()}')
        )

    # 搜索名稱回調
    def _set_search_name_callback(self) -> None:
        cid = f'搜索-{self.search_cid[0]}-{self.search_cid[1]}-{self.search_cid[2]}'
        if cid in self.allpath:
            self.allpath[cid]['refresh'] = True
        create_task(self.network(cid, add=False))

    # 搜索全部回調
    def _set_search_all_callback(self) -> None:
        cid = f'搜索-0-{self.search_cid[1]}-{self.search_cid[2]}'
        if cid in self.allpath:
            self.allpath[cid]['refresh'] = True
        create_task(self.network(cid, add=False))

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        Window.resizeEvent(self, event)
        self.listdirectory.resize(self.content_widget.width(), self.content_widget.height() - 70)


# 離線窗口
async def offline(directory, folderlist: FolderList) -> None:
    class Offline(Window):
        def __init__(self) -> None:
            super().__init__(TitleLabel_2, 75, tracking=False)
            # 設置離線標題
            self.titlelabel.setdata('添加離線鏈結', (30, 25, 120, 30))
            self.setStyleSheet('#shadow_widget{background-color:rgb(255,255,255);border-radius:15px}')
            self.cid = ''
            self.text = QTextEdit(self.shadow_widget)
            self.text.setGeometry(30, 75, 660, 175)

            self.savetext = TextQLabel(f'保存到：云下载', fontsize=12, move=(30, 275), parent=self.shadow_widget)
            # 設置更改目錄按鈕
            self.button: MyQLabel = MyQLabel(
                '更改目錄', (self.savetext.x() + self.savetext.width() + 10, 269, 80, 30),
                clicked=lambda: create_task(self.folder()), fontsize=12, parent=self.shadow_widget
            )
            # 設置關閉按鈕
            MyIco('黑色關閉', '藍色關閉', coordinate=(670, 35, 12, 12), state=True,
                  click=self.close, parent=self.shadow_widget)

            # 設置開始離線按鈕
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
            # 設置窗口大小
            self.resize(746, 346)

        async def folder(self) -> None:
            if data := await folderlist.stop('選擇要保存的資料夾', '保存到這裡', self):
                self.cid, name = data
                self.savetext.setText(f'保存到：{name}')
                self.savetext.adjustSize()
                self.button.move(self.savetext.x() + self.savetext.width() + 10, 269)

        async def end(self) -> None:
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

        # 調整大小事件
        def resizeEvent(self, event: QResizeEvent) -> None:
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


async def sha1save(cid: str, name: str, folderlist: FolderList):
    class Sha1Save(Window):
        def __init__(self) -> None:
            super().__init__(TitleLabel_2, 75, tracking=False)
            # 設置 sha1 標題
            self.titlelabel.setdata('添加sha1鏈結', (30, 25, 250, 30))
            # 設置 背景空白 圓角邊框
            self.setStyleSheet('#shadow_widget{background-color:rgb(255,255,255);border-radius:15px}')
            # 顯示保存到哪裡標籤
            self.savetext = TextQLabel(f'保存到：{name}', fontsize=12, move=(30, 235), parent=self.content_widget)
            # 導入sha1鏈結文件標題
            TextQLabel('導入sha1鏈結文件', fontsize=12, move=(30, 195), parent=self.content_widget)
            # 未選擇任何檔案標題
            self.file_label: TextQLabel = TextQLabel(f'未選擇任何檔案', fontsize=12, move=(260, 193), parent=self.content_widget)
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
            # 設置 sha1 文本框
            self.text: QTextEdit = QTextEdit(self.content_widget)
            self.text.setGeometry(30, 0, 660, 175)
            # 保存目錄cid
            self.cid: str = cid
            # sha1文件路徑
            self.path: str = ''
            # 結果
            self.result: Optional[tuple[str, str]] = None
            # 設置窗口大小
            self.resize(746, 381)

        async def folder(self) -> None:
            if data := await folderlist.stop('選擇要保存的資料夾', '保存到這裡', self):
                self.cid, _name = data
                self.savetext.setText(f'保存到：{_name}')
                self.savetext.adjustSize()
                self.changebutton.move(self.savetext.x() + self.savetext.width() + 10, 227)

        def end(self) -> None:
            if text := self.text.toPlainText():
                if text[-1] != '\n':
                    text += '\n'
            if self.path:
                with open(self.path, 'r', encoding='UTF-8') as f:
                    text += f.read()
            if text:
                self.result = self.cid, text
            self.close()

        def open(self) -> None:
            self.path, _ = QFileDialog.getOpenFileName(self, "選擇sha1檔案", "/", filter='Text Files (*.txt)')
            if self.path:
                self.file_label.setText(f'{basename(self.path)}')
            else:
                self.file_label.setText('未選擇任何檔案')
            self.file_label.adjustSize()

        def closeEvent(self, event: QCloseEvent) -> None:
            if self.result is None:
                self.result = False
            event.accept()

    _sha1save = Sha1Save()
    _sha1save.show()
    while 1:
        if _sha1save.result is not None:
            return _sha1save.result
        await sleep(0.1)


async def myfiledialog(parent: QObject) -> list[str, ...]:
    class MyFileDialog(QFileDialog):
        def __init__(self) -> None:
            super(MyFileDialog, self).__init__(parent)
            self.result: list[str, ...] = []
            self.setWindowModality(Qt.NonModal)
            self.setOption(QFileDialog.DontUseNativeDialog, True)
            self.findChild(QListView, 'listView').setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.findChild(QTreeView, 'treeView').setSelectionMode(QAbstractItemView.ExtendedSelection)
            button = self.findChild(QDialogButtonBox, 'buttonBox')
            button.accepted.disconnect(self.accept)
            button.accepted.connect(lambda: self.setvalue(self.selectedFiles()))
            self.show()

        def setvalue(self, value: list[str, ...]) -> None:
            self.result = value
            self.close()

    _myfiledialog = MyFileDialog()
    _myfiledialog.show()
    while 1:
        if _myfiledialog.result:
            return _myfiledialog.result
        await sleep(0.1)

