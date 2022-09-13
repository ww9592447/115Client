from module import QApplication, QWidget, split, set_event_loop, isfile, backdrop, MyQLabel, QFrame, Sidebar\
    , create_task, time, QLabel, picture, pybyte, MyIco, Window, sleep, splitext, srequests, getpath,\
    isdir, walk, join, get_ico, QMetaMethod, remove, exists, ListDirectory, math, Path
from multiprocessing import Process, Manager, Lock, Value, freeze_support
from hints import error, myerror, myenter, offline, folderlist, sha1save, myfiledialog
from configparser import ConfigParser
from API.directory import Directory
from sys import argv
from qasync import QEventLoop
from QList.endlist import EndList
from QList.downloadlist import DownloadList
from QList.uploadlist import UploadList
from QList.sha1list import Sha1List
from QList.offlinelist import Offlinelist
from QList.aria2list import Aria2List
from mprocess import Mprocess
import re
import json


def getsignal(self, name):
    ometaobj = self.metaObject()
    for i in range(ometaobj.methodCount()):
        ometamethod = ometaobj.method(i)
        if not ometamethod.isValid():
            continue
        if ometamethod.methodType() == QMetaMethod.Signal and ometamethod.name() == name:
            return self.isSignalConnected(ometamethod)
    return None


class TitleLabel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.setPalette(backdrop('空白'))
        self.label_1 = QLabel(self)
        self.label_1.setPixmap(picture('115ico'))
        self.label_1.setGeometry(20, 6, 30, 30)
        self.label_2 = QLabel(self)
        self.label_2.setPixmap(picture('115text'))
        self.label_2.setGeometry(58, 8, 76, 29)
        # 副標題
        self.titleLabel = QWidget(self)
        # 最小化按鈕
        self.minimize = MyIco('黑色縮小', '藍色縮小', state=True, coordinate=(17, 6, 12, 12),
                              click=parent.parent().showMinimized, parent=self.titleLabel)
        # 最大化按鈕
        self.maximize = MyIco('黑色最大化', '藍色最大化', state=True, coordinate=(46, 6, 12, 12),
                              click=lambda: self.replace(True), parent=self.titleLabel)
        # 關閉按鈕
        self.closure = MyIco('黑色關閉', '藍色關閉', state=True, coordinate=(75, 6, 12, 12),
                             click=parent.parent().close, parent=self.titleLabel)
        # 還原大小按鈕
        self.reduction = MyIco('黑色還原', '藍色還原', state=True, coordinate=(46, 6, 12, 12),
                               click=lambda: self.replace(False), parent=self.titleLabel)
        # 初始化還原大小隱藏
        self.reduction.hide()
        # 設定標題下方邊框
        self.setStyleSheet('TitleLabel{border-style:solid; border-bottom-width:1px;'
                           'border-color:rgba(200, 200, 200, 125)}')
        # 邊框
        self.frame = QFrame(self.titleLabel)
        self.frame.setGeometry(0, 3, 1, 19)
        self.frame.setStyleSheet('background-color: rgba(200, 200, 200, 125)')

    # 根據目前窗口狀態 來決定是否 最大化 還原
    def setico(self):
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

    def replace(self, _bool):
        if _bool:
            self.parent().parent().showMaximized()
        else:
            self.parent().parent().showNormal()

    def resizeEvent(self, e):
        self.titleLabel.move(self.width() - 104, 10)


