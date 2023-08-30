import math
import re
from typing import Callable, Awaitable
from os.path import splitext
from asyncio import create_task, current_task, Future
from io import BytesIO

from PyQt5.Qt import QFrame, QLabel, QWidget, QResizeEvent, QLineEdit, QVBoxLayout, QTextEdit, QApplication, Qt,\
    QDialog, QHBoxLayout, QListWidgetItem, QAction, QContextMenuEvent, QRegExp, QPixmap, QPushButton, QIcon,\
    QRegExpValidator, QKeyEvent, pyqtSignal, QButtonGroup, QImage
from PIL import Image as PilImage

from .window import NFramelessWindow

from MyQlist.NText import Text
from MyQlist.DList import NListDirectory
from Modules.type import NTextData, NMyTextData, NTextSlots, MyTextSlots, NAllCidData, ErrorResult
from Modules.image import AllImage, Image, GifImage, IcoImage, get_ico
from Modules.widgets import MyIco, TextLabel, MyPushButton, RadioButton, SwitchBtn, Frame
from Modules.menu import Menu
from Modules.get_data import pybyte
from API.directory import Directory
from API.offline import Offline
from API.share import Share


def error(load: bool = False):
    def get_error(title, name, func, self, retry, *args, **kwargs) -> None:
        if Error.get(title, name) == 1 and retry:
            f1 = error(load)(func)(self, *args, **kwargs)
            create_task(f1)
        elif load:
            self.prohibit(True)

    def decorator(func: Callable[[any, any], Awaitable[ErrorResult]]):
        async def wrap(self=None, *args, state=True, **kwargs):
            if load:
                self.prohibit(False)
            result = await func(self, *args, **kwargs)
            retry = result['retry'] if 'retry' in result else True
            if result['state'] is False and state:
                current_task().add_done_callback(
                    lambda task: get_error(result['title'], result['name'], func, self, retry, *args, **kwargs)
                )
            elif load:
                self.prohibit(True)
            return result
        return wrap
    return decorator


