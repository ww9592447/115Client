import math
import re
import time
import pickle
from typing import AsyncIterable, Callable, Awaitable
from asyncio import create_task, sleep, current_task
from os.path import splitext, isfile, split, isdir, join, exists
from os import startfile, walk, remove
from threading import Thread
from pathlib import Path
from multiprocessing import Process, Manager, Lock, Value

from PyQt5.Qt import QCloseEvent, QFrame, QWidget, QLabel, QButtonGroup, QFileDialog, QProgressBar, \
    QFont, QPixmap, QPushButton, QResizeEvent, QIcon, QDragEnterEvent, QDropEvent

from mprocess import MultiProgress
from Modules import srequests
from Modules.type import MyTextSlots, TextSlots, MyTextData, TextData, AllCidData, GetFolderData, StateData, \
    ErrorResult, Credential, Config
from Modules.image import AllImage, Image, IcoImage, get_ico
from Modules.widgets import MyIco, MyPushButton
from MyQlist.DList import QListDirectory
from MyQlist.QText import Text
from Modules.get_data import pybyte, get_path
from Window.window import YFramelessWindow
from Window.hints import error, Error, Enter, FolderList, EnterOffline, EnterShare
from Window.endlist import EndList
from Window.downloadlist import DownloadList
from Window.uploadlist import UploadList
from Window.offlinelist import OfflineList
from Window.aria2list import Aria2List
from Window.sharelist import ShareList
from API.directory import Directory
from API.offline import Offline
from API.share import Share

try:
    from winfspy.plumbing import bindings

    bindings.get_winfsp_bin_dir()
    WinFsp = True
except RuntimeError:
    WinFsp = False