class MyListDirectory(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.setPalette(backdrop('空白'))
        self.upload = MyQLabel('上傳', (10, 8, 111, 41), fontsize=16, parent=self)
        self.sha1 = MyQLabel('上傳sha1', (130, 8, 111, 41), fontsize=16, parent=self)
        self.offline = MyQLabel('離線下載', (250, 8, 111, 41), fontsize=16, parent=self)
        self.listdirectory = ListDirectory(True, self)
        # 設置 背景空白 左側邊框
        self.setStyleSheet('MyListDirectory{background-color: rgb(255, 255, 255);'
                           'border-style:solid; border-left-width:1px; border-color:rgba(200, 200, 200, 125)}')

    def resizeEvent(self, e):
        self.listdirectory.setGeometry(1, 55, self.width() - 1, self.height() - 55)


class Fake115GUI(Window):
    def __init__(self):
        super().__init__(TitleLabel, 44)
        # 初始化設定
        self.config = ConfigParser()
        self.config.read('config.ini', encoding='utf-8')
        # 允許拖曳文件
        self.setAcceptDrops(True)
        # 所有目錄資料
        self.allpath = {}
        # 目前所在目錄
        self.self_path_list = '0'
        # 目前搜索cid
        self.search_cid = None
        # 上一頁目錄順序
        self.up_page_list = []
        # 下一頁目錄順序
        self.under_page_list = []
        # 待複製列表
        self._copy = []
        # 待剪下列表
        self._cut = []
        # 原本剪下目錄cid
        self._cut_cid = None
        # 添加中任務
        self.add_task = None
        # 目前側框
        self.sidebar = 1
        # 共用數據
        self._state = Manager().dict()
        # 共用數據鎖
        self.lock = Lock()
        # 傳送列表
        self.wait = Manager().list()
        # 傳送列表鎖
        self.waitlock = Lock()
        # 關閉信號
        self.closes = Value('i', 0)
        # 目錄操作
        self.directory = Directory(self.config)
        # 所有子窗口
        self.child_window = QWidget(self.content_widget)
        # 按鈕+瀏覽窗口組合
        self.mylistdirectory = MyListDirectory(parent=self.child_window)
        # 加入傳輸完畢視窗
        self.endlist = EndList(lambda: self.sidebar_switch(1, self.mylistdirectory), self.network, self.child_window)
        # 加入下載視窗
        self.downloadlist = DownloadList(
            self._state, self.allpath, self.lock, self.wait, self.waitlock,
            self.config, self.endlist, self.refresh, parent=self.child_window
        )
        # 加入aria2視窗
        self.aria2list = Aria2List(
            self._state, self.allpath, self.lock, self.wait, self.waitlock,
            self.config, self.endlist, self.refresh, parent=self.child_window
        )
        # 加入上傳視窗
        self.uploadlist = UploadList(
            self._state, self.allpath, self.lock, self.wait, self.waitlock,
            self.config, self.endlist, self.refresh, self.add_folder, parent=self.child_window
        )
        # 加入sha1視窗
        self.sha1list = Sha1List(
            self._state, self.allpath, self.lock, self.wait, self.waitlock,
            self.refresh, parent=self.child_window
        )
        # 加入離線視窗
        self.offlinelist = Offlinelist(self.directory, lambda: self.sidebar_switch(1, self.mylistdirectory),
                                       self.network, parent=self.child_window)
        # 加入瀏覽視窗
        self.listdirectory = self.mylistdirectory.listdirectory
        # 首頁加入左側瀏覽窗口
        self.sidebar_1 = Sidebar('首頁', '黑色首頁', '藍色首頁', move=(0, 0),
                                 click=lambda: self.sidebar_switch(1, self.mylistdirectory), parent=self.content_widget)
        self.sidebar_2 = Sidebar('正在下載', '下載', '下載藍色', move=(0, 38),
                                 click=lambda: self.sidebar_switch(2, self.downloadlist), parent=self.content_widget)
        self.sidebar_3 = Sidebar('sha1', '下載', '下載藍色', move=(0, 76),
                                 click=lambda: self.sidebar_switch(3, self.sha1list), parent=self.content_widget)
        self.sidebar_4 = Sidebar('正在上傳', '上傳', '上傳藍色', move=(0, 114),
                                 click=lambda: self.sidebar_switch(4, self.uploadlist), parent=self.content_widget)
        self.sidebar_5 = Sidebar('Aria2', '黑色aria2', '藍色aria2', move=(0, 152),
                                 click=lambda: self.sidebar_switch(5, self.aria2list), parent=self.content_widget)
        self.sidebar_6 = Sidebar('傳輸完成', '傳輸完成', '傳輸完成藍色', move=(0, 190),
                                 click=lambda: self.sidebar_switch(6, self.endlist), parent=self.content_widget)
        self.sidebar_7 = Sidebar('離線下載', '傳輸完成', '傳輸完成藍色', move=(0, 228),
                                 click=lambda: self.sidebar_switch(7, self.offlinelist), parent=self.content_widget)

        # 設定預設瀏覽窗口
        self.sidebar_switch(1, self.mylistdirectory)
        # 新增瀏覽視窗標題
        self.listdirectory.title_add('名稱', 400, 200)
        self.listdirectory.title_add(' 修改時間', 120, 120)
        self.listdirectory.title_add(' 大小', 85, 85)
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
        # 設定搜索全部回調
        self.listdirectory.set_search_all_connect(self._set_search_all_callback)
        # 設定搜索名稱回調
        self.listdirectory.set_search_name_connect(self._set_search_name_callback)
        # 設定背景顏色
        self.content_widget.setStyleSheet('#content_widget{background-color: rgb(249, 250, 251)}')
        # 設定 texts 下載 右鍵
        self.listdirectory.texts_menu_click_connect(
            '下載', lambda: create_task(self.get_download('download'))
        )

        # 設定 texts 刪除 右鍵
        self.listdirectory.texts_menu_click_connect(
            '刪除', lambda: create_task(self.get_enter(action='刪除'))
        )
        # 設定 texts 重新命名 右鍵
        self.listdirectory.texts_menu_click_connect(
            '重新命名', lambda: lambda: create_task(self.get_enter(action='重新命名'))
        )
        # 設定 texts 複製 右鍵
        self.listdirectory.texts_menu_click_connect('複製', self.copy)
        # 設定 texts 剪下 右鍵
        self.listdirectory.texts_menu_click_connect('剪下', self.cut)
        # 設定 texts 移動 右鍵
        self.listdirectory.texts_menu_click_connect('移動', lambda: create_task(self.get_enter('移動檔案')))
        # 設定 texts sha1提取 右鍵
        self.listdirectory.texts_menu_click_connect(
            'sha1提取', lambda: create_task(self.get_download('sha1'))
        )
        # 設定 texts aria2下載 右鍵
        self.listdirectory.texts_menu_click_connect(
            'aria2 rpc', lambda: create_task(self.get_download('aria2'))
        )
        # 設定背景 貼上 右鍵
        self.listdirectory.backdrop_menu_click_connect(
            '貼上', lambda: create_task(self.network(
                self.self_path_list, action=lambda: create_task(self.paste(self.self_path_list))
            )), mode=False
        )
        # 設定背景 新增資料夾 右鍵
        self.listdirectory.backdrop_menu_click_connect('新建資料夾', lambda: create_task(self.get_enter('新建資料夾')))
        # 設定上傳回調
        self.mylistdirectory.upload.clicked.connect(lambda: create_task(self.get_enter('上傳檔案')))
        # 設定離線下載回調
        self.mylistdirectory.offline.clicked.connect(lambda: create_task(self.get_enter('離線下載')))
        # 設定sha1上傳回調
        self.mylistdirectory.sha1.clicked.connect(lambda: create_task(self.get_enter('sha1')))

        self.mprocess = Process(target=Mprocess, args=(self._state, self.lock, self.wait, self.waitlock, self.closes,
                                                       self.directory, self.config,))
        self.mprocess.daemon = True
        self.mprocess.start()

        self.resize(800, 400)
        create_task(self.network(cid='0', pages=True))

        if exists('state.json'):
            with open('state.json', 'r', encoding='utf-8') as f:
                output = json.load(f)
            for out in output.items():
                state = {out[0]: out[1]}
                action = out[0][0]
                if action == '0':
                    self.downloadlist.add(state=state)
                elif action == '1':
                    self.downloadlist.folder_add(state=state)
                elif action == '2':
                    self.aria2list.add(state=state)
                elif action == '3':
                    self.aria2list.folder_add(state=state)
                elif action == '4':
                    self.sha1list.add(state=state)
                elif action == '5':
                    self.sha1list.folder_add(state=state)
                elif action == '6':
                    create_task(self.uploadlist.add(state=state))
                elif action == '7':
                    self.uploadlist.sha1_add(state=state)
            remove('state.json')


    async def network(self, cid, index=0, action=None, pages=None):
        # 重新設定目前窗口 垂直滾動條歸0
        self.listdirectory.scrollarea.verticalcontents.setvalue(0)
        # 重新設定目前窗口 橫向滾動條歸0
        self.listdirectory.scrollarea.hrizontalcontents.setvalue(0)
        # 瀏覽目錄清空
        self.listdirectory.directory_cls()
        # 統計數字隱藏
        self.listdirectory.quantity.alltext.hide()
        # 內容隱藏
        self.listdirectory.content_show()
        # 顯示等待動畫
        self.listdirectory.load_show()
        # 禁止操作
        self.prohibit(True)
        # 清空點擊
        self.listdirectory.cls_click()

        # 查看cid是否是搜索
        if cid[0:3] == '搜索-':
            # 分割 cid 獲取資料
            search = re.search('搜索-(.+)-(.+)-(.+)', cid).groups()
            # 查看上一頁是不是搜索
            if self.self_path_list[0:3] != '搜索-':
                # 設定目前搜索 cid資料
                self.search_cid = search
                # 查看 搜索cid 是不是根目錄
                if self.search_cid[0] != '0':
                    # 設定搜索名稱按鈕
                    self.listdirectory.setname(self.search_cid[1])
            # 上一頁是搜索
            else:
                # 查看 搜索cid 是不是 根目錄 and 查看目前搜索名稱 是不是跟 上一頁 搜索名稱不一致
                if search[0] != '0' and search[1] != self.listdirectory.searchbutton.search_name.text():
                    # 重新設定搜索名稱按鈕
                    self.listdirectory.setname(search[1])
                # 搜索按鈕全部影藏
                self.listdirectory.searchbutton.hide()
        # 目前不是搜索 and 上一頁是搜索
        elif self.self_path_list[0:3] == '搜索-':
            # 搜索按鈕初始化
            self.listdirectory.searchbutton.hide_()

        # 查看 目前目錄是否發生變化
        if self.self_path_list != cid:
            # 查看上一頁是否是搜索
            if self.self_path_list[0:3] == '搜索-':
                # 如果是則把上一頁搜索設定成需要刷新
                self.allpath[self.self_path_list]['refresh'] = True
            if cid in self.allpath and index not in self.allpath[cid]:
                self.listdirectory.replace_contents(cid)
                if self.listdirectory.page != 0:
                    self.listdirectory.quantity.setpage(0, callback=False)
            # 設定目前所在目錄
            self.self_path_list = cid

        # 查看是否要新增 上一頁目錄
        if pages is True:
            # 下一頁目錄清空
            self.under_page_list = []
            # 下一頁按鈕 不可使用
            self.listdirectory.set_pgon(False)
            # 上一頁加入
            self.up_page_list.append(cid)

        result = True
        if action or (cid in self.allpath and self.allpath[cid]['refresh']):
            if action and await action() is False:
                result = False
            if result:
                # 刪除舊的容器
                self.listdirectory.delete_old_contents(cid)
                del self.allpath[cid]

        if result:
            if cid not in self.allpath or index not in self.allpath[cid] or pages is None\
                    or not self.allpath[cid][index]['add']:
                if cid not in self.allpath:
                    self.listdirectory.new_contents()
                if cid[0:3] == '搜索-':
                    await self.search(cid, index)
                elif cid in self.allpath and index in self.allpath[cid] and not self.allpath[cid][index]['add']:
                    pass
                else:
                    # 刷新目錄
                    if await create_task(self.refresh(cid, index)) == '0':
                        create_task(self.network(cid='0', pages=True))
                        return
                # 目錄添加到列表
                await create_task(self.add(cid, index, True))
            # 不需要刷新
            else:
                # 目錄添加到列表
                await create_task(self.add(cid, index, False))

        if cid[0:3] == '搜索-':
            self.listdirectory.searchbutton.show()
        # 可以操作
        self.prohibit(False)
        # 隱藏等待動畫
        self.listdirectory.load_hide()
        # 內容顯示
        self.listdirectory.content_hide()

    # 禁止操作
    def prohibit(self, mode):
        # 是否禁止 搜索欄
        self.listdirectory.directorycontainer.setEnabled(not mode)
        # 是否禁止 頁數欄
        self.listdirectory.quantity.pageico.setEnabled(not mode)
        if mode:
            # 隱藏背景右鍵
            self.listdirectory.backdrop_menu_hide('新建資料夾')
        else:
            # 顯示背景右鍵
            self.listdirectory.backdrop_menu_show('新建資料夾')

    # 下載
    async def get_download(self, action):
        data = self.listdirectory.extra()
        for _data in [data] if isinstance(data, dict) else data:
            if _data['category'] != '0':
                if action == 'download':
                    self.downloadlist.add(data=_data)
                elif action == 'aria2':
                    _data['path'] = await self.get_aria2_path()
                    self.aria2list.add(data=_data)
                elif action == 'sha1':
                    self.sha1list.add(data=_data)
            else:
                if action == 'download':
                    self.downloadlist.folder_add(data=_data)
                elif action == 'aria2':
                    _data['path'] = await self.get_aria2_path()
                    self.aria2list.folder_add(data=_data)
                elif action == 'sha1':
                    _data['dir'] = _data['name']
                    self.sha1list.folder_add(data=_data)

    # 獲取 aria2 下載路徑
    async def get_aria2_path(self):
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

    # 添加到窗口列表
    async def add(self, cid, index, value):
        # 獲取目錄相關資料
        text, data, ico, my_mode, text_mode, _, _, _ = self.allpath[cid][index].values()
        path = self.allpath[cid]['path']
        # 查看 上一頁 是否可以顯示可用
        if len(self.up_page_list) != 1 and not self.listdirectory.get_pgup():
            # 設定 上一頁按鈕 成可用
            self.listdirectory.set_pgup(True)
        if value and self.listdirectory.quantity.page == 0 and self.allpath[cid]['page'] != 0:
            self.listdirectory.page_advance(self.allpath[cid]['page'])

        # 查看是否需要手動添加
        if value:
            self.allpath[cid][index]['add'] = True
            if self.self_path_list[0:3] == '搜索-' and ' 所在目錄' not in self.listdirectory.alltitle:
                self.listdirectory.title_add(' 所在目錄', least=80)
            elif self.self_path_list[0:3] != '搜索-' and ' 所在目錄' in self.listdirectory.alltitle:
                self.listdirectory.delete_title(' 所在目錄')
            # 添加目錄到新的內容窗口
            await self.listdirectory.text_adds(
                text, index=index, icos=ico, datas=data, my_modes=my_mode, text_modes=text_mode
            )
            # 儲存目前的內容窗口
            self.listdirectory.save_contents(cid)
        else:
            # 更換舊的內容窗口資料
            self.listdirectory.replace_contents(cid)
        # 添加瀏覽目錄
        for _path in path:
            self.listdirectory.directory_add(_path[0], data=_path[1])

        _index = index if value else 0
        if self.listdirectory.page != _index and _index not in self.allpath[cid]['_page']:
            self.listdirectory.quantity.setpage(_index, callback=False)

    # 側邊框選擇
    def sidebar_switch(self, index, window):
        # 子窗口置頂
        window.raise_()
        # 上一個側邊框點擊隱藏
        getattr(self, f'sidebar_{self.sidebar}').select(False)
        # 目前側邊框顯示
        getattr(self, f'sidebar_{index}').select(True)
        # 紀錄目前側邊框
        self.sidebar = index

    # 獲取輸入
    async def get_enter(self, action):
        if action == '新建資料夾' and self.self_path_list[0:3] != '搜索-':
            if name := await myenter('新建資料夾', '新名稱'):
                await self.network(self.self_path_list, index=self.listdirectory.page,
                                   action=lambda: create_task(self.add_folder(self.self_path_list, name))
                                   )
        elif action == '重新命名':
            if name := await myenter('重新命名', '新名稱'):
                await self.network(self.self_path_list, index=self.listdirectory.page,
                                   action=lambda: create_task(self.rename(self.self_path_list, name))
                                   )
        elif action == '刪除':
            if await myerror('刪除', '請問是否刪除'):
                currentclick = self.listdirectory.now_all().copy()
                await self.network(self.self_path_list, action=lambda: create_task(self.delete(currentclick)))
        elif action == '移動檔案':
            if _cid := await folderlist('打開要移動的目標文件夾', '移動到這裡', self.directory):
                cid = []
                data = self.listdirectory.extra()
                for _data in [data] if isinstance(data, dict) else data:
                    cid.append(_data['cid'])
                await self.network(self.self_path_list, index=self.listdirectory.page,
                                   action=lambda: create_task(self.file_move(_cid[0], cid))
                                   )
            self.activateWindow()
        elif action == 'sha1' and self.self_path_list[0:3] != '搜索-':
            path = self.allpath[self.self_path_list]["path"][-1][0]
            if _data := await sha1save(self.self_path_list, path, self.directory):
                for sha1 in re.findall('115://(.+)', _data[1]):
                    data = {'sha1': sha1, 'cid': _data[0]}
                    create_task(self.uploadlist.sha1_add(data=data))
        elif action == '上傳檔案' and self.self_path_list[0:3] != '搜索-':
            paths = myfiledialog(self)
            for path in paths:
                if isdir(path):
                    for root, dirs, files in walk(path):
                        if files:
                            for file in files:
                                if (_path := root.replace(path, '')) != '':
                                    _path = getpath(_path)
                                data = {
                                    'dir': _path, 'path': getpath(join(root, file)), 'cid': self.self_path_list
                                }
                                create_task(self.uploadlist.add(data=data))
                        elif files == [] and dirs == []:
                            _dir = getpath(root.replace(path, ''), False).parts
                            data = {
                                'dir': '\\'.join(_dir[1:]),
                                'cid': self.self_path_list, 'name': getpath(root, False).name
                            }
                            create_task(self.uploadlist.new_folder_add(data=data))
                elif isfile(path):
                    data = {'dir': None, 'path': path, 'cid': self.self_path_list}
                    create_task(self.uploadlist.add(data=data))

        elif action == '離線下載':
            if result := await offline(self.directory):
                await self.directory.add_offline(result[0], result[1])
            self.activateWindow()

    # 搜索回調
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

    # 搜索名稱回調
    def _set_search_name_callback(self):
        cid = f'搜索-{self.search_cid[0]}-{self.search_cid[1]}-{self.search_cid[2]}'
        if cid in self.allpath:
            self.allpath[cid]['refresh'] = True
        create_task(self.network(cid, pages=False))

    # 搜索全部回調
    def _set_search_all_callback(self):
        cid = f'搜索-0-{self.search_cid[1]}-{self.search_cid[2]}'
        if cid in self.allpath:
            self.allpath[cid]['refresh'] = True
        create_task(self.network(cid, pages=False))

    # 頁數回調
    def setpage(self, index):
        cid = self.self_path_list
        if index not in self.allpath[cid] or self.allpath[cid]['refresh'] or\
                (index in self.allpath[cid] and not self.allpath[cid][index]['add']):
            create_task(self.network(cid=self.self_path_list, index=index))

    # 目錄點擊回調
    def directory_del(self, texts):
        create_task(self.network(cid=texts.data, pages=True))

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

    # 複製
    def copy(self):
        self._copy.clear()
        self._cut.clear()
        self._cut_cid = None
        self.listdirectory.backdrop_menu_show('貼上')
        data = self.listdirectory.extra()
        for _data in [data] if isinstance(data, dict) else data:
            self._copy.append(_data['cid'])

    # 剪下
    def cut(self):
        self._copy.clear()
        self._cut.clear()
        self._cut_cid = self.self_path_list
        self.listdirectory.backdrop_menu_show('貼上')
        data = self.listdirectory.extra()
        for _data in [data] if isinstance(data, dict) else data:
            self._cut.append(_data['cid'])

    # 重新整理
    async def reorganize(self):
        self.listdirectory.refresh_show()
        del self.allpath[self.self_path_list]
        create_task(self.network(cid=self.self_path_list, index=self.listdirectory.page))
        self.listdirectory.refresh_hide()

    # 分析115數據
    def dumps(self, cid, items, index):
        def _getpath(__cid):
            return lambda: create_task(self.network(__cid, pages=True))
        path = {cid: {index: {'text': [], 'data': [], 'ico': [], 'my_mode': [], 'text_mode': []
            , 'read': len(items['data']), 'folder_read': False, 'add': False}, 'path': [], 'folder': {}}}

        for data in items['data']:
            if 'te' in data:
                _time = data['te']
            else:
                _time = data['t'] if data['t'].isdigit() else int(
                    time.mktime(time.strptime(f"{data['t']}:0", "%Y-%m-%d %H:%M:%S")))
            _Time = time.strftime('%Y-%m-%d %H:%M', time.localtime(int(_time)))
            ico = get_ico(splitext(data['n'])[1] if 'fid' in data else '資料夾')
            size = data['s'] if 's' in data else '0'

            path[cid][index]['text'].append(
                {'名稱': data['n'], ' 修改時間': _Time,
                 ' 大小': '-' if size == '0' else pybyte(int(size))}
            )
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
            my_mode = {'doubleclick': [slot]} if ico == '資料夾' else None
            text_mode = {'名稱': {'leftclick': [slot], 'color': ((0, 0, 0), (6, 168, 255))}} if ico == '資料夾' else None
            if 'dp' in data:
                path[cid][index]['text'][-1].update({' 所在目錄': data['dp']})
                pid = path[cid][index]['data'][-1]['pid']
                if text_mode:
                    text_mode.update({' 所在目錄': {'leftclick': [_getpath(pid)], 'color': ((0, 0, 0), (6, 168, 255))}})
                else:
                    text_mode = {' 所在目錄': {'leftclick': [_getpath(pid)], 'color': ((0, 0, 0), (6, 168, 255))}}

            path[cid][index]['my_mode'].append(my_mode)
            path[cid][index]['text_mode'].append(text_mode)
            if 'fid' not in data:
                path[cid]['folder'][data['n']] = str(data['cid'])
            elif not path[cid][index]['folder_read']:
                path[cid][index]['folder_read'] = True

        if cid not in self.allpath:
            page = math.ceil(items['count'] / self.listdirectory.pagemax)
            _page = list(range(0, page))
            if _page:
                _page.remove(index)
            _path = {'refresh': False, 'count': items['count'], 'read': len(items['data']),
                     'page': page, '_page': _page,
                     'folder_read': len(items['data']) != len(path[cid]['folder']), '_read': 1}
            if 'path' in items:
                for __path in items['path']:
                    path[cid]['path'].append((__path['name'], str(__path['cid'])))
            # 搜索
            elif 'folder' in items:
                path[cid]['path'].append(('根目录', '0'))
                path[cid]['path'].append((f'搜尋-{self.search_cid[1]}', cid))
            path[cid].update(_path)
        return path

    # 刷新目錄
    @error()
    async def refresh(self, cid, index):
        result = await self.directory.path(cid, index * self.listdirectory.pagemax, self.listdirectory.pagemax)
        if result:
            if cid != str(result['cid']):
                return '0'
            if cid not in self.allpath:
                self.allpath.update(self.dumps(cid, result, index))

            else:
                _result = self.dumps(cid, result, index)
                self.allpath[cid][index] = _result[cid][index]
                self.allpath[cid][index]['folder_read'] = _result[cid][index]['folder_read']
                self.allpath[cid]['folder'].update(_result[cid]['folder'])
                self.allpath[cid]['read'] += _result[cid][index]['read']
                self.allpath[cid]['_page'].remove(index)
                if not self.allpath[cid]['folder_read'] and index == self.allpath[cid]['_read']:
                    _index = index
                    while 1:
                        self.allpath[cid]['_read'] += 1
                        if self.allpath[cid][_index]['folder_read']:
                            self.allpath[cid]['folder_read'] = True
                        if self.allpath[cid]['_read'] not in self.allpath[cid]:
                            break
                        _index += 1
            if len(self.allpath[cid]['folder']) == self.allpath[cid]['count']:
                self.allpath[cid]['folder_read'] = True
            if self.allpath[cid]['_page'] == [] and not self.allpath[cid]['folder_read']:
                page = math.ceil(self.allpath[cid]['count'] / self.listdirectory.pagemax)
                print('-------------------')
                print(cid, len(self.allpath[cid]['folder']), self.allpath[cid]['count'], index, page,
                      self.allpath[cid]['path'])
                self.allpath[cid]['folder_read'] = True
        return result

    # 搜索
    @error()
    async def search(self, cid, index):
        self.listdirectory.lineEdit.setText('')
        _cid, _, name = re.search('搜索-(.+)-(.+)-(.+)', cid).groups()
        result = await self.directory.search(
            name, _cid,
            index * self.listdirectory.pagemax, self.listdirectory.pagemax
        )
        if result:
            if cid not in self.allpath:
                _result = self.dumps(cid, result, index)
                self.allpath.update(_result)
            else:
                _result = self.dumps(cid, result, index)
                self.allpath[cid][index] = _result[cid][index]
                self.allpath[cid][index]['folder_read'] = _result[cid][index]['folder_read']
                self.allpath[cid]['folder'].update(_result[cid]['folder'])
                self.allpath[cid]['read'] += _result[cid][index]['read']
                self.allpath[cid]['_page'].remove(index)
        return result

    # 貼上
    @error()
    async def paste(self, cid):
        if self._copy:
            result = await self.directory.paste(self._copy, cid)
            if result:
                self.listdirectory.backdrop_menu_hide('貼上')
                self._copy.clear()
            return result
        if self._cut:
            result = await self.directory.move(self._cut, cid)
            if result:
                self.listdirectory.backdrop_menu_hide('貼上')
                self._cut.clear()
                self.allpath[self._cut_cid]['refresh'] = True
                self._cut_cid = None
            return result
        return False

    # 新建資料夾
    @error()
    async def add_folder(self, pid, name):
        return await self.directory.add_folder(pid, name)

    # 重新命名
    @error()
    async def rename(self, name, cid):
        return await self.directory.rename(name, cid)

    # 刪除
    @error()
    async def delete(self, currentclick):
        cid = []
        if len(currentclick) != 1:
            for texts in currentclick:
                cid.append(texts.data['cid'])
        else:
            cid = currentclick[0].data['cid']
        result = await self.directory.delete(cid)
        # 刪除完畢後如果是資料夾檢查是否有後續
        if result:
            for texts in currentclick:
                cid = texts.data['cid']
                if texts.data['cid'] in self.listdirectory.save:
                    pid = texts.data['pid']
                    if pid in self.listdirectory.save:
                        self.allpath[pid]['refresh'] = True
                    if cid in self.up_page_list:
                        self.up_page_list.remove(cid)
                    if cid in self.under_page_list:
                        self.under_page_list.remove(cid)
                    del self.allpath[cid]
                    self.listdirectory.delete_contents(cid)
        return result

    # 移動檔案
    @error()
    async def file_move(self, move_cid, file_cid):
        result = await self.directory.move(file_cid, move_cid)
        if result:
            if move_cid in self.allpath:
                self.allpath[move_cid]['refresh'] = True
        return result

    # 窗口變化事件  最大化 還原
    def window_change(self, value):
        # 根據目前窗口狀態 來決定是否 最大化 還原
        self.titlelabel.setico()

    def resizeEvent(self, event):
        Window.resizeEvent(self, event)
        self.child_window.setGeometry(165, 0, self.content_widget.width(), self.content_widget.height())
        self.mylistdirectory.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.downloadlist.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.uploadlist.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.sha1list.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.offlinelist.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.aria2list.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.endlist.resize(self.content_widget.width() - 165, self.content_widget.height())

    async def wait_close(self):
        while 1:
            if not self.mprocess.is_alive():
                self.close()
                return
            await sleep(0.1)

    # 是否允許拖曳文件
    def dragEnterEvent(self, event):
        # 如果是在首頁則允許拖曳
        if self.sidebar == 1 or self.sidebar == 3:
            # 允許拖曳
            event.acceptProposedAction()

    def dropEvent(self, event):
        # 獲取文件路徑
        file_path = event.mimeData().text()
        # 把路徑中/轉換成\
        file_path = file_path.replace('/', '\\')
        if self.sidebar == 1 and self.self_path_list[0:3] != '搜索-':
            # 分割路徑
            for path in re.findall('file:...(.+)', file_path):
                # 獲取初始目錄
                _dir = re.search('(.+)\\\\.+$', path)[1] + '\\'
                if isdir(path):
                    for root, dirs, files in walk(path):
                        if files:
                            for file in files:
                                data = {
                                    'dir': root.replace(_dir, ''), 'path': join(root, file), 'cid': self.self_path_list
                                }
                                create_task(self.uploadlist.add(data=data))
                        elif files == [] and dirs == []:
                            _path = Path(root)
                            data = {'dir': root.replace(_dir, ''), 'cid': self.self_path_list, 'name': _path.name}
                            create_task(self.uploadlist.new_folder_add(data=data))
                elif isfile(path):
                    data = {'dir': None, 'path': path, 'cid': self.self_path_list}
                    create_task(self.uploadlist.add(data=data))
        elif self.sidebar == 3:
            for path in re.findall('file:...(.+)', file_path):
                _dir = re.search('(.+)\\\\.+$', path)[1] + '\\'
                if isdir(path):
                    for root, dirs, files in walk(path):
                        for file in files:
                            ico = get_ico(splitext(file)[1])
                            data = {'name': file, 'dir': root.replace(_dir, ''), 'path': join(root, file), 'ico': ico}
                            self.sha1list.path_add(data=data)
                elif isfile(path):
                    _, name = split(path)
                    ico = get_ico(splitext(name)[1])
                    data = {'name': name, 'dir': None, 'path': path, 'ico': ico}
                    self.sha1list.path_add(data=data)

    def closeEvent(self, event):
        if self.closes.value:
            if self._state:
                with open('state.json', 'w') as f:
                    json.dump(dict(self._state), f)
            event.accept()
        else:
            self.closes.value = 1
            create_task(self.wait_close())
            event.ignore()

if __name__ == '__main__':
    freeze_support()
    app = QApplication(argv)
    loop = QEventLoop(app)
    set_event_loop(loop)
    ex = Fake115GUI()
    ex.show()
    with loop:
        loop.run_forever()