# 瀏覽窗口
class FolderList(QDialog, NFramelessWindow):
    def __init__(self,  directory: Directory):
        super().__init__()
        title: QWidget = QWidget()
        title.resize(self.width(), 75)
        self.title_label: TextLabel = TextLabel(title, '', font_size=14, geometry=(30, 25, 250, 30))
        self.set_title(title)

        self.directory: Directory = directory
        # 初始化結果
        self.result: tuple[str, str] | None = None
        # 設置所有cid資料
        self.all_cid_data: dict[str, NAllCidData] = {}
        # 目前所在目錄
        self.self_path_list: str = '0'
        # 設置目前搜索cid
        self.search_cid: tuple[str, ...] | None = None
        # 設置上一頁目錄順序
        self.up_page_list: list[str, ...] = []
        # 設置下一頁目錄順序
        self.on_page_list: list[str, ...] = []
        # 獲取瀏覽視窗
        self.list_directory: NListDirectory = NListDirectory(self.content_widget)
        self.list_directory.setStyleSheet(
            'NList{border-style:solid; border-bottom-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )
        # 設置事件回調
        self.set_callable()
        # 禁止水平滾動條出現
        self.list_directory.scroll_area.set_horizontal(False)
        # 設置text點擊回調
        self.set_text_slot()
        self.setStyleSheet('FolderList{background-color:rgb(255,255,255)}')
        # 設置確認按鈕
        self.yes_button = MyPushButton(
            self.content_widget, '', (520, 411, 130, 40), qss=1, font_size=16, click=self.end
        )
        # 設置 新增文件夾 按鈕
        MyPushButton(
            self.content_widget, '新建資料夾', (20, 411, 130, 40), qss=2, font_size=16,
            click=lambda: self.get_enter('新建資料夾'),
        )
        # 設置 關閉按鈕
        MyIco(self, Image.BLACK_CLOSE, Image.BLUE_CLOSE, state=True, coordinate=(620, 35, 12, 12), click=self.close)

        # 設置任務欄圖標
        self.setWindowIcon(AllImage.get_ico(IcoImage.FAVICON))

        self.resize(674, 539)

    def stop(self, title_text: str, text: str) -> tuple[str, str]:
        # 初始化結果
        self.result: tuple[str, str] | None = None
        # 初始化所有目錄資料
        self.all_cid_data.clear()
        # 初始化目前所在目錄
        self.self_path_list: str = '0'
        # 初始化目前搜索cid
        self.search_cid: str = ''
        # 初始化上一頁目錄順序
        self.up_page_list.clear()
        # 初始化下一頁目錄順序
        self.on_page_list.clear()
        # 初始化所有介面的頁數資料
        self.list_directory.all_cls()
        # 設置標題名稱
        self.title_label.setText(title_text)
        # 設置確定按鈕名稱
        self.yes_button.setText(text)
        # 瀏覽窗口
        create_task(self.network('0'))
        # 顯示窗口
        self.exec()
        # 返回資料
        return self.result

    def end(self) -> None:
        if self.self_path_list[0:3] != '搜索-':
            self.result = self.self_path_list, self.all_cid_data[self.self_path_list]['path'][-1][0]
            self.close()

    # 設置text點擊回調
    def set_text_slot(self) -> None:
        text_slot_list: list[NTextSlots, ...] = []
        my_text_slots: MyTextSlots = MyTextSlots(connect_left_click=[self.click_callable], disconnect_left_click=None)
        n_text_slots: NTextSlots = NTextSlots(
            connect_left_click=None,
            connect_double_click=[self.click_callable],
            disconnect_left_click=None,
            disconnect_double_click=None,
            text=my_text_slots
        )
        for _ in range(self.list_directory.nlist_data['quantity_limit']):
            text_slot_list.append(n_text_slots)
        self.list_directory.set_text_slots(text_slot_list)

    # text點擊回調
    def click_callable(self, text: Text) -> None:
        create_task(self.network(text.text_data['data']['cid']))

    # 獲取輸入
    def get_enter(self, action: str) -> None:
        if action == '新建資料夾' and self.self_path_list[0:3] != '搜索-':
            if name := Enter.get('新建資料夾', '新名稱'):
                create_task(self.network(
                    self.self_path_list, page=self.list_directory.nlist_data['page'],
                    action=lambda: create_task(self.add_folder(self.self_path_list, name)),
                    add=False
                ))

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
        # 顯示等待動畫
        self.list_directory.set_load_visible(True)
        # 禁止操作
        # self.prohibit(False)
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
                    del self.list_directory.text.text_save_list.save[cid]

        # 查看 cid 是否不在 所有介面的頁數資料
        if cid not in self.list_directory.text.text_save_list.save:
            # 如果不再 則新增 新窗口
            self.list_directory.new(cid)
        elif cid != self.list_directory.text.text_name:
            self.list_directory.switch(cid)

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
                        self.list_directory.set_load_visible(False)
                        return
            self.add(cid, page)
            if cid[0:3] == '搜索-':
                self.list_directory.search_button_container.show()
        # 關閉等待動畫
        self.list_directory.set_load_visible(False)
        # 恢復操作
        # self.prohibit(True)

    # 刷新目錄
    @error()
    async def refresh(self, cid: str, page: int) -> ErrorResult:
        result = await self.directory.folder(
            cid, (page - 1) * self.list_directory.nlist_data['quantity_limit'],
            self.list_directory.nlist_data['quantity_limit']
        )
        if result:
            if cid != str(result['cid']):
                return ErrorResult(state=True, title='', name='', result='0')
            # 格式化115數據
            self.dumps(result, cid, page)
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='刷新介面錯誤', name='請問是否重新嘗試', result='')

    # 格式化115數據
    def dumps(self, items: dict, cid: str, page: int) -> None:
        index: dict[str, dict[str, any]] = {}
        text_data_list: list[NTextData, ...] = []

        for data in items['data']:
            # 獲取檔案cid
            data_cid = str(data['fid']) if 'fid' in data else str(data['cid'])
            # 獲取檔案cid
            data_ico = get_ico(splitext(data['n'])[1] if 'fid' in data else 'folder')
            # 獲取檔案cid
            data_size = data['s'] if 's' in data else '0'

            name_text_data: NMyTextData = NMyTextData(text=data['n'], color=((0, 0, 0), (6, 168, 255)), mouse=True)

            text_data: NTextData = NTextData(
                data={
                    'name': data['n'],
                    'category': '1' if 'fid' in data else '0',
                    'cid': data_cid,
                    'pid': data['pid'] if 'pid' in data else data['cid'],
                    'pc': data['pc'],
                    'sha1': data['sha'] if 'sha' in data else None,
                    'size': int(data_size),
                    'ico': data_ico,
                    'dp': data['dp'] if 'dp' in data else None,
                },
                ico=data_ico,
                text=name_text_data,
                mouse=True if data_ico == 'folder' else False
            )

            index[data['n']] = text_data['data']
            text_data_list.append(text_data)

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
                        'page': math.ceil(items['count'] / self.list_directory.nlist_data['quantity_limit'])}
                }
            )
        else:
            self.all_cid_data[cid]['data'][page] = text_data_list
            self.all_cid_data[cid]['index'].update(index)

    # 添加到窗口列表
    def add(self, cid: str, page: int) -> None:
        # 比對text資料
        def comparison() -> bool:
            return self.list_directory.get_text_data()[page] == self.all_cid_data[cid]['data'][page]

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
            if page != self.list_directory.quantity.nlist_data['page']:
                self.list_directory.quantity.set_page(page, callable=False)

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
                if comparison():
                    # 如果一樣則退出
                    return

        self.list_directory.add_text(self.all_cid_data[cid]['data'][page])

    @error()
    async def search(self, cid: str, page: int) -> ErrorResult:
        self.list_directory.lineedit.setText('')
        _cid, _, name = re.search('搜索-(.+)-(.+)-(.+)', cid).groups()
        result = await self.directory.search(
            name, _cid,
            (page - 1) * self.list_directory.nlist_data['quantity_limit'],
            self.list_directory.nlist_data['quantity_limit'],
        )
        if result:
            # 格式化115數據
            self.dumps(result, cid, page)
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='搜索錯誤', name='請問是否重新嘗試', result='')

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

    # 重新整理回調
    async def reorganize_callable(self) -> None:
        self.list_directory.set_refresh_gif_visible(True)
        self.all_cid_data[self.self_path_list]['refresh'] = True
        await create_task(self.network(cid=self.self_path_list, page=self.list_directory.nlist_data['page'], add=False))
        self.list_directory.set_refresh_gif_visible(False)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        NFramelessWindow.resizeEvent(self, event)
        self.list_directory.resize(self.content_widget.width(), self.content_widget.height() - 70)


