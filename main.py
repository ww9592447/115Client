from module import QApplication, QWidget, split, set_event_loop, isfile, backdrop, MyQLabel, QFrame, Sidebar\
    , create_task, time, QLabel, picture, pybyte, MyIco, Window, sleep, splitext, srequests, getpath,\
    isdir, walk, join, get_ico, remove, exists, ListDirectory, math, Path, QObject,\
    QResizeEvent, Optional, Callable, TextSave, MyTextSave, Union, AllPath, ConfigParser,  QCloseEvent,\
    Process, Manager, Lock, Value, freeze_support, QButtonGroup, Awaitable, AsyncIterable, QDragEnterEvent, \
    QDropEvent, QFileDialog
from hints import error, myenter, myerror, offline, FolderList, sha1save, myfiledialog
from MyQlist.QText import Text
from API.directory import Directory
from qasync import QEventLoop
from sys import argv
from QList.endlist import EndList
from QList.downloadlist import DownloadList
from QList.uploadlist import UploadList
from QList.sha1list import Sha1List
from QList.aria2list import Aria2List
from QList.offlinelist import Offlinelist
from mprocess import Mprocess
import re
import json


class TitleLabel(QFrame):
    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        # 設置 115 圖標容器
        self.ico: QLabel = QLabel(self)
        # 設置 115 圖標
        self.ico.setPixmap(picture('115ico'))
        # 調整 115 圖標 大小
        self.ico.setGeometry(20, 6, 30, 30)
        # 設置 115 文字圖片容器
        self.text: QLabel = QLabel(self)
        # 設置 115 文字圖片
        self.text.setPixmap(picture('115text'))
        # 設置 115 文字圖片容器 大小
        self.text.setGeometry(58, 8, 76, 29)
        # 副標題
        self.titleLabel: QWidget = QWidget(self)
        # 最小化按鈕
        self.minimize: MyIco = MyIco(
            '黑色縮小', '藍色縮小', state=True, coordinate=(17, 6, 12, 12),
            click=parent.parent().showMinimized, parent=self.titleLabel
        )
        # 最大化按鈕
        self.maximize: MyIco = MyIco(
            '黑色最大化', '藍色最大化', state=True, coordinate=(46, 6, 12, 12),
            click=lambda: self.replace(True), parent=self.titleLabel
        )
        # 關閉按鈕
        self.closure: MyIco = MyIco(
            '黑色關閉', '藍色關閉', state=True, coordinate=(75, 6, 12, 12),
            click=parent.parent().close, parent=self.titleLabel
        )
        # 還原大小按鈕
        self.reduction = MyIco(
            '黑色還原', '藍色還原', state=True, coordinate=(46, 6, 12, 12),
            click=lambda: self.replace(False), parent=self.titleLabel
        )
        # 右側邊框
        self.frame: QFrame = QFrame(self.titleLabel)
        self.frame.setGeometry(0, 3, 1, 19)
        self.frame.setStyleSheet('background-color: rgba(200, 200, 200, 125)')
        # 允許填充背景顏色
        self.setAutoFillBackground(True)
        # 背景設定成空白
        self.setPalette(backdrop('空白'))
        # 初始化還原大小隱藏
        self.reduction.hide()
        # 設定標題下方邊框
        self.setStyleSheet('TitleLabel{border-style:solid; border-bottom-width:1px;'
                           'border-color:rgba(200, 200, 200, 125)}')

    # 根據目前窗口狀態 來決定是否 最大化 還原
    def setico(self) -> None:
        # 查看是否已經最大化
        if self.parent().parent().state:
            # 如果已經最大化 則還原大小
            # 還原按鈕顯示
            self.reduction.show()
            # 最大化按鈕隱藏
            self.maximize.hide()
        else:
            # 還原按鈕隱藏
            self.reduction.hide()
            # 最大化按鈕顯示
            self.maximize.show()

    # 設置 最大化 還原
    def replace(self, visible: bool) -> None:
        if visible:
            self.parent().parent().showMaximized()
        else:
            self.parent().parent().showNormal()

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.titleLabel.move(self.width() - 104, 10)