class TitleLabel(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__()
        # 設置 115 圖標容器
        self.ico: QLabel = QLabel(self)
        # 設置 115 圖標
        self.ico.setPixmap(AllImage.get_image(Image.ICO_115))
        # 調整 115 圖標 大小
        self.ico.setGeometry(20, 6, 30, 30)
        # 設置 115 文字圖片容器
        self.text: QLabel = QLabel(self)
        # 設置 115 文字圖片
        self.text.setPixmap(AllImage.get_image(Image.TEXT_115))
        # 設置 115 文字圖片容器 大小
        self.text.setGeometry(58, 8, 76, 29)
        # 副標題
        self.title_label: QWidget = QWidget(self)
        # 設置最小化按鈕
        self.minimize: MyIco = MyIco(
            self.title_label, Image.BLACK_MINIMIZE, Image.BLUE_MINIMIZE, state=True,
            coordinate=(17, 6, 12, 12), click=parent.showMinimized)
        # 設置最大化按鈕
        self.maximize: MyIco = MyIco(
            self.title_label, Image.BLACK_MAXIMIZE, Image.BLUE_MAXIMIZE, state=True,
            coordinate=(46, 6, 12, 12), click=lambda: self.replace(True))
        # 設置關閉按鈕
        self.closure: MyIco = MyIco(
            self.title_label, Image.BLACK_CLOSE, Image.BLUE_CLOSE, state=True,
            coordinate=(75, 6, 12, 12), click=parent.close
        )
        # 設置還原大小按鈕
        self.reduction: MyIco = MyIco(
            self.title_label, Image.BLACK_RESTORE, Image.BLUE_RESTORE, state=True,
            coordinate=(46, 6, 12, 12), click=lambda: self.replace(False)
        )

        # 設置右側邊框
        self.frame: QFrame = QFrame(self.title_label)
        # 設置右側邊框大小
        self.frame.setGeometry(0, 3, 1, 19)
        # 設置右側邊框顏色
        self.frame.setStyleSheet('background-color: rgba(200, 200, 200, 125)')
        # 初始化還原大小隱藏
        self.reduction.hide()
        # 設定標題下方邊框
        self.setStyleSheet('TitleLabel{background-color: rgb(255, 255, 255);'
                           'border-style:solid; border-bottom-width:1px;'
                           'border-color:rgba(200, 200, 200, 125)}')

    # 根據目前窗口狀態 來決定是否 最大化 還原
    def set_ico(self) -> None:
        # 查看是否已經最大化
        if self.parentWidget().is_maximize:
            # 查看還原按鈕是否還是變色狀態
            if self.reduction.state:
                # 如果是還原圖片
                self.reduction.initialization()
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
            self.parentWidget().show_maximized()
        else:
            self.parentWidget().show_normal()

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.title_label.move(self.width() - 104, 10)


class MyListDirectory(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        # 設置上傳按鈕
        self.upload_file: MyPushButton = MyPushButton(self, '上傳檔案', (10, 8, 111, 41), qss=2, font_size=16)
        # 設置離線按鈕
        self.upload_folder: MyPushButton = MyPushButton(self, '上傳資料夾', (130, 8, 111, 41), qss=2, font_size=16)
        # 設置離線按鈕
        self.offline: MyPushButton = MyPushButton(self, '離線下載', (250, 8, 111, 41), qss=2, font_size=16)
        # 設置瀏覽窗口
        self.list_directory: QListDirectory = QListDirectory(self)
        # 設置 背景空白 左側邊框
        self.setStyleSheet('MyListDirectory{background-color: rgb(255, 255, 255);'
                           'border-style:solid; border-left-width:1px; border-color:rgba(200, 200, 200, 125)}')

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.list_directory.setGeometry(1, 55, self.width() - 1, self.height() - 55)


# 側邊框
class Sidebar(QPushButton):
    def __init__(
            self,
            parent: QWidget,
            window: QWidget,
            text: str,
            ico_1: Image,
            ico_2: Image,
            move: tuple[int, int]
    ) -> None:
        super().__init__(parent)
        # 設置未點擊圖標
        self.ico_1: QPixmap = AllImage.get_image(ico_1)
        # 設置已點擊圖標
        self.ico_2: QPixmap = AllImage.get_image(ico_2)
        # 獲取字體
        font = QFont()
        # 設置字體大小
        font.setPointSize(10)
        # 設置 側邊框文字
        self.text: QLabel = QLabel(self)
        # 設置 側邊框 位置
        self.text.move(55, 12)
        # 設置 側邊框 文字
        self.text.setText(text)
        # 設置 側邊框 字體
        self.text.setFont(font)
        # 設置 側邊框 自動調整大小
        self.text.adjustSize()
        # 設置 側邊框目前數量
        self.index: QLabel = QLabel(self)
        # 設置 側邊框 目前數量 位置
        self.index.move(self.text.x() + self.text.width() + 5, 12)
        # 設置 側邊框 目前數量 字體
        self.index.setFont(font)
        # 設置 側邊框圖案
        self.ico = QLabel(self)
        # 設置 側邊框圖案 大小 位置
        self.ico.setGeometry(31, 9, 20, 20)
        # 設置 側邊框圖案
        self.ico.setPixmap(self.ico_1)

        # 是否設定大小
        self.move(*move)
        # 設置成可切換按鈕
        self.setCheckable(True)
        # 設置成自動排他按鈕
        self.setAutoExclusive(True)
        # 連接切換圖標事件
        self.toggled.connect(
            lambda visible: self.ico.setPixmap(self.ico_2) if visible else self.ico.setPixmap(self.ico_1)
        )
        # 連切置頂窗口事件
        self.toggled.connect(lambda visible: window.raise_() if visible else '')

        # 設置 側邊框 qss
        self.setStyleSheet(
            'Sidebar{background-color:rgb(249, 250, 251); border-style:solid;border-left-width: 5px;'
            'border-color: rgb(249, 250, 251)}'
            'Sidebar:on{background-color:rgb(234, 246, 253); border-color: rgb(6, 163, 248)}'
            'Sidebar:hover:!on{background-color:rgb(234, 246, 253); border-color: rgb(234, 246, 253)}'
        )

        # 設置 測邊框 大小
        self.resize(165, 38)


class Fake115(YFramelessWindow):

    def __init__(self, config: Config, credential: Credential):
        super().__init__()
        # 設置任務欄圖標
        self.setWindowIcon(AllImage.get_ico(IcoImage.FAVICON))
        # 獲取115設定
        self.config: Config = config
        # 設置所有cid資料
        self.all_cid_data: dict[str, AllCidData] = {}
        # 設置目前所在目錄
        self.self_path_list: str = '0'
        # 設置目前搜索cid
        self.search_cid: tuple[str, ...] | None = None
        # 設置上一頁目錄順序
        self.up_page_list: list[str, ...] = []
        # 設置下一頁目錄順序
        self.on_page_list: list[str, ...] = []
        # 設置待複製列表
        self._copy: list[str, ...] = []
        # 設置待剪下列表
        self._cut: list[str, ...] = []
        # 設置原本剪下目錄cid
        self._cut_cid: str = ''
        # 設置共用數據
        self.all_data: dict[str, any] = Manager().dict()
        # 設置共用數據鎖
        self.lock: Lock = Lock()
        # 設置傳送列表鎖
        self.wait_lock: Lock = Lock()
        # 設置傳送列表
        self.wait: list[str, ...] = Manager().list()
        # 設置關閉信號
        self.closes: Value = Value('i', 0)
        # 搜索資料夾任務
        self.search_task: dict[tuple[str, str | int], Awaitable[ErrorResult]] = {}
        # 設置標題窗口
        self.title_label: TitleLabel = TitleLabel(self)
        # 設置標題大小
        self.title_label.resize(self.shadow_widget.width(), 44)
        # 更新標題窗口至主窗口
        self.set_title(self.title_label)

        # 設置目錄操作API
        self.directory: Directory = Directory(credential)
        # 設置分享API
        self.share: Share = Share(credential)
        # 設置離線API
        self.offline: Offline = Offline(credential)

        # 設置設置所有子窗口
        self.child_window: QWidget = QWidget(self.content_widget)
        # 設置按鈕+瀏覽窗口組合窗口
        self.my_list_directory: MyListDirectory = MyListDirectory(self.child_window)
        # 設置瀏覽窗口
        self.list_directory: QListDirectory = self.my_list_directory.list_directory
        # 資料夾瀏覽窗口
        self.folder_list: FolderList = FolderList(self.directory)

        # 加入傳輸完畢窗口
        self.end_list: EndList = EndList(
            lambda: self.btn_group.button(1).click(), self.network,
            lambda index: self.set_text(5, index),
            self.child_window
        )
        # 加入下載窗口
        self.download_list: DownloadList = DownloadList(
            self.all_data, self.lock, self.wait, self.wait_lock,
            self.config, self.end_list, self.get_folder, lambda index: self.set_text(2, index),
            parent=self.child_window
        )
        # 加入aria2窗口
        self.aria2_list: Aria2List = Aria2List(
            self.all_data, self.lock, self.wait, self.wait_lock,
            self.config, self.end_list, self.get_folder, lambda index: self.set_text(3, index),
            parent=self.child_window
        )
        # 加入上傳窗口
        self.upload_list: UploadList = UploadList(
            self.all_data, self.lock, self.wait, self.wait_lock,
            self.config, self.end_list, lambda index: self.set_text(4, index),
            self.all_cid_data, self.search_add_folder,
            parent=self.child_window
        )
        # 加入離線窗口
        self.offline_list: OfflineList = OfflineList(
            self.offline, lambda: self.btn_group.button(1).click(),
            lambda cid: self.network(cid), parent=self.child_window
        )
        # 加入分享窗口
        self.share_list: ShareList = ShareList(self.child_window, self.share)
        # 新增瀏覽視窗標題
        self.list_directory.title_add('名稱', 400, 200)
        self.list_directory.title_add(' 修改時間', 130, 130)
        self.list_directory.title_add(' 大小', 85, 85)
        self.list_directory.title_add(' 所在目錄', least=80)
        # 設定 所在目錄 標題 隱藏
        self.list_directory.set_title_visible(' 所在目錄', False)
        # 設置 側邊框 按鈕組
        self.btn_group: QButtonGroup = QButtonGroup(self)
        # 設置 側邊框 內容
        self.set_sidebar()
        # 設置事件回調
        self.set_callable()
        # 設置 text 點擊回調
        self.set_text_slot()
        # 設置 text | 背景 右鍵回調
        self.set_text_menu_click()

        # 設置 容量大小 進度條
        self.progressbar = QProgressBar(self)
        # 設置 容量大小 文字
        self.progressbar_size = QLabel(self)
        self.progressbar.setStyleSheet('QProgressBar{border: 0px; background:rgb(200, 100, 200); border-radius:6px;'
                                       'background-color: rgb(229, 230, 234);color:rgb(60, 104, 137)}'
                                       'QProgressBar:chunk {background-color: rgb(6, 168, 255); border-radius:6px}')
        self.progressbar.setMaximum(100)

        self.progressbar.setTextVisible(False)

        # 設置允許拖曳文件
        self.setAcceptDrops(True)

        # 設置最低大小
        self.setMinimumSize(1000, 600)

        if exists('state.json'):
            with open('state.json', 'rb') as f:
                output = pickle.load(f)
            for out in output.items():
                data = out[1]
                action = out[0][0]
                if action == '2':
                    self.download_list.add(data, value=False)
                elif action == '3':
                    self.upload_list.add(data, value=False)
                elif action == '4':
                    self.aria2_list.add(data, value=False)
            remove('state.json')

        self.multi_progress = Process(
            target=MultiProgress, args=(self.all_data, self.lock, self.wait, self.wait_lock,
                                        self.closes, 11, self.directory, credential, self.config)
        )
        self.multi_progress.daemon = True
        self.multi_progress.start()

        create_task(self.network('0'))

    # 獲取 aria2 下載路徑
    async def get_aria2_path(self) -> str | bool:
        data = {
            'jsonrpc': '2.0',
            'id': 'qwer',
            'method': 'aria2.getGlobalOption',
        }
        result = await srequests.async_post(url=self.config['aria2_rpc_url'], json=data, retry=1, timeout=1)

        if result and result.status_code == 200:
            return result.json()['result']['dir']
        else:
            return False

    @error()
    # 下載
    async def get_download(self, action: str) -> ErrorResult:
        data = self.list_directory.extra()
        for _data in [data] if isinstance(data, dict) else data:
            if _data['category'] != '0':
                if action == 'download':
                    self.download_list.add(_data)
                elif action == 'aria2':
                    path = await self.get_aria2_path()
                    if path:
                        _data['path'] = path
                        self.aria2_list.add(_data)
                    else:
                        return ErrorResult(state=False, title='Aria2 url 不可用', name='請問是否重新獲取', result='')
            else:
                if action == 'download':
                    self.download_list.folder_add(_data)
                elif action == 'aria2':
                    _data['path'] = await self.get_aria2_path()
                    self.aria2_list.folder_add(_data)
        return ErrorResult(state=True, title='', name='', result='')

    # 設置側邊框
    def set_sidebar(self) -> None:
        all_data = (
            (self.my_list_directory, '首頁', Image.BLACK_FRONT_PAGE, Image.BLUE_FRONT_PAGE),
            (self.download_list, '正在下載', Image.BLACK_DOWNLOAD, Image.BLUE_DOWNLOAD),
            (self.aria2_list, 'Aria2', Image.BLACK_ARIA2, Image.BLUE_ARIA2),
            (self.upload_list, '正在上傳', Image.BLACK_UPLOAD, Image.BLUE_UPLOAD),
            (self.end_list, '傳輸完成', Image.BLACK_TRANSMISSION_COMPLETE, Image.BLUE_TRANSMISSION_COMPLETE),
            (self.offline_list, '離線下載', Image.BLACK_TRANSMISSION_COMPLETE, Image.BLUE_TRANSMISSION_COMPLETE),
            (self.share_list, '我的分享', Image.BLACK_SHARE, Image.BLUE_SHARE),
        )
        for index, data in enumerate(all_data):
            sidebar: Sidebar = Sidebar(
                self.content_widget, data[0], data[1], data[2], data[3], (0, 38 * index)
            )
            self.btn_group.addButton(sidebar, index + 1)
        self.btn_group.button(1).click()

    # 設置 text | 背景 右鍵回調
    def set_text_menu_click(self) -> None:
        # 設定 text 下載 右鍵
        self.list_directory.text_menu_click_connect(
            '下載', lambda: create_task(self.get_download('download')), ico=AllImage.get_ico(IcoImage.DOWNLOAD)
        )
        # 設定 text 下載 右鍵
        self.list_directory.text_menu_click_connect(
            'aria2下載', lambda: create_task(self.get_download('aria2')), ico=AllImage.get_ico(IcoImage.ARIA2)
        )
        self.list_directory.text_menu_click_connect(
            '播放', lambda: create_task(self.play()), ico=AllImage.get_ico(IcoImage.PLAY)
        )
        # 設定 text 刪除 右鍵
        self.list_directory.text_menu_click_connect(
            '刪除', lambda: self.get_enter('刪除'), ico=AllImage.get_ico(IcoImage.DELETE)
        )
        # 設定 text 重新命名 右鍵
        self.list_directory.text_menu_click_connect(
            '重新命名', lambda: self.get_enter('重新命名'), ico=AllImage.get_ico(IcoImage.RENAME)
        )
        # 設定 text 複製 右鍵
        self.list_directory.text_menu_click_connect(
            '複製', self.copy, ico=AllImage.get_ico(IcoImage.COPY)
        )
        # 設定 text 剪下 右鍵
        self.list_directory.text_menu_click_connect(
            '剪下', self.cut, ico=AllImage.get_ico(IcoImage.CUT)
        )
        # 設定 text 移動 右鍵
        self.list_directory.text_menu_click_connect(
            '移動', lambda: self.get_enter('移動檔案'), ico=AllImage.get_ico(IcoImage.MOVE)
        )
        # 設定 text 移動 右鍵
        self.list_directory.text_menu_click_connect(
            '分享', lambda: create_task(self.set_share()), ico=AllImage.get_ico(IcoImage.SHARE)
        )
        # 設定背景 新增資料夾 右鍵
        self.list_directory.backdrop_menu_click_connect(
            '新建資料夾', lambda: self.get_enter('新建資料夾'), ico=AllImage.get_ico(IcoImage.NEW_FOLDER)
        )
        # 設定 背景 貼上 右鍵
        self.list_directory.backdrop_menu_click_connect(
            '貼上', lambda: create_task(self.network(
                self.self_path_list, action=lambda: create_task(self.paste(self.self_path_list)), add=False
            )), ico=AllImage.get_ico(IcoImage.PASTE), mode=False
        )

        # 設定背景 新增資料夾 右鍵
        self.list_directory.text_menu_click_connect(
            '測試', self.qq, ico=AllImage.get_ico(IcoImage.NEW_FOLDER)
        )

    def qq(self):
        print(self.list_directory.extra())

    # 設置事件回調
    def set_callable(self) -> None:
        # 設定搜索回調
        self.list_directory.set_linedit_callable(self.search_callable)
        # 設定搜索全部回調
        self.list_directory.set_search_all_callable(self.search_all_callable)
        # 設定搜索名稱回調
        self.list_directory.set_search_name_callable(self.search_name_callable)
        # 設定目錄點擊回調
        self.list_directory.set_directory_callable(lambda text: create_task(self.network(text.data)))
        # 設定上一頁回調
        self.list_directory.set_pgup_callable(self.up_page_callable)
        # 設定下一頁回調
        self.list_directory.set_pgon_callable(self.on_page_callable)
        # 設置頁數回調
        self.list_directory.set_page_callable(self.page_callable)
        # 設定重新整理回調
        self.list_directory.set_rectangle_callable(lambda: create_task(self.reorganize_callable()))
        # 設定上傳檔案回調
        self.my_list_directory.upload_file.clicked.connect(
            lambda: self.get_enter('打開檔案瀏覽器')
        )
        # 設定上傳資料夾回調
        self.my_list_directory.upload_folder.clicked.connect(
            lambda: self.get_enter('打開資料夾瀏覽器')
        )

        # 設定離線下載回調
        self.my_list_directory.offline.clicked.connect(
            lambda: EnterOffline.get(self.offline, self.folder_list)
        )
        # 設置右鍵回調
        self.list_directory.set_text_menu_callable(self.text_menu_callback)

    # 設置text點擊回調
    def set_text_slot(self) -> None:
        text_slot_list: list[TextSlots, ...] = []
        my_text_slots: MyTextSlots = MyTextSlots(connect_left_click=[self.click_callable], disconnect_left_click=None)
        text_slots: TextSlots = TextSlots(
            connect_left_click=None,
            connect_double_click=[self.click_callable],
            disconnect_left_click=None,
            disconnect_double_click=None,
            my_text={'名稱': my_text_slots, ' 所在目錄': my_text_slots}
        )
        for _ in range(self.list_directory.qlist_data['quantity_limit']):
            text_slot_list.append(text_slots)
        self.list_directory.set_text_slots(text_slot_list)

    def set_text(self, sidebar_id: int, index: int) -> None:
        sidebar = self.btn_group.button(sidebar_id)
        if index != 0:
            sidebar.index.setText(f'({index})')
            sidebar.index.adjustSize()
        else:
            sidebar.index.setText('')

    # 禁止操作
    def prohibit(self, mode: bool) -> None:
        # 是否顯示 等待動畫
        self.list_directory.set_load_visible(not mode)
        self.list_directory.setEnabled(mode)

    # 網路
    async def network(
            self,
            cid: str,
            page: int = 1,
            action: Callable[[], Awaitable[ErrorResult]] | None = None,
            add: bool = True
    ) -> None:
        # 瀏覽目錄清空
        self.list_directory.directory_cls()
        # 清空點擊
        self.list_directory.cls_click()
        # 禁止操作
        self.prohibit(False)
        # 查看cid是否是搜索
        if cid[0:3] == '搜索-':
            # 分割 cid 獲取資料
            search = re.search('搜索-(.+)-(.+)-(.+)', cid).groups()
            self.search_cid = search
            if self.search_cid[0] != '0':
                self.list_directory.set_search_visible(True, self.search_cid[1])
        # 目前不是搜索 and 上一頁是搜索
        elif self.self_path_list[0:3] == '搜索-':
            # 搜索按鈕初始化
            self.list_directory.set_search_visible(False)
        # 如果不是搜索 and 搜索還有資料
        elif self.search_cid:
            # 初始化搜索
            self.search_cid = None

        # 搜索按鈕全部影藏
        self.list_directory.search_button_container.hide()
        # 查看是否要新增 上一頁目錄
        if add is True:
            # 下一頁目錄清空
            self.on_page_list.clear()
            # 下一頁按鈕 不可使用
            self.list_directory.set_pgon(False)
            # 上一頁加入
            self.up_page_list.append(cid)

        result = True
        if action or (cid in self.all_cid_data and self.all_cid_data[cid]['refresh']):
            if action:
                self.list_directory.cls()
                if (await action())['state'] is False:
                    result = False
            if result:
                del self.all_cid_data[cid]
                if cid in self.list_directory.text.text_save_list.save:
                    self.list_directory.cls(cid)

        if self.progressbar_size.text() == '':
            await self.set_progressbar()

        # 查看 cid 是否不在 所有介面的頁數資料
        if cid not in self.list_directory.text.text_save_list.save:
            # 如果不再 則新增 新窗口
            self.list_directory.new(cid)
        elif cid != self.list_directory.text.text_name:
            self.list_directory.switch(cid, refresh=True)

        if result:
            if cid not in self.all_cid_data or page not in self.all_cid_data[cid]['data']:
                if cid[0:3] == '搜索-':
                    await self.search(cid, page)
                else:
                    res = await create_task(self.refresh(cid, page))
                    # 刷新目錄
                    if res['result'] == '0':
                        create_task(self.network('0'))
                        return
                    elif res['state'] is False:
                        # 恢復操作
                        self.prohibit(True)
                        return
            self.add(cid, page)
            if cid[0:3] == '搜索-':
                self.list_directory.search_button_container.show()
        # 恢復操作
        self.prohibit(True)

    # 刷新目錄
    @error()
    async def refresh(self, cid: str, page: int) -> ErrorResult:
        result = await self.directory.path(
            cid, (page - 1) * self.list_directory.qlist_data['quantity_limit'],
            self.list_directory.qlist_data['quantity_limit']
        )
        if result:
            if cid != str(result['cid']):
                return ErrorResult(state=True, title='', name='', result='0')
            # 格式化115數據
            await self.dumps(result, cid, page)
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='刷新介面錯誤', name='請問是否重新嘗試', result='')

    # 格式化115數據
    async def dumps(self, items: dict, cid: str, page: int) -> None:
        index: dict[str, dict[str, any]] = {}
        text_data_list: list[TextData, ...] = []

        for data in items['data']:
            # 獲取 檔案 or 資料夾 修改日期時間戳 並轉換成正常日期
            if 'te' in data:
                _data_time = data['te']
            else:
                _data_time = data['t'] if data['t'].isdigit() else int(
                    time.mktime(time.strptime(f"{data['t']}:0", "%Y-%m-%d %H:%M:%S")))
            data_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(int(_data_time)))
            # 獲取檔案cid
            data_cid = str(data['fid']) if 'fid' in data else str(data['cid'])
            # 獲取檔案ico
            data_ico = get_ico(splitext(data['n'])[1] if 'fid' in data else 'folder')
            # 獲取檔案大小
            data_size = data['s'] if 's' in data else '0'

            if data_ico == Image.MIN_FOLDER:
                name_text_data: MyTextData = MyTextData(
                    text=data['n'], color=((0, 0, 0), (6, 168, 255)), mouse=True, text_size=[]
                )
            else:
                name_text_data: MyTextData = MyTextData(text=data['n'], color=None, mouse=False, text_size=[])

            time_text_data: MyTextData = MyTextData(text=data_time, color=None, mouse=False, text_size=[])
            size_text_data: MyTextData = MyTextData(
                text='-' if data_size == '0' else pybyte(int(data_size)), color=None, mouse=False, text_size=[]
            )
            text_data: TextData = TextData(
                data={
                    'name': data['n'],
                    'category': '1' if 'fid' in data else '0',
                    'cid': data_cid,
                    'pid': data['pid'] if 'pid' in data else data['cid'],
                    'time': int(_data_time),
                    'pc': data['pc'],
                    'sha1': data['sha'] if 'sha' in data else None,
                    'size': int(data_size),
                    'ico': data_ico,
                    'dp': data['dp'] if 'dp' in data else None,
                },
                ico=data_ico,
                my_text={'名稱': name_text_data, ' 修改時間': time_text_data, ' 大小': size_text_data},
                mouse=True if data_ico == Image.MIN_FOLDER else False
            )
            # print(data['fuuid'])
            # 查看是否有所在目錄
            if 'dp' in data:
                text_data['my_text'][' 所在目錄'] = MyTextData(
                    text=data['dp'], color=((0, 0, 0), (6, 168, 255)), mouse=True, text_size=[]
                )
            index[data['n']] = text_data['data']
            text_data_list.append(text_data)

        with self.lock:
            self.all_data[f'0{cid}'] = {'state': False, 'list': text_data_list}

        with self.wait_lock:
            self.wait.append(f'0{cid}')

        while 1:
            await sleep(0.1)
            with self.lock:
                if self.all_data[f'0{cid}']['state']:
                    text_data_list = self.all_data[f'0{cid}']['list']
                    del self.all_data[f'0{cid}']
                    break
        if cid not in self.all_cid_data:
            if 'path' in items:
                path = [(i['name'], str(i['cid'])) for i in items['path']]
            else:
                path = [('根目录', '0'), (f'搜尋-{self.search_cid[1]}', cid)]

            self.all_cid_data.update(
                {
                    cid:
                        {
                            'data': {page: text_data_list},
                            'path': path,
                            'index': index,
                            'refresh': False,
                            'count': items['count'],
                            'page': math.ceil(items['count'] / self.list_directory.qlist_data['quantity_limit'])}
                }
            )
        else:
            self.all_cid_data[cid]['data'][page] = text_data_list
            self.all_cid_data[cid]['index'].update(index)

    # 添加到窗口列表
    def add(self, cid: str, page: int) -> None:
        # 查看 上一頁 是否可以顯示可用
        if len(self.up_page_list) != 1 and not self.list_directory.get_pgup():
            # 設定 上一頁按鈕 成可用
            self.list_directory.set_pgup(True)
        # 添加瀏覽目錄
        for path in self.all_cid_data[cid]['path']:
            self.list_directory.directory_add(path[0], path[1])

        # 查看是否需要增加頁數
        if self.list_directory.quantity.page_max != self.all_cid_data[cid]['page']:
            self.list_directory.set_all_page(self.all_cid_data[cid]['page'])
            if page != self.list_directory.quantity.qlist_data['page']:
                self.list_directory.quantity.set_page(page, callable=False, refresh=False)

        if cid[0:3] == '搜索-' and ' 所在目錄' not in self.list_directory.get_title():
            self.list_directory.set_title_visible(' 所在目錄', True)
        elif cid[0:3] != '搜索-' and ' 所在目錄' in self.list_directory.get_title():
            self.list_directory.set_title_visible(' 所在目錄', False)
        # 查看目前目錄 是否變化
        if self.self_path_list != cid:
            # 查看上一頁是否是搜索
            if self.self_path_list[0:3] == '搜索-':
                # 如果是則把上一頁搜索設定成需要刷新
                self.all_cid_data[self.self_path_list]['refresh'] = True
            # 設定目前所在目錄
            self.self_path_list = cid

            if cid in self.list_directory.text.text_save_list.save:
                # 比對資料是否一樣
                if self.list_directory.get_text_data()[page].text_data_list == self.all_cid_data[cid]['data'][page]:
                    # 如果一樣則退出
                    return
        self.list_directory.add_text(self.all_cid_data[cid]['data'][page], refresh=True)

    # 搜索資料夾 如果沒有則創建資料夾
    async def search_add_folder(self, cid: str, names: str) -> AsyncIterable[tuple[StateData, str]]:
        for name in names.split('\\'):
            if not name:
                break
            task = None
            index = 1
            while 1:
                if cid in self.all_cid_data and name in self.all_cid_data[cid]['index']:
                    cid = self.all_cid_data[cid]['index'][name]['cid']
                    break
                elif (cid, name) not in self.search_task and cid in self.all_cid_data and \
                        index in self.all_cid_data[cid]['data'] and \
                        (self.all_cid_data[cid]['count'] == 0 or index == self.all_cid_data[cid]['page']
                         or self.all_cid_data[cid]['data'][index][-1]['data']['category'] == '1'):
                    task = create_task(self.add_folder(cid, name))
                    task.set_name('創建資料夾失敗')
                    task.add_done_callback(lambda _task: self.search_task.pop((cid, name)))
                    self.search_task[(cid, name)] = task
                elif cid in self.all_cid_data and index in self.all_cid_data[cid]['data'] \
                        and index != self.all_cid_data[cid]['page']:
                    if (index := index + 1) in self.all_cid_data[cid]['data']:
                        continue
                elif (cid, name) not in self.search_task and (cid, index) not in self.search_task \
                        and (cid in self.all_cid_data and name not in self.all_cid_data[cid]['index']
                             or cid not in self.all_cid_data):
                    task = create_task(self.refresh(cid, index, state=False))
                    task.set_name('獲取資料夾資料失敗')
                    task.add_done_callback(lambda _task: self.search_task.pop((cid, index)))
                    self.search_task[(cid, index)] = task
                elif (cid, name) in self.search_task:
                    task = self.search_task[(cid, name)]
                elif (cid, index) in self.search_task:
                    task = self.search_task[(cid, index)]
                if task:
                    if task.get_name() == '創建資料夾失敗':
                        yield StateData.TEXT, '創建資料夾中'
                    result = await task
                    if result['state'] is False or result['result'] == '0':
                        yield StateData.ERROR, '資料夾不存在' if result == '0' else task.get_name()
                    task = None
        yield StateData.COMPLETE, cid

    # 下載 資料夾 獲取資料
    async def get_folder(self, cid: str) -> GetFolderData:
        # 查看是否有 cid and 是否需要刷新
        if cid in self.all_cid_data and self.all_cid_data[cid]['refresh']:
            del self.all_cid_data[cid]
            if cid in self.list_directory.text.text_save_list.save:
                self.list_directory.cls(cid)
        # index 初始化
        index = 0
        while cid not in self.all_cid_data or index < self.all_cid_data[cid]['page']:
            result = await self.refresh(cid, index, state=False)
            if result is False or result == '0':
                return GetFolderData(state=False, result='資料夾不存在' if result == '0' else '獲取資料夾資料失敗')
            index += 1
        return GetFolderData(state=True, result=self.all_cid_data[cid]['index'])

    @error()
    async def set_share(self, share_code: str = '') -> ErrorResult:
        self.prohibit(False)
        if share_code == '':
            cid = self.list_directory.extra()['cid']
            result = await self.share.set_share(cid)
            if result:
                data = result['data']
                await self.set_share(data['share_code'])
                self.prohibit(True)
                return ErrorResult(state=True, title='', name='', result='')
            self.prohibit(True)
            return ErrorResult(state=False, title='網路異常分享失敗', name='請問是否重新嘗試', result='')
        result = await self.share.get_share_data(share_code)
        if result:
            data = result['data']
            current_task().add_done_callback(
                lambda task: EnterShare.get(
                    self.share, data['share_title'], int(data['total_size']), data['share_code'],
                    data['share_url'], data['custom_receive_code'], data['receive_code'], data['sys_receive_code'])
            )
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='網路異常獲取分享資料失敗', name='請問是否重新嘗試', result='')

    # 獲取輸入
    def get_enter(self, action: str) -> None:
        if action == '移動檔案':
            if _cid := self.folder_list.stop('打開要移動的目標文件夾', '移動到這裡'):
                cid = []
                data = self.list_directory.extra()
                for _data in [data] if isinstance(data, dict) else data:
                    cid.append(_data['cid'])
                create_task(self.network(
                    self.self_path_list, action=lambda: create_task(self.file_move(_cid[0], cid)), add=False
                ))
        elif action == '新建資料夾' and self.self_path_list[0:3] != '搜索-':
            if name := Enter.get('新建資料夾', '新名稱'):
                create_task(self.network(
                    self.self_path_list, page=self.list_directory.qlist_data['page'],
                    action=lambda: create_task(self.add_folder(self.self_path_list, name)),
                    add=False
                ))
        elif action == '重新命名':
            if name := Enter.get('重新命名', '新名稱'):
                cid = self.list_directory.text.current_click[0].text_data['data']['cid']
                create_task(self.network(
                    self.self_path_list, page=self.list_directory.qlist_data['page'],
                    action=lambda: create_task(self.rename(name, cid)), add=False
                ))
        elif action == '刪除':
            current_click = self.list_directory.text.current_click.copy()
            if Error.get('刪除', '請問是否刪除'):
                current_click = self.list_directory.text.current_click.copy()
                create_task(self.network(
                    self.self_path_list, action=lambda: create_task(self.delete(current_click)), add=False
                ))
        elif action == '打開檔案瀏覽器':
            files, _ = QFileDialog.getOpenFileNames(self, "Open file", "./")
            self.upload(files)
        elif action == '打開資料夾瀏覽器':
            folder = QFileDialog.getExistingDirectory(self, "Open file", "./")
            self.upload([folder])

    # 複製
    def copy(self) -> None:
        self._copy.clear()
        self._cut.clear()
        self._cut_cid = ''
        self.list_directory.set_backdrop_menu_visible('貼上', True)
        data = self.list_directory.extra()
        for _data in [data] if isinstance(data, dict) else data:
            self._copy.append(_data['cid'])

    # 剪下
    def cut(self) -> None:
        self._copy.clear()
        self._cut.clear()
        self._cut_cid = self.self_path_list
        self.list_directory.set_backdrop_menu_visible('貼上', True)
        data = self.list_directory.extra()
        for _data in [data] if isinstance(data, dict) else data:
            self._cut.append(_data['cid'])

    # 貼上
    @error()
    async def paste(self, cid: str) -> ErrorResult:
        if self._copy:
            result = await self.directory.paste(self._copy, cid)
            if result:
                self.list_directory.set_backdrop_menu_visible('貼上', False)
                self._copy.clear()
            return ErrorResult(state=True, title='', name='', result='')
        if self._cut:
            result = await self.directory.move(self._cut, cid)
            if result:
                self.list_directory.set_backdrop_menu_visible('貼上', False)
                self._cut.clear()
                self.all_cid_data[self._cut_cid]['refresh'] = True
                self._cut_cid = ''
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='貼上錯誤', name='請問是否重新嘗試', result='')

    # 移動檔案
    @error()
    async def file_move(self, move_cid: str, file_cid: str | list[str, ...]) -> ErrorResult:
        result = await self.directory.move(file_cid, move_cid)
        if result:
            if move_cid in self.all_cid_data:
                self.all_cid_data[move_cid]['refresh'] = True
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='貼上錯誤', name='請問是否重新嘗試', result='')

    # 刪除
    @error()
    async def delete(self, current_click: list[Text, ...]) -> ErrorResult:
        all_cid_data: list[str, ...] = []
        if len(current_click) != 1:
            for text in current_click:
                all_cid_data.append(text.text_data['data']['cid'])
        else:
            all_cid_data = current_click[0].text_data['data']['cid']
        result = await self.directory.delete(all_cid_data)
        # 刪除完畢後如果是資料夾檢查是否有後續
        if result:
            for text in current_click:
                cid = text.text_data['data']['cid']
                if cid in self.all_cid_data:
                    pid = text.text_data['data']['pid']
                    if pid in self.all_cid_data:
                        self.all_cid_data[pid]['refresh'] = True
                    if cid in self.up_page_list:
                        self.up_page_list.remove(cid)
                    if cid in self.on_page_list:
                        self.on_page_list.remove(cid)
                    del self.all_cid_data[cid]
                    # 查看是否已經有資料新增
                    if cid in self.list_directory.text.text_save_list.save:
                        # 如果以新增 則刪除
                        del self.list_directory.text.text_save_list.save[cid]
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='刪除錯誤', name='請問是否重新嘗試', result='')

    # 重新命名
    @error()
    async def rename(self, name: str, cid: str) -> ErrorResult:
        result = await self.directory.rename(name, cid)
        if result:
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='重新命名錯誤', name='請問是否重新嘗試', result='')

    # 新建資料夾
    @error()
    async def add_folder(self, pid: str, name: str) -> ErrorResult:
        result = await self.directory.add_folder(pid, name)
        if result:
            self.all_cid_data[pid]['refresh'] = True
            self.all_cid_data[pid]['index'][name] = {
                'name': name,
                'category': 0,
                'cid': str(result['cid']),
                'pid': pid,
            }
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='新建資料夾錯誤', name='請問是否重新嘗試', result='')

    # 搜索
    @error()
    async def search(self, cid: str, page: int) -> ErrorResult:
        self.list_directory.lineedit.setText('')
        _cid, _, name = re.search('搜索-(.+)-(.+)-(.+)', cid).groups()
        result = await self.directory.search(
            name, _cid,
            (page - 1) * self.list_directory.qlist_data['quantity_limit'],
            self.list_directory.qlist_data['quantity_limit'],
        )
        if result:
            # 格式化115數據
            await self.dumps(result, cid, page)
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='搜索錯誤', name='請問是否重新嘗試', result='')

    # 播放
    @error(True)
    async def play(self) -> ErrorResult:
        data = self.list_directory.extra()
        with self.lock:
            self.all_data[f'1{data["name"]}!{data["size"]}!{data["pc"]}'] = False
        with self.wait_lock:
            self.wait.append(f'1{data["name"]}!{data["size"]}!{data["pc"]}')

        while 1:
            with self.lock:
                if self.all_data[f'1{data["name"]}!{data["size"]}!{data["pc"]}']:
                    break
            await sleep(0.5)
        with self.lock:
            del self.all_data[f'1{data["name"]}!{data["size"]}!{data["pc"]}']
        t = Thread(target=lambda: startfile(fr'x:\{data["name"]}'))
        # 執行該子執行緒
        t.start()
        while 1:
            if not t.is_alive():
                break
            await sleep(0.1)
        return ErrorResult(state=True, title='', name='', result='')

    # 刷新並設定空間容量
    @error()
    async def set_progressbar(self) -> ErrorResult:
        if size := await self.directory.get_size():
            remain, total, use = size
            _size = int(use) / int(total)
            self.progressbar.setValue(int(('%.2f' % _size)[2:]))
            self.progressbar_size.setFont(QFont("細明體", 9))
            self.progressbar_size.setText(f'已用{pybyte(int(use))}/{pybyte(int(total))}')
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='獲取容量錯誤', name='請問是否重新嘗試', result='')

    # 右鍵回調
    def text_menu_callback(self) -> bool:
        if self.list_directory.get_current_click() > 1:
            self.list_directory.set_menu_visible('重新命名', False)
            self.list_directory.set_menu_visible('播放', False)
        else:
            self.list_directory.set_menu_visible('重新命名', True)
            data = self.list_directory.extra()
            if (WinFsp and data['ico'] == Image.MIN_VIDEO) or data['ico'] == Image.MIN_MUSIC:
                self.list_directory.set_menu_visible('播放', True)
            else:
                self.list_directory.set_menu_visible('播放', False)
        return True

    # 搜索回調
    def search_callable(self) -> None:
        if self.self_path_list[0:3] == '搜索-':
            cid = self.search_cid[0]
            path = self.all_cid_data[self.self_path_list]['path'][-1][0][3:]
        else:
            cid = self.self_path_list
            path = self.all_cid_data[self.self_path_list]['path'][-1][0]
        create_task(self.network(
            f'搜索-{cid}-{path}-'
            f'{self.list_directory.lineedit.text()}')
        )

    # 搜索名稱回調
    def search_name_callable(self) -> None:
        cid = f'搜索-{self.search_cid[0]}-{self.search_cid[1]}-{self.search_cid[2]}'
        if cid in self.all_cid_data:
            self.all_cid_data[cid]['refresh'] = True
        create_task(self.network(cid, add=False))

    # 搜索全部回調
    def search_all_callable(self) -> None:
        cid = f'搜索-0-{self.search_cid[1]}-{self.search_cid[2]}'
        if cid in self.all_cid_data:
            self.all_cid_data[cid]['refresh'] = True
        create_task(self.network(cid, add=False))

    # text點擊回調
    def click_callable(self, text: Text) -> None:
        if not isinstance(self.sender(), Text):
            title: str = [k for k, v in text.child_text.items() if v == self.sender()][0]
            if title == ' 所在目錄':
                create_task(self.network(text.text_data['data']['pid']))
                return
        create_task(self.network(text.text_data['data']['cid']))

    # 上一頁回調
    def up_page_callable(self) -> None:
        # 獲取上一頁最後一cid
        cid = self.up_page_list.pop()
        # cid 添加到下一頁
        self.on_page_list.append(cid)
        # 查看 上一頁 是否只有一個
        if len(self.up_page_list) == 1:
            # 如果只有一個 設定 上一頁按鈕 關閉
            self.list_directory.set_pgup(False)
        # 查看 下一頁按鈕 是否關閉
        if not self.list_directory.get_pgon():
            # 如果關閉 則啟動
            self.list_directory.set_pgon(True)
        # 獲取上一頁最後一個cid
        cid = self.up_page_list[-1]
        # 進入上一頁最後一個cid
        create_task(self.network(cid=cid, add=False))

    # 下一頁回調
    def on_page_callable(self) -> None:
        # 獲取 下一頁 最後一個 cid
        cid = self.on_page_list.pop()
        # 查看 下一頁 是否還有
        if not self.on_page_list:
            # 如果沒有 則把 下一頁按鈕 關閉
            self.list_directory.set_pgon(False)
        # cid 添加到 上一頁
        self.up_page_list.append(cid)
        # 進入 cid
        create_task(self.network(cid=cid, add=False))

    # 頁數回調
    def page_callable(self, page: int) -> None:
        cid = self.self_path_list
        if page not in self.all_cid_data[cid]['data'] or self.all_cid_data[cid]['refresh']:
            create_task(self.network(cid=cid, page=page, add=False))

    # 分析上傳路徑
    def upload(self, paths: list[str, ...]) -> None:
        # for path in paths:
        #     if isfile(path):
        #         _path, name = split(path)
        #         ico = get_ico(splitext(name)[1])
        #         data = {
        #             'name': name,
        #             'ico': ico,
        #             'dir': _path[10:],
        #             'path': path,
        #             'cid': self.self_path_list
        #         }
        #         if self.btn_group.checkedId() == 1:
        #             self.upload_list.add(data)

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
                            if self.btn_group.checkedId() == 1:
                                # 開始上傳
                                self.upload_list.add(data)
                    # 查看是否是空資料夾
                    elif self.btn_group.checkedId() == 1 and files == [] and dirs == []:
                        _path = Path(root)
                        data = {
                            'dir': root.replace(path_dir, ''),
                            'cid': self.self_path_list,
                            'name': _path.name
                        }
                        # 開始上傳
                        self.upload_list.new_folder_add(data)
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
                if self.btn_group.checkedId() == 1:
                    self.upload_list.add(data)

    # 重新整理回調
    async def reorganize_callable(self) -> None:
        self.list_directory.set_refresh_gif_visible(True)
        self.all_cid_data[self.self_path_list]['refresh'] = True
        await create_task(self.network(cid=self.self_path_list, page=self.list_directory.qlist_data['page'], add=False))
        self.list_directory.set_refresh_gif_visible(False)

    # 窗口變化事件  最大化 還原
    def window_change(self, value: bool) -> None:
        # 根據目前窗口狀態 來決定是否 最大化 還原
        self.title_label.set_ico()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        # 如果是在首頁則允許拖曳
        if self.btn_group.checkedId() == 1 and self.self_path_list[0:3] != '搜索-':
            # 允許拖曳
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        file_path = event.mimeData().text()
        file_path = get_path(file_path.replace('file:///', '')).strip()
        if self.btn_group.checkedId() == 1 and self.self_path_list[0:3] != '搜索-':
            self.upload(file_path.split('\n'))

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        YFramelessWindow.resizeEvent(self, event)
        self.child_window.setGeometry(165, 0, self.content_widget.width(), self.content_widget.height())
        self.my_list_directory.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.download_list.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.aria2_list.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.upload_list.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.end_list.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.offline_list.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.share_list.resize(self.content_widget.width() - 165, self.content_widget.height())
        self.progressbar.setGeometry(20, self.height() - 55, 150, 13)
        self.progressbar_size.setGeometry(18, self.height() - 35, 150, 15)

    async def wait_close(self) -> None:
        while 1:
            if self.multi_progress is None:
                self.close()
                return
            if not self.multi_progress.is_alive():
                self.close()
                return
            await sleep(0.1)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.closes.value:
            with self.lock:
                all_data = self.all_data.copy()
            if all_data:
                with open('state.json', 'wb') as f:
                    pickle.dump(all_data, f)
            event.accept()
        else:
            self.closes.value = 1
            create_task(self.wait_close())
            event.ignore()