class OfflineText(QTextEdit):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        # 右鍵菜單
        self.menu: Menu = Menu()

        copy = QAction(AllImage.get_ico(IcoImage.COPY), '複製')
        copy.triggered.connect(self.copy)
        self._copy: QListWidgetItem = self.menu.addAction(copy)

        cut = QAction(AllImage.get_ico(IcoImage.CUT), '剪下')
        cut.triggered.connect(self.cut)
        self._cut: QListWidgetItem = self.menu.addAction(cut)

        paste = QAction(AllImage.get_ico(IcoImage.PASTE), '貼上')
        paste.triggered.connect(self.paste)
        self._paste: QListWidgetItem = self.menu.addAction(paste)

        # 禁止富文本
        self.setAcceptRichText(False)
        # 禁止自動換行
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setStyleSheet('QTextEdit{border: 1px solid rgb(230, 230, 230); background-color: transparent}'
                           'QTextEdit:active{selection-background-color: rgb(151, 198, 235);'
                           'selection-color:rgb(0, 0, 0);font-family:Consolas;font-size:15px}'
                           )

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self.textCursor().selectionStart() != self.textCursor().selectionEnd():
            self.menu.set_item_enabled(self._copy, True)
            self.menu.set_item_enabled(self._cut, True)
        else:
            self.menu.set_item_enabled(self._copy, False)
            self.menu.set_item_enabled(self._cut, False)

        if QApplication.clipboard().text():
            self.menu.set_item_enabled(self._paste, True)
        else:
            self.menu.set_item_enabled(self._paste, False)

        self.menu.exec(event.globalPos())


class EnterText(QLineEdit):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        # 右鍵菜單
        self.menu: Menu = Menu()

        copy = QAction(AllImage.get_ico(IcoImage.COPY), '複製')
        copy.triggered.connect(self.copy)
        self._copy: QListWidgetItem = self.menu.addAction(copy)

        cut = QAction(AllImage.get_ico(IcoImage.CUT), '剪下')
        cut.triggered.connect(self.cut)
        self._cut: QListWidgetItem = self.menu.addAction(cut)

        paste = QAction(AllImage.get_ico(IcoImage.PASTE), '貼上')
        paste.triggered.connect(self.paste)
        self._paste: QListWidgetItem = self.menu.addAction(paste)

        self.setStyleSheet('EnterText{border: 1px solid rgb(230, 230, 230); background-color: transparent;font-size:15px}'
                           'EnterText:active{selection-background-color: rgb(151, 198, 235);'
                           'selection-color:rgb(0, 0, 0);font-family:Consolas}'
                           )

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self.selectionStart() != self.selectionEnd():
            self.menu.set_item_enabled(self._copy, True)
            self.menu.set_item_enabled(self._cut, True)
        else:
            self.menu.set_item_enabled(self._copy, False)
            self.menu.set_item_enabled(self._cut, False)

        if QApplication.clipboard().text():
            self.menu.set_item_enabled(self._paste, True)
        else:
            self.menu.set_item_enabled(self._paste, False)

        self.menu.exec(event.globalPos())


class EnterOffline(QDialog, NFramelessWindow):
    def __init__(self, offline: Offline, folder_list: FolderList) -> None:
        super().__init__()
        # 設置窗口大小
        self.resize(720, 320)
        # 設置背景空白 QSS
        self.setStyleSheet('EnterOffline{background-color: rgb(255, 255, 255)}')
        # 設置瀏覽資料夾窗口
        self.folder_list: FolderList = folder_list
        # 115目錄API
        self.offline: Offline = offline
        # 設置標題窗口
        title: QWidget = QWidget()
        # 設置標題窗口大小
        title.resize(self.width(), 75)
        # 設置標題
        TextLabel(title, '添加離線鏈結', font_size=14, geometry=(30, 25, 120, 30))
        # 更新標題 到 主窗口
        self.set_title(title)
        # 115cid
        self.cid: str = ''
        # 設置文字輸入框
        self.text = OfflineText(self.content_widget)
        # 設置文字輸入框大小
        self.text.setGeometry(30, 0, 660, 175)
        # 設置保存在哪文字框
        self.save_text = TextLabel(self.content_widget, '保存到：云下载', font_size=12, move=(30, 200))
        # 設置更改目錄按鈕
        self.button: MyPushButton = MyPushButton(
            self.content_widget, '更改目錄', (self.save_text.x() + self.save_text.width() + 10, 194, 80, 30),
            qss=2, font_size=16, click=self.folder
        )
        # 設置 開始離線按鈕
        self.yes_button: MyPushButton = MyPushButton(
            self.content_widget, '開始離線下載', (540, 190, 150, 40), qss=1,
            font_size=16, click=lambda: create_task(self.start()),
        )
        # 設置 關閉按鈕
        self.closure_button: MyIco = MyIco(
            self, Image.BLACK_CLOSE, Image.BLUE_CLOSE, state=True, coordinate=(670, 35, 12, 12), click=self.close
        )
        # 設定 等待GIF
        self.load = AllImage.get_gif(
            self,
            GifImage.MAX_LOAD,
            (int((self.width() - 32) / 2), int((self.height() - 32) / 2), 32, 32)
        )
        # 設置任務欄圖標
        self.setWindowIcon(AllImage.get_ico(IcoImage.FAVICON))

    def folder(self) -> None:
        if data := self.folder_list.stop('選擇要保存的資料夾', '保存到這裡'):
            self.cid, name = data
            self.save_text.setText(f'保存到：{name}')
            self.save_text.adjustSize()
            self.button.move(self.save_text.x() + self.save_text.width() + 10, 194)

    @classmethod
    def get(cls, offline: Offline, folder_list: FolderList) -> None:
        offline = cls(offline, folder_list)
        offline.exec()

    # 禁止操作
    def prohibit(self, mode: bool) -> None:
        # 是否顯示 等待動畫
        self.load.setVisible(not mode)
        self.content_widget.setEnabled(mode)

    async def start(self) -> None:
        result = self.text.toPlainText()
        if result.find('\n') != -1:
            _result = []
            for text in result.split('\n'):
                if text:
                    _result.append(text)
            result = _result
        if result:
            create_task(self.add_offline(result))

    @error(True)
    async def add_offline(self, text: str) -> ErrorResult:
        result = await self.offline.add_offline(text, self.cid)
        if result == -1:
            return ErrorResult(state=False, title='網路異常新增離線任務失敗', name='請問是否重新嘗試', result='')
        elif result == 0:
            current_task().add_done_callback(self.get_captcha)
            return ErrorResult(state=True, title='', name='', result='')
        self.accept()
        return ErrorResult(state=True, title='', name='', result='')

    def get_captcha(self, task: Future):
        Captcha.get(self.offline)