class Fake115GUI(Window):
    def __init__(self) -> None:
        super().__init__(TitleLabel, 44)
        # 初始化設定
        self.config: ConfigParser = ConfigParser()
        self.config.read('config.ini', encoding='utf-8')
        # 所有目錄資料
        self.allpath: dict[str, AllPath] = {}
        # 目前所在目錄
        self.self_path_list: str = '0'
        # 目前搜索cid
        self.search_cid: str = ''
        # 上一頁目錄順序
        self.up_page_list: list[str, ...] = []
        # 下一頁目錄順序
        self.on_page_list: list[str, ...] = []
        # 待複製列表
        self._copy: list[str, ...] = []
        # 待剪下列表
        self._cut: list[str, ...] = []
        # 原本剪下目錄cid
        self._cut_cid: Optional[str] = None
        # 添加中任務
        self.task: dict[tuple[str, Union[str, int]], Awaitable[Union[str, bool]]] = {}
        # 目前側框
        self.sidebar: int = 1
        # 共用數據
        self._state: dict[str, any] = Manager().dict()
        # 共用數據鎖
        self.lock: Lock = Lock()
        # 傳送列表
        self.wait: list[str, ...] = Manager().list()
        # 傳送列表鎖
        self.waitlock = Lock()
        # 關閉信號
        self.closes: Value = Value('i', 0)
        # 目錄操作
        self.directory: Directory = Directory(self.config)
        # 所有子窗口
        self.child_window: QWidget = QWidget(self.content_widget)
        # 按鈕+瀏覽窗口組合
        self.mylistdirectory: MyListDirectory = MyListDirectory(parent=self)
        # 資料夾瀏覽窗口
        self.folderlist = FolderList(self.directory)
        # 獲取瀏覽視窗
        self.listdirectory: ListDirectory = self.mylistdirectory.listdirectory
        # 加入傳輸完畢視窗
        self.endlist: EndList = EndList(
            lambda: self.sidebar_1.click(), self.network,
            lambda index: self.settext(self.sidebar_6, index), self.child_window
        )
        # 加入下載視窗
        self.downloadlist: DownloadList = DownloadList(
            self._state, self.lock, self.wait, self.waitlock,
            self.config, self.endlist, self.getfolder, lambda index: self.settext(self.sidebar_2, index),
            parent=self.child_window
        )
        # 加入sha1視窗
        self.sha1list: Sha1List = Sha1List(
            self._state, self.lock, self.wait, self.waitlock,
            self.getfolder, lambda index: self.settext(self.sidebar_3, index),  parent=self.child_window
        )
        # 加入上傳視窗
        self.uploadlist = UploadList(
            self._state, self.lock, self.wait, self.waitlock,
            self.config, self.endlist, self.allpath, self.search_add_folder, lambda index: self.settext(self.sidebar_4, index),
            parent=self.child_window
        )
        # 加入aria2視窗
        self.aria2list = Aria2List(
            self._state, self.lock, self.wait, self.waitlock,
            self.config, self.endlist, self.getfolder, lambda index: self.settext(self.sidebar_5, index),
            parent=self.child_window
        )
        # 加入離線視窗
        self.offlinelist: Offlinelist = Offlinelist(
            self.directory, lambda: self.sidebar_1.click(),
            lambda cid: self.network(cid), parent=self.child_window
        )
        # 側邊框 按鈕組
        self.btngroup: QButtonGroup = QButtonGroup(self)
        # 首頁加入左側瀏覽窗口
        self.sidebar_1: Sidebar = Sidebar(
            '首頁', '黑色首頁', '藍色首頁', move=(0, 0),
            window=self.mylistdirectory,
            parent=self.content_widget
        )
        self.sidebar_2: Sidebar = Sidebar(
            '正在下載', '下載', '下載藍色', move=(0, 38), window=self.downloadlist, parent=self.content_widget
        )
        self.sidebar_3 = Sidebar(
            'sha1', '下載', '下載藍色', move=(0, 76), window=self.sha1list, parent=self.content_widget
        )
        self.sidebar_4 = Sidebar(
            '正在上傳', '上傳', '上傳藍色', move=(0, 114), window=self.uploadlist, parent=self.content_widget
        )
        self.sidebar_5 = Sidebar(
            'Aria2', '黑色aria2', '藍色aria2', move=(0, 152), window=self.aria2list, parent=self.content_widget
        )
        self.sidebar_6: Sidebar = Sidebar(
            '傳輸完成', '傳輸完成', '傳輸完成藍色', move=(0, 190), window=self.endlist, parent=self.content_widget
        )
        self.sidebar_7: Sidebar = Sidebar(
            '離線下載', '傳輸完成', '傳輸完成藍色', move=(0, 228), window=self.offlinelist, parent=self.content_widget
        )
        self.btngroup.addButton(self.sidebar_1, 1)
        self.btngroup.addButton(self.sidebar_2, 2)
        self.btngroup.addButton(self.sidebar_3, 3)
        self.btngroup.addButton(self.sidebar_5, 5)
        self.btngroup.addButton(self.sidebar_4, 4)
        self.btngroup.addButton(self.sidebar_6, 6)
        self.btngroup.addButton(self.sidebar_7, 7)
        # 設定預設瀏覽窗口
        self.sidebar_1.click()
        # 新增瀏覽視窗標題
        self.listdirectory.title_add('名稱', 400, 200)
        self.listdirectory.title_add(' 修改時間', 120, 120)
        self.listdirectory.title_add(' 大小', 85, 85)
        self.listdirectory.title_add(' 所在目錄', least=80)
        # 設定 所在目錄 標題 隱藏
        self.listdirectory.set_title_visible(' 所在目錄', False)
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
        self.listdirectory.pgon_connect(self.on_page)
        # 設定右鍵回調
        self.listdirectory.menu_callback = self.menu_callback
        # 設定上傳回調
        self.mylistdirectory.upload.clicked.connect(lambda: create_task(self.get_enter('上傳檔案')))
        # 設定離線下載回調
        self.mylistdirectory.offline.clicked.connect(lambda: create_task(self.get_enter('離線下載')))
        # 設定sha1上傳回調
        self.mylistdirectory.sha1.clicked.connect(lambda: create_task(self.get_enter('sha1')))
        # 設定 text 下載 右鍵
        self.listdirectory.text_menu_click_connect(
            '下載', lambda: create_task(self.get_download('download'))
        )
        # 設定 text 刪除 右鍵
        self.listdirectory.text_menu_click_connect(
            '刪除', lambda: create_task(self.get_enter('刪除'))
        )
        # 設定 text 重新命名 右鍵
        self.listdirectory.text_menu_click_connect(
            '重新命名', lambda: create_task(self.get_enter('重新命名'))
        )
        # 設定 text 複製 右鍵
        self.listdirectory.text_menu_click_connect('複製', self.copy)
        # 設定 text 剪下 右鍵
        self.listdirectory.text_menu_click_connect('剪下', self.cut)
        # 設定背景 新增資料夾 右鍵
        self.listdirectory.backdrop_menu_click_connect('新建資料夾', lambda: create_task(self.get_enter('新建資料夾')))
        # 設定 text 移動 右鍵
        self.listdirectory.text_menu_click_connect('移動', lambda: create_task(self.get_enter('移動檔案')))
        self.listdirectory.backdrop_menu_click_connect('qqq', lambda: self.z.zzz(self))
        # self.listdirectory.text_menu_click_connect('www', lambda: self.z.hide())

        # 設定背景 貼上 右鍵
        self.listdirectory.backdrop_menu_click_connect(
            '貼上', lambda: create_task(self.network(
                self.self_path_list, action=lambda: create_task(self.paste(self.self_path_list))
            )), mode=False
        )

        self.mprocess = Process(target=Mprocess, args=(self._state, self.lock, self.wait, self.waitlock, self.closes,
                                                       self.directory, self.config,))
        self.mprocess.daemon = True
        self.mprocess.start()

        # 允許拖曳文件
        self.setAcceptDrops(True)

        self.resize(800, 400)

        create_task(self.network('0'))

        if exists('state.json'):
            with open('state.json', 'r', encoding='utf-8') as f:
                output = json.load(f)
            for out in output.items():
                state = out[1]
                action = out[0][0]
                if action == '0':
                    self.downloadlist.add(state, value=False)
                elif action == '1':
                    self.downloadlist.folder_add(state, value=False)
                elif action == '2':
                    self.aria2list.add(state, value=False)
                elif action == '3':
                    self.aria2list.folder_add(state, value=False)
                elif action == '4':
                    self.sha1list.add(state, value=False)
                elif action == '5':
                    self.sha1list.folder_add(state, value=False)
                elif action == '6':
                    self.uploadlist.add(state, value=False)
                elif action == '7':
                    self.uploadlist.sha1_add(state, value=False)
            remove('state.json')

    def qq(self):
        print(QFileDialog.getOpenFileNames())

    # 頁數回調
    def setpage(self, page: int) -> None:
        cid = self.self_path_list
        if page not in self.allpath[cid]['data'] or self.allpath[cid]['refresh'] or self.listdirectory.textall == 0:
            create_task(self.network(cid=cid, page=page, add=False))

    # 網路
    async def network(self, cid: str, page: int = 1, action: Optional[Callable] = None, add: bool = True) -> None:
        # 瀏覽目錄清空
        self.listdirectory.directory_cls()
        # 顯示等待動畫
        self.listdirectory.set_load_visible(True)
        # 清空點擊
        self.listdirectory.cls_click()
        # 禁止操作
        self.prohibit(False)
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

        # 查看 cid 是否不在 所有介面的頁數資料
        if cid not in self.listdirectory.savecontents:
            # 如果不再 則新增 新窗口
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
        # 恢復操作
        self.prohibit(True)

    # 禁止操作
    def prohibit(self, mode: bool) -> None:
        # 是否禁止 搜索欄
        self.listdirectory.directorycontainer.setEnabled(mode)
        # 是否禁止 頁數欄
        self.listdirectory.quantity.pageico.setEnabled(mode)
        # 查看是否顯示 背景新建資料夾
        self.listdirectory.set_backdrop_menu_visible('新建資料夾', mode)

    def settext(self, sidebar: Sidebar, index: int) -> None:
        if index != 0:
            sidebar.index.setText(f'({index})')
            sidebar.index.adjustSize()
        else:
            sidebar.index.setText('')

    # 下載
    async def get_download(self, action: str) -> None:
        data = self.listdirectory.extra()
        for _data in [data] if isinstance(data, dict) else data:
            if _data['category'] != '0':
                if action == 'download':
                    self.downloadlist.add(_data)
                elif action == 'aria2':
                    _data['path'] = await self.get_aria2_path()
                    self.aria2list.add(_data)
                elif action == 'sha1':
                    self.sha1list.add(_data)
            else:
                if action == 'download':
                    self.downloadlist.folder_add(_data)
                elif action == 'aria2':
                    _data['path'] = await self.get_aria2_path()
                    self.aria2list.folder_add(_data)
                elif action == 'sha1':
                    _data['dir'] = _data['name']
                    self.sha1list.folder_add(_data)

    # 下載 資料夾 獲取資料
    async def getfolder(self, cid: str) -> tuple[bool, Union[dict[str, dict[str, any]], str]]:
        # 查看是否有 cid and 是否需要刷新
        if cid in self.allpath and self.allpath[cid]['refresh']:
            # 刪除 cid
            del self.allpath[cid]
            # 查看是否已經有資料新增
            if cid in self.listdirectory.savecontents:
                # 如果以新增 則刪除
                del self.listdirectory.savecontents[cid]
        # index 初始化
        index = 0
        while cid not in self.allpath or index < self.allpath[cid]['page']:
            result = await self.refresh(cid, index, state=False)
            if result is False or result == '0':
                return False, '資料夾不存在' if result == '0' else '獲取資料夾資料失敗'
            index += 1
        return True, self.allpath[cid]['index']

    # 獲取 aria2 下載路徑
    async def get_aria2_path(self) -> Union[str, bool]:
        data = {
            'jsonrpc': '2.0',
            'id': 'qwer',
            'method': 'aria2.getGlobalOption',
        }
        response = await srequests.async_post(url=self.config['aria2-rpc']['rpc_url'], json=data)
        if response.status_code == 200:
            return response.json()['result']['dir']
        else:
            return False

    # 搜索
    @error()
    async def search(self, cid: str, page: int) -> bool:
        self.listdirectory.lineEdit.setText('')
        _cid, _, name = re.search('搜索-(.+)-(.+)-(.+)', cid).groups()
        result = await self.directory.search(
            name, _cid,
            (page - 1) * self.listdirectory.pagemax, self.listdirectory.pagemax
        )
        if result:
            # 格式化115數據
            self.dumps(result, cid, page)
            return True
        return False

    # 刷新目錄
    @error()
    async def refresh(self, cid: str, page: int) -> Union[str, bool]:
        result = await self.directory.path(cid, (page - 1) * self.listdirectory.pagemax, self.listdirectory.pagemax)
        if result:
            if cid != str(result['cid']):
                return '0'
            # 格式化115數據
            self.dumps(result, cid, page)
            return True
        return False

    # 添加到窗口列表
    def add(self, cid: str, page: int) -> None:
        # 查看 上一頁 是否可以顯示可用
        if len(self.up_page_list) != 1 and not self.listdirectory.get_pgup():
            # 設定 上一頁按鈕 成可用
            self.listdirectory.set_pgup(True)

        # 添加瀏覽目錄
        for _path in self.allpath[cid]['path']:
            self.listdirectory.directory_add(_path[0], data=_path[1])

        if cid[0:3] == '搜索-' and ' 所在目錄' not in self.listdirectory.titlelist.text():
            self.listdirectory.set_title_visible(' 所在目錄', True)
        elif cid[0:3] != '搜索-' and ' 所在目錄' in self.listdirectory.titlelist.text():
            self.listdirectory.set_title_visible(' 所在目錄', False)

        # 查看 目前目錄是否一樣 and 查看text 資料是否一樣
        if self.self_path_list == cid and self.listdirectory.textsave == self.allpath[cid]['data'][page]:
            # 如果都一樣 退出
            return
        # 查看目前目錄 是否變化
        elif self.self_path_list != cid:
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
    def on_page(self) -> None:
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

    # 格式化115數據
    def dumps(self, items: dict, cid: str, page: int) -> None:
        def _getpath(__cid):
            return lambda: create_task(self.network(__cid))

        index: dict[str, dict[str, any]] = {}
        textsavelist: list[TextSave, ...] = []
        for data in items['data']:
            textsave: TextSave = TextSave(text={}, data=None, ico=None, leftclick=None, doubleclick=None)
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
            textsave['text'] = {
                '名稱': text,
                ' 修改時間': MyTextSave(text=_Time, leftclick=None, color=None),
                ' 大小': MyTextSave(text='-' if size == '0' else pybyte(int(size)), leftclick=None, color=None),
            }
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
            # 查看是否有所在目錄
            if 'dp' in data:
                pid = textsave['data']['pid']
                textsave['text'][' 所在目錄'] = MyTextSave(
                    text=data['dp'], leftclick=[_getpath(pid)], color=((0, 0, 0), (6, 168, 255))
                )
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

    # 禁止操作
    def setenabled(self, enabled: bool) -> None:
        # 是否禁止 搜索欄
        self.listdirectory.directorycontainer.setEnabled(not enabled)
        # 是否禁止 頁數欄
        self.listdirectory.quantity.pageico.setEnabled(not enabled)
        # 設定是否隱藏 新增資料夾 背景右鍵
        self.listdirectory.set_backdrop_menu_visible('新建資料夾', enabled)

    # 獲取輸入
    async def get_enter(self, action: str) -> None:
        if action == '新建資料夾' and self.self_path_list[0:3] != '搜索-':
            if name := await myenter('新建資料夾', '新名稱'):
                await self.network(
                    self.self_path_list, page=self.listdirectory.quantity.page,
                    action=lambda: create_task(self.add_folder(self.self_path_list, name))
                )
        elif action == '重新命名':
            if name := await myenter('重新命名', '新名稱'):
                cid = self.listdirectory.currentclick[0].data['cid']
                await self.network(self.self_path_list, page=self.listdirectory.quantity.page,
                                   action=lambda: create_task(self.rename(name, cid))
                                   )
        elif action == '刪除':
            if await myerror('刪除', '請問是否刪除'):
                currentclick = self.listdirectory.currentclick.copy()
                await self.network(self.self_path_list, action=lambda: create_task(self.delete(currentclick)))
        elif action == '移動檔案':
            if _cid := await self.folderlist.stop('打開要移動的目標文件夾', '移動到這裡', self):
                cid = []
                data = self.listdirectory.extra()
                for _data in [data] if isinstance(data, dict) else data:
                    cid.append(_data['cid'])
                await self.network(self.self_path_list, action=lambda: create_task(self.file_move(_cid[0], cid)))
            self.activateWindow()
        elif action == '離線下載':
            await offline(self.directory, self.folderlist)
            self.activateWindow()
        elif action == 'sha1' and self.self_path_list[0:3] != '搜索-':
            path = self.allpath[self.self_path_list]["path"][-1][0]
            if _data := await sha1save(self.self_path_list, path, self.folderlist):
                for sha1 in re.findall('115://(.+)', _data[1]):
                    data = {'sha1': sha1, 'cid': _data[0]}
                    self.uploadlist.sha1_add(data=data)
        elif action == '上傳檔案' and self.self_path_list[0:3] != '搜索-':
            self.upload(await myfiledialog(self))

    # 複製
    def copy(self) -> None:
        self._copy.clear()
        self._cut.clear()
        self._cut_cid = None
        self.listdirectory.set_backdrop_menu_visible('貼上', True)
        data = self.listdirectory.extra()
        for _data in [data] if isinstance(data, dict) else data:
            self._copy.append(_data['cid'])

    # 剪下
    def cut(self) -> None:
        self._copy.clear()
        self._cut.clear()
        self._cut_cid = self.self_path_list
        self.listdirectory.set_backdrop_menu_visible('貼上', True)
        data = self.listdirectory.extra()
        for _data in [data] if isinstance(data, dict) else data:
            self._cut.append(_data['cid'])

    # 貼上
    @error()
    async def paste(self, allcid: str) -> bool:
        if self._copy:
            result = await self.directory.paste(self._copy, allcid)
            if result:
                self.listdirectory.set_backdrop_menu_visible('貼上', False)
                self._copy.clear()
            return True
        if self._cut:
            result = await self.directory.move(self._cut, allcid)
            if result:
                self.listdirectory.set_backdrop_menu_visible('貼上', False)
                self._cut.clear()
                self.allpath[self._cut_cid]['refresh'] = True
                self._cut_cid = None
            return True
        return False

    # 刪除
    @error()
    async def delete(self, currentclick: list[Text, ...]) -> bool:
        allcid: list[str, ...] = []
        if len(currentclick) != 1:
            for text in currentclick:
                allcid.append(text.data['cid'])
        else:
            allcid = currentclick[0].data['cid']
        result = await self.directory.delete(allcid)
        # 刪除完畢後如果是資料夾檢查是否有後續
        if result:
            for text in currentclick:
                cid = text.data['cid']
                if cid in self.allpath:
                    pid = text.data['pid']
                    if pid in self.allpath:
                        self.allpath[pid]['refresh'] = True
                    if cid in self.up_page_list:
                        self.up_page_list.remove(cid)
                    if cid in self.on_page_list:
                        self.on_page_list.remove(cid)
                    del self.allpath[cid]
                    # 查看是否已經有資料新增
                    if cid in self.listdirectory.savecontents:
                        # 如果以新增 則刪除
                        del self.listdirectory.savecontents[cid]
            return True
        return False

    # 移動檔案
    @error()
    async def file_move(self, move_cid: str, file_cid: str) -> bool:
        result = await self.directory.move(file_cid, move_cid)
        if result:
            if move_cid in self.allpath:
                self.allpath[move_cid]['refresh'] = True
            return True
        return result

    # 新建資料夾
    @error()
    async def add_folder(self, pid: str, name: str) -> bool:
        result = await self.directory.add_folder(pid, name)
        if result:
            self.allpath[pid]['refresh'] = True
            self.allpath[pid]['index'][name] = {
                'name': name,
                'category': 0,
                'cid': str(result['cid']),
                'pid': pid,
            }
            return True
        return False

    # 搜索資料夾 如果沒有則創建資料夾
    async def search_add_folder(self, cid: str, names: str) -> AsyncIterable[dict[str, str]]:
        for name in names.split('\\'):
            if not name:
                break
            task = None
            index = 1
            while 1:
                if cid in self.allpath and name in self.allpath[cid]['index']:
                    cid = self.allpath[cid]['index'][name]['cid']
                    break
                elif (cid, name) not in self.task and cid in self.allpath and index in self.allpath[cid]['data'] \
                        and (self.allpath[cid]['count'] == 0
                             or index == self.allpath[cid]['page']
                             or self.allpath[cid]['data'][index][-1]['data']['category'] == '1'
                             ):
                    task = create_task(self.add_folder(cid, name))
                    task.set_name('創建資料夾失敗')
                    task.add_done_callback(lambda _task: self.task. pop((cid, name)))
                    self.task[(cid, name)] = task
                elif cid in self.allpath and index in self.allpath[cid]['data'] \
                        and index != self.allpath[cid]['page']:
                    if (index := index + 1) in self.allpath[cid]['data']:
                        continue
                elif (cid, name) not in self.task and (cid, index) not in self.task \
                        and (cid in self.allpath and name not in self.allpath[cid]['index']
                             or cid not in self.allpath):
                    task = create_task(self.refresh(cid, index, state=False))
                    task.set_name('獲取資料夾資料失敗')
                    task.add_done_callback(lambda _task: self.task.pop((cid, index)))
                    self.task[(cid, index)] = task
                elif (cid, name) in self.task:
                    task = self.task[(cid, name)]
                elif (cid, index) in self.task:
                    task = self.task[(cid, index)]
                if task:
                    if task.get_name() == '創建資料夾失敗':
                        yield {'state': 'text', 'result': '創建資料夾中'}
                    result = await task
                    if result is False or result == '0':
                        yield {'state': 'error', 'result': '資料夾不存在' if result == '0' else task.get_name()}
                    task = None
        yield {'state': 'end', 'result': cid}

    # 分析上傳路徑
    def upload(self, paths: list[str, ...]) -> None:
        for path in paths:
            # 查看是否是資料夾
            if isdir(path):
                # 獲取資料夾所在目錄
                path_dir = re.search('(.+\\\\).+$', path)[1]
                # 獲取路徑下的 所有 檔案 資料夾
                for root, dirs, files in walk(path):
                    # 查看資料夾下面是否有檔案
                    if files:
                        # 獲取檔案
                        for file in files:
                            # 設定資料
                            data = {
                                'name': file,
                                'ico': get_ico(splitext(file)[1]),
                                'dir': root.replace(path_dir, ''),
                                'path': join(root, file),
                                'cid': self.self_path_list
                            }
                            if self.btngroup.checkedId() == 1:
                                # 開始上傳
                                self.uploadlist.add(data)
                            else:
                                # sha1本地添加
                                self.sha1list.path_add(data)
                    # 查看是否是空資料夾
                    elif self.btngroup.checkedId() == 1 and files == [] and dirs == []:
                        _path = Path(root)
                        data = {
                            'dir': root.replace(path_dir, ''),
                            'cid': self.self_path_list,
                            'name': _path.name
                        }
                        # 開始上傳
                        self.uploadlist.new_folder_add(data)
            # 查看是否是檔案
            elif isfile(path):
                _, name = split(path)
                ico = get_ico(splitext(name)[1])
                data = {
                    'name': name,
                    'ico': ico,
                    'dir': None,
                    'path': path,
                    'cid': self.self_path_list
                }
                if self.btngroup.checkedId() == 1:
                    self.uploadlist.add(data)
                else:
                    self.sha1list.path_add(data)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        Window.resizeEvent(self, event)
        self.child_window.setGeometry(165, 0, self.content_widget.width(), self.content_widget.height())
        self.mylistdirectory.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.downloadlist.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.uploadlist.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.sha1list.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.aria2list.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.offlinelist.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.endlist.resize(self.content_widget.width() - 165, self.content_widget.height())

    async def wait_close(self) -> None:
        while 1:
            if not self.mprocess.is_alive():
                self.close()
                return
            await sleep(0.1)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.closes.value:
            if self._state:
                with open('state.json', 'w') as f:
                    json.dump(dict(self._state), f)
            event.accept()
        else:
            self.closes.value = 1
            create_task(self.wait_close())
            event.ignore()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        # 如果是在首頁則允許拖曳
        if (self.btngroup.checkedId() == 1 and self.self_path_list[0:3] != '搜索-') or self.btngroup.checkedId() == 3:
            # 允許拖曳
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        file_path = event.mimeData().text()
        file_path = getpath(file_path.replace('file:///', '')).strip()
        if (self.btngroup.checkedId() == 1 and self.self_path_list[0:3] != '搜索-') or self.btngroup.checkedId() == 3:
            self.upload(file_path.split('\n'))

    # 窗口變化事件  最大化 還原
    def window_change(self, value) -> None:
        # 根據目前窗口狀態 來決定是否 最大化 還原
        self.titlelabel.setico()


class MyListDirectory(QFrame):
    def __init__(self, parent: Fake115GUI) -> None:
        super().__init__(parent.child_window)
        # 設置上傳按鈕
        self.upload: MyQLabel = MyQLabel('上傳', (10, 8, 111, 41), fontsize=16, parent=self)
        # 設置sha1按鈕
        self.sha1: MyQLabel = MyQLabel('上傳sha1', (130, 8, 111, 41), fontsize=16, parent=self)
        # 設置離線按鈕
        self.offline: MyQLabel = MyQLabel('離線下載', (250, 8, 111, 41), fontsize=16, parent=self)
        # 設置瀏覽窗口
        self.listdirectory: ListDirectory = ListDirectory(True, self)
        # 設置 背景空白 左側邊框
        self.setStyleSheet('MyListDirectory{background-color: rgb(255, 255, 255);'
                           'border-style:solid; border-left-width:1px; border-color:rgba(200, 200, 200, 125)}')

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.listdirectory.setGeometry(1, 55, self.width() - 1, self.height() - 55)


if __name__ == '__main__':
    freeze_support()
    app = QApplication(argv)
    loop = QEventLoop(app)
    set_event_loop(loop)
    ex = Fake115GUI()
    ex.show()
    with loop:
        loop.run_forever()