class Error(QDialog, NFramelessWindow):
    def __init__(self, title_text: str, name_text: str) -> None:
        super().__init__()
        # 設置結果
        self.result: str = ''
        # 設置 標題
        title_widget: QLabel = QLabel(self)
        # 設置 標題文字
        title_widget.setText(title_text)
        # 設置 標題大小
        title_widget.setFixedHeight(30)
        # 設置 標題qss
        title_widget.setStyleSheet(
            """
            QLabel{
                background-color:rgb(243, 243, 243);
                font: 14px 'Segoe UI', 'Microsoft YaHei';
                padding: 5px 9px 6px 9px;
                }
            """
        )
        # 設置 標題 到 主介面
        self.set_title(title_widget,  set_size=False)
        # 設置 背景空白 QSS
        self.setStyleSheet('Error{background-color:rgb(255, 255, 255)}')
        # 設置 全部布局
        self.box_layout = QVBoxLayout(self)
        # 設置 全部布局 間隔為0
        self.box_layout.setSpacing(0)
        # 設置 全部布局 內容邊距 大小
        self.box_layout.setContentsMargins(0, 0, 0, 0)
        # 設置 內容布局
        self.text_layout = QHBoxLayout()
        # 設置 內容布局 間隔為10
        self.text_layout.setSpacing(10)
        # 設置 內容布局 內容邊距 大小
        self.text_layout.setContentsMargins(10, 10, 10, 10)
        # 設置 按鈕組
        self.button_group = QFrame(self.content_widget)
        # 設置 按鈕組 QSS
        self.button_group.setStyleSheet(
            """
            QFrame{
                background-color: rgb(243, 243, 243);
                border-top: 1px solid rgb(229, 229, 229);
                border-left: none;
                border-right: none;
                border-bottom: none;
                }
            """
        )
        # 設置 按鈕布局
        self.button_layout = QHBoxLayout(self.button_group)
        # 設置 確認按鈕
        self.yes_button = MyPushButton(
            None, '確認', qss=1, font='Microsoft YaHei',
            font_size=16,  padding=(5, 9, 6, 9), click=self.yes_button_clicked
        )
        # 設置 取消按鈕
        self.cancel_button = MyPushButton(
            None, '取消', qss=2, font='Microsoft YaHei',
            font_size=16,  padding=(5, 9, 6, 9), click=self.cancel_button_clicked
        )
        # 添加 確認按鈕 到按鈕布局
        self.button_layout.addWidget(self.yes_button)
        # 添加 取消按鈕 到按鈕布局
        self.button_layout.addWidget(self.cancel_button)
        # 設置 內容
        self.text_label = QLabel(name_text, self.content_widget)
        # 設置 內容 QSS
        self.text_label.setStyleSheet("font: 20px 'Segoe UI', 'Microsoft YaHei';padding: 0;")
        # 設置 警告圖片容器
        label: QLabel = QLabel()
        # 設置警告圖片
        label.setPixmap(AllImage.get_image(Image.WARNINGS))
        # 添加 警告圖片 到 內容布局
        self.text_layout.addWidget(label)
        # 添加 內容 到 內容布局
        self.text_layout.addWidget(self.text_label)
        # 添加 標題 到 全部布局
        self.box_layout.addWidget(self.title_widget)
        # 添加 內容布局 到 全部布局
        self.box_layout.addLayout(self.text_layout, 1)
        # 添加 按鈕組 到 全部布局
        self.box_layout.addWidget(self.button_group)

    @classmethod
    def get(cls, title_text: str, name_text: str) -> int:
        return cls(title_text, name_text).exec()

    def yes_button_clicked(self) -> None:
        self.accept()

    def cancel_button_clicked(self) -> None:
        self.reject()


class Enter(QDialog, NFramelessWindow):
    def __init__(self, title_text: str, name_text: str):
        super().__init__()
        # 設置結果
        self.result: str = ''
        # 設置 標題
        self.title_widget: QLabel = QLabel(self)
        # 設置 標題文字
        self.title_widget.setText(title_text)
        # 設置 標題大小
        self.title_widget.setFixedHeight(30)
        # 設置 標題qss
        self.title_widget.setStyleSheet("""
        QLabel{
            background-color:rgb(243, 243, 243);
            font: 14px 'Segoe UI', 'Microsoft YaHei';
            padding: 5px 9px 6px 9px;
            }
            """
                                        )
        # 設置 標題 到 主介面
        self.set_title(self.title_widget, set_size=False)
        # 設置 背景空白 QSS
        self.setStyleSheet('Enter{background-color:rgb(255, 255, 255)}')
        # 設置 全部布局
        self.box_layout = QVBoxLayout(self)
        # 設置 全部布局 間隔為0
        self.box_layout.setSpacing(0)
        # 設置 全部布局 內容邊距 大小
        self.box_layout.setContentsMargins(0, 0, 0, 0)
        # 設置 內容布局
        self.text_layout = QVBoxLayout()
        # 設置 內容布局 間隔為10
        self.text_layout.setSpacing(10)
        # 設置 內容布局 內容邊距 大小
        self.text_layout.setContentsMargins(10, 10, 10, 10)
        # 設置 按鈕組
        self.button_group = QFrame(self.content_widget)
        # 設置 按鈕組 QSS
        self.button_group.setStyleSheet("""
        QFrame{
            background-color: rgb(243, 243, 243);
            border-top: 1px solid rgb(229, 229, 229);
            border-left: none;
            border-right: none;
            border-bottom: none;
        }
        """
                                        )

        # 設置 按鈕布局
        self.button_layout = QHBoxLayout(self.button_group)
        # 設置 按鈕布局 間隔為10
        self.button_layout.setSpacing(10)
        # 設置 確認按鈕
        self.yes_button = MyPushButton(
            self.button_group, '確認', qss=1, font='Microsoft YaHei',
            font_size=14,  padding=(5, 9, 6, 9), click=self.yes_button_clicked
        )
        # 設置 取消按鈕
        self.cancel_button = MyPushButton(
            self.button_group, '取消', qss=2, font='Microsoft YaHei',
            font_size=14,  padding=(5, 9, 6, 9), click=self.cancel_button_clicked
        )
        # 設置 標題
        self.title_label = QLabel(name_text, self.content_widget)
        # 設置 標題 QSS
        self.title_label.setStyleSheet("QLabel{font: 20px 'Segoe UI', 'Microsoft YaHei';padding: 0;}")
        # 設置 輸入框
        self.line_edit: EnterText = EnterText(self.content_widget)
        # 添加 確認按鈕 到按鈕布局
        self.button_layout.addWidget(self.yes_button)
        # 添加 取消按鈕 到按鈕布局
        self.button_layout.addWidget(self.cancel_button)
        # 添加 標題 到 內容布局
        self.text_layout.addWidget(self.title_label)
        # 添加 輸入框 到 內容布局
        self.text_layout.addWidget(self.line_edit)
        # 添加 標題 到 全部布局
        self.box_layout.addWidget(self.title_widget)
        # 添加 內容布局 到 全部布局
        self.box_layout.addLayout(self.text_layout)
        # 添加 按鈕組 到 全部布局
        self.box_layout.addWidget(self.button_group)

    @classmethod
    def get(cls, title_text: str, name_text: str) -> str:
        enter = cls(title_text, name_text)
        enter.exec()
        return enter.result

    def yes_button_clicked(self) -> None:
        self.accept()
        self.result = self.line_edit.text()

    def cancel_button_clicked(self) -> None:
        self.reject()

    def exec(self) -> int:
        self.line_edit.setFocus()
        return QDialog.exec(self)


class Captcha(QDialog, NFramelessWindow):
    captcha_widget_qss = """
    QLabel {
        background-color: rgb(245, 245, 245);
    }"""

    def __init__(self, offline: Offline) -> None:
        super().__init__()
        # 設置窗口大小
        self.resize(320, 390)
        self.setStyleSheet('Captcha{background-color: white}')
        # 設置標題窗口
        title: QWidget = QWidget()
        title.setStyleSheet('QWidget{background-color: rgb(255, 140, 2)}')
        # 設置標題窗口大小
        title.resize(self.width(), 75)
        # 設置標題
        title_label: TextLabel = TextLabel(title, '帳號使用異常 請重新驗證', font_size=14, geometry=(30, 25, 300, 30))
        title_label.setStyleSheet('TextLabel{color: white}')
        # 更新標題 到 主窗口
        self.set_title(title)

        self.image_labels = []

        for index in range(0, 4):
            label = QLabel(self.content_widget)
            label.setStyleSheet(self.captcha_widget_qss)
            label.setGeometry(30 + index * 50 + 2 * index, 20, 50, 50)
            self.image_labels.append(label)

        # 設置 關閉按鈕
        self.closure_button: MyIco = MyIco(
            self.content_widget, Image.GREY_Revoke, Image.BLACK_Revoke, state=True,
            coordinate=(241, 20, 50, 50), click=self.del_image
        )

        self.code_label = QLabel(self.content_widget)
        self.code_label.setGeometry(30, 80, 144, 46)
        self.code_label.setStyleSheet(self.captcha_widget_qss)

        self.refresh_button = MyPushButton(
            self.content_widget, '看不清? 換一個', qss=3, font_size=15, move=(180, 95), click=self.refresh
        )

        self.code_map_label = QLabel(self.content_widget)
        self.code_map_label.setGeometry(30, 136, 250, 100)
        self.code_map_label.setStyleSheet(self.captcha_widget_qss)

        for i, index in zip((0, 1, 2, 3, 4, 0, 1, 2, 3, 4), range(10)):
            label = QPushButton(self.code_map_label)
            label.setObjectName(str(index))
            label.setStyleSheet('border: 0px')
            label.clicked.connect(self.set_image)
            label.setGeometry(i * 50, 0 if index < 5 else 50, 50, 50)

        self.yes_button = MyPushButton(
            self.content_widget, '確定', (30, 246, 120, 50), font_size=16, qss=1, click=lambda: create_task(self.yes())
        )
        self.cancel_button = MyPushButton(
            self.content_widget, '取消', (160, 246, 120, 50), font_size=16, qss=2, click=self.reject
        )
        # 設定 等待GIF
        self.load = AllImage.get_gif(
            self,
            GifImage.MAX_LOAD,
            (int((self.width() - 32) / 2), int((self.height() - 32) / 2), 32, 32)
        )
        self.cb: str = ''
        self.sing: str = ''
        self.code: str = ''
        self.index: int = 0
        self.offline: Offline = offline

    @classmethod
    def get(cls, offline: Offline):
        captcha = cls(offline)
        create_task(captcha.get_image())
        captcha.exec()

    # 禁止操作
    def prohibit(self, mode: bool) -> None:
        self.load.setVisible(not mode)
        self.content_widget.setEnabled(mode)

    @error(True)
    async def get_image(self) -> ErrorResult:
        if self.cb == '':
            result = await self.offline.security()
            if result is False:
                return ErrorResult(state=False, title='獲取驗證資訊失敗', name='請問是否重新獲取', result='')
            self.cb, self.sing = result
        code_image = await self.offline.verification_code()
        if code_image is False:
            return ErrorResult(state=False, title='獲取驗證圖片失敗', name='請問是否重新獲取', result='')
        bytes_stream = BytesIO(code_image)
        image = PilImage.open(bytes_stream).convert()
        im = image.convert("RGBA")
        data = im.tobytes("raw", "RGBA")
        qim = QPixmap.fromImage(QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888))
        self.code_label.setPixmap(qim)

        all_image = await self.offline.verification_map()
        if all_image is False:
            return ErrorResult(state=False, title='獲取所有驗證圖片失敗', name='請問是否重新獲取', result='')
        bytes_stream = BytesIO(all_image)
        image = PilImage.open(bytes_stream)
        image.save(r'r:\1.png')
        for i, index in zip((0, 1, 2, 3, 4, 0, 1, 2, 3, 4), range(10)):
            box = (i * 50, 0 if index < 5 else 50, (i + 1) * 50, 50 if index < 5 else 100)
            img = image.crop(box)
            im = img.convert("RGBA")
            data = im.tobytes("raw", "RGBA")
            qim = QPixmap.fromImage(QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888))

            label: QPushButton = self.code_map_label.findChild(QPushButton, str(index))
            label.setIcon(QIcon(qim))
            label.setIconSize(qim.rect().size())
            label.show()
        return ErrorResult(state=True, title='', name='', result='')

    def set_image(self) -> None:
        if self.index == 4:
            return
        index = self.sender().objectName()
        self.image_labels[self.index].setPixmap(self.sender().icon().pixmap(50, 50))
        self.code += index
        self.index += 1

    def del_image(self) -> None:
        if self.index == 0:
            return
        self.index -= 1
        self.image_labels[self.index].setPixmap(QPixmap(""))
        self.code = self.code[:-1]

    @error(True)
    async def yes(self) -> ErrorResult:
        if len(self.code) == 4:
            result = await self.offline.captcha(self.code, self.sing, self.cb)
            if result == -1:
                self.accept()
                return ErrorResult(state=False, title='網路異常驗證失敗', name='請問是否重新嘗試', result='')
            elif result == 0:
                return ErrorResult(state=False, title='錯誤', name='驗證碼錯誤', result='', retry=False)
        return ErrorResult(state=True, title='', name='', result='')

    def refresh(self) -> None:
        self.code_label.setPixmap(QPixmap(""))
        for label in self.code_map_label.children():
            label.setIcon(QIcon())
        create_task(self.get_image())


class CodeLineEdit(QLineEdit):
    # 按鍵輸入信號
    key_press_enter = pyqtSignal(QKeyEvent)

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setMaxLength(1)
        self.setValidator(QRegExpValidator(QRegExp('[a-zA-Z0-9]+$')))
        self.setStyleSheet(
                'border: 2px solid rgb(230, 230, 230); background-color: transparent;'
                'font-size:30px;qproperty-alignment:AlignHCenter'
            )

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)
        self.key_press_enter.emit(event)


class ReceiveCode(QDialog, NFramelessWindow):
    def __init__(self, share_code: str, receive_code: str) -> None:
        super().__init__()
        # 設置標題窗口
        title: QWidget = QWidget()
        # 設置標題窗口大小
        title.resize(self.width(), 75)
        # 設置標題
        TextLabel(title, '變更訪問碼', font_size=14, geometry=(30, 25, 300, 30))
        # 設置離線標題文字
        TextLabel(
            title, f'當前訪問碼: {receive_code}', font_size=14, geometry=(300, 25, 150, 30)
        )
        # 設置 關閉按鈕
        MyIco(
            title, Image.BLACK_CLOSE, Image.BLUE_CLOSE, state=True, coordinate=(460, 35, 12, 12), click=self.accept
        )
        # 更新標題 到 主窗口
        self.set_title(title)

        self.share_code: str = share_code
        self.result: str = ''

        self.line_edit_list: list[CodeLineEdit, ...] = []

        for index in range(0, 4):
            line_edit = CodeLineEdit(self.content_widget)
            line_edit.key_press_enter.connect(self.text_changed)
            line_edit.setGeometry(120 + index * 50 + 20 * index, 20, 50, 50)
            self.line_edit_list.append(line_edit)

        label = QLabel('*新訪問碼統一4位, 只允許輸入字母和數字', self.content_widget)
        label.setStyleSheet('color: red; font-size: 16px')
        label.move(100, 100)

        MyPushButton(self.content_widget, '取消', font_size=16, qss=2, geometry=(190, 145, 130, 40), click=self.accept)
        MyPushButton(
            self.content_widget, '確認', font_size=16, qss=1,
            geometry=(338, 145, 130, 40), click=self.yes)

        self.setStyleSheet('ReceiveCode{background-color: rgb(255, 255, 255)}')
        self.resize(500, 290)

    def yes(self) -> None:
        receive_code = ''.join([text.text() for text in self.line_edit_list])
        if len(receive_code) == 4:
            self.result = receive_code
            self.accept()

    def text_changed(self, event: QKeyEvent) -> None:
        index = self.line_edit_list.index(self.sender())
        if event.key() == Qt.Key_Backspace and index != 0:
            self.line_edit_list[index - 1].setFocus()
        elif event.key() != Qt.Key_Backspace and event.text() != '' and index != 3:
            self.line_edit_list[index + 1].setFocus()

    @classmethod
    def get(cls, share_code: str, receive_code: str) -> str:
        enter = cls(share_code, receive_code)
        enter.exec()
        return enter.result


class EnterShare(QDialog, NFramelessWindow):
    def __init__(
            self,
            share: Share,
            file_name: str,
            file_size: int,
            share_code: str,
            url: str,
            custom_receive_code: str,
            receive_code: str,
            sys_receive_code: str
    ) -> None:
        super().__init__()
        # 設置標題窗口
        title: QWidget = QWidget()
        # 設置標題窗口大小
        title.resize(self.width(), 70)
        # 設置標題
        TextLabel(title, '分享文件', font_size=14, geometry=(30, 25, 300, 30))
        # 設置 關閉按鈕
        MyIco(
            title, Image.BLACK_CLOSE, Image.BLUE_CLOSE, state=True, coordinate=(370, 35, 12, 12), click=self.close
        )
        # 更新標題 到 主窗口
        self.set_title(title)
        # 115api
        self.share: Share = share
        # 分享url
        self.url: str = url
        # 接收碼
        self.receive_code: str = receive_code
        # 分享文件id
        self.share_code: str = share_code

        self.widget: QWidget = QWidget(self.content_widget)
        self.widget.setGeometry(30, 0, 350, 200)
        self.widget.setStyleSheet('QWidget{background-color: rgb(240, 240, 240)}')

        self.ico = QLabel(self.widget)
        self.ico.setPixmap(AllImage.get_image(Image.MAX_APK))
        self.ico.move(10, 10)

        TextLabel(self.widget, file_name, font_size=14, move=(45, 14))

        TextLabel(self.widget, '文件大小 :', font_size=12, move=(45, 50))

        TextLabel(self.widget, pybyte(file_size), font_size=12, move=(130, 50))

        TextLabel(self.widget, '有效期限 :', font_size=12, move=(45, 80))

        TextLabel(self.widget, '長期', font_size=12, move=(130, 80))

        time_data = (('1天', 130, False, 1), ('7天', 190, False, 7), ('長期', 250, True, 0))
        self.time_group = QButtonGroup(self)
        self.time_group.idClicked.connect(lambda _id: create_task(self.set_switch_time(_id)))
        for data in time_data:
            time_radio_button = RadioButton(
                self.widget, data[0], font_size=12, move=(data[1], 110), checked=data[2]
            )
            self.time_group.addButton(time_radio_button, data[3])
        self.currently_time_button: RadioButton = self.time_group.buttons()[-1]
        self.currently_code_button: RadioButton | None = None

        TextLabel(self.widget, text='訪問碼 :', font_size=12, move=(61, 140))

        self.file_code: TextLabel | None = None
        self.file_code_group: QButtonGroup | None = None
        self.change_button = MyPushButton(
            self.widget, geometry=(170, 143, 15, 15),
            icon=AllImage.get_ico(IcoImage.CHANGE),
            click=lambda: create_task(self.set_receive_code(ReceiveCode.get(self.share_code, self.receive_code)))
        )

        if custom_receive_code == '':
            self.file_code = TextLabel(self.widget, text=receive_code, font_size=12, move=(130, 140))
        else:
            self.set_file_code_group(sys_receive_code, custom_receive_code)

        TextLabel(self.widget, '分享鏈結自動填充口令', font_size=12, move=(45, 170))

        self.switch_btn = SwitchBtn(self.widget, geometry=(210, 168, 50, 20), click=self.switch_state)

        Frame(self.content_widget, geometry=(30, 215, 350, 1))

        self.url_line = QLineEdit(self.content_widget)
        self.url_line.setFocusPolicy(Qt.NoFocus)
        self.url_line.setContextMenuPolicy(Qt.NoContextMenu)
        self.url_line.setGeometry(30, 230, 240, 40)
        self.url_line.setStyleSheet(
            'QLineEdit{border: 1px solid rgb(230, 230, 230); background-color: transparent; font-size:25px}'
            'QLineEdit:active{selection-background-color: rgb(151, 198, 235);'
            'selection-color:rgb(0, 0, 0);font-family:Consolas}'
        )
        self.switch_state(self.switch_btn.checked)

        # 設置確認按鈕
        self.yes_button = MyPushButton(
            self.content_widget, '複製', (280, 230, 100, 40), qss=1, font_size=16,
            click=lambda: QApplication.clipboard().setText(self.url_line.text())
        )

        self.resize(410, 370)

        # 設定 等待GIF
        self.load = AllImage.get_gif(
            self,
            GifImage.MAX_LOAD,
            (int((self.width() - 32) / 2), int((self.height() - 32) / 2), 32, 32)
        )

        self.setStyleSheet('EnterShare{background-color: rgb(255, 255, 255)}')

    # 禁止操作
    def prohibit(self, mode: bool) -> None:
        # 是否顯示 等待動畫
        self.load.setVisible(not mode)
        self.content_widget.setEnabled(mode)

    def set_file_code_group(self, sys_receive_code: str, custom_receive_code: str) -> None:
        time_a = RadioButton(
            self.widget, sys_receive_code, font_size=12, move=(130, 140),
            click=lambda: create_task(self.switch_receive_code(time_a))
        )
        time_a.adjustSize()
        time_b = RadioButton(
            self.widget, custom_receive_code, font_size=12, move=(time_a.x() + time_a.width() + 3, 140),
            click=lambda: create_task(self.switch_receive_code(time_b)), checked=True
        )
        self.file_code_group = QButtonGroup(self)
        self.file_code_group.addButton(time_a)
        self.file_code_group.addButton(time_b)
        self.change_button.move(time_b.x() + time_b.width() + 3, 143)
        self.currently_code_button = time_b

    @error()
    async def set_receive_code(self, receive_code: str) -> ErrorResult:
        if receive_code:
            self.prohibit(False)
            result = await self.share.set_receive_code(self.share_code, receive_code)
            self.prohibit(True)
            if result:
                self.receive_code = receive_code
                self.switch_state(self.switch_btn.checked)
                if self.file_code_group is None:
                    self.set_file_code_group(self.receive_code, receive_code)
                button = self.file_code_group.buttons()[-1]
                button.setChecked(True)
                button.setText(receive_code)
                button.adjustSize()
                self.change_button.move(button.x() + button.width() + 3, 143)
                return ErrorResult(state=True, title='', name='', result='')
            return ErrorResult(state=False, title='網路異常設定訪問碼錯誤', name='請問是否重新嘗試', result='')
        return ErrorResult(state=True, title='', name='', result='')

    @error()
    async def set_switch_time(self, share_time: int) -> ErrorResult:
        if share_time == 0:
            share_time = -1
        self.prohibit(False)
        result = await self.share.set_share_time(self.share_code, share_time)
        self.prohibit(True)
        if result:
            self.currently_time_button = self.time_group.checkedButton()
            return ErrorResult(state=True, title='', name='', result='')
        self.currently_time_button.setChecked(True)
        return ErrorResult(state=False, title='網路異常設定時間失敗', name='請問是否重新嘗試', result='')

    @error()
    async def switch_receive_code(self, receive_code_button: RadioButton) -> ErrorResult:
        self.prohibit(False)
        result = await self.share.switch_receive_code(self.share_code, receive_code_button.text())
        self.prohibit(True)
        if result:
            self.receive_code = receive_code_button.text()
            self.currently_code_button = receive_code_button
            self.switch_state(self.switch_btn.checked)
            return ErrorResult(state=True, title='', name='', result='')
        self.currently_code_button.setChecked(True)
        return ErrorResult(state=False, title='網路異常設定時間失敗', name='請問是否重新嘗試', result='')

    def switch_state(self, checked: bool) -> None:
        if checked:
            self.url_line.setText(f'{self.url}?password={self.receive_code}')
        else:
            self.url_line.setText(f'{self.url}')
        self.url_line.home(False)

    @classmethod
    def get(
            cls,
            share: Share,
            file_name: str,
            file_size: int,
            share_code: str,
            url: str,
            custom_receive_code: str,
            receive_code: str,
            sys_receive_code: str
    ) -> None:
        enter = cls(
            share, file_name, file_size, share_code, url,
            custom_receive_code,receive_code, sys_receive_code
        )
        enter.exec()
