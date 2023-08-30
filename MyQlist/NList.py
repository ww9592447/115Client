from typing import Callable

from PyQt5.Qt import QFrame, pyqtSignal, QWidget, Qt, QApplication, QLabel, QContextMenuEvent,\
    QListWidgetItem, QIcon, QAction, QMouseEvent, QResizeEvent

from .MScroolBar import ScrollArea
from .NText import QText

from Modules.type import NTextData, NlistData, NTextSlots
from Modules.image import GifLabel, AllImage, Image, GifImage
from Modules.widgets import MyIco
from Modules.menu import Menu


# 可視窗口容器
class VisualContents(QWidget):
    load: GifLabel

    def __init__(self) -> None:
        super().__init__()
        self.load: GifLabel = AllImage.get_gif(self, GifImage.MIN_LOAD)
        self.load.resize(20, 20)
        self.load.hide()

    def set_load_visible(self, visible: bool) -> None:
        if visible:
            self.load.raise_()
        self.load.setVisible(visible)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.load.move(
            int((self.width() - self.load.width()) / 2),
            int((self.height() - self.load.height()) / 2)
        )


# 所有容器
class AllWidget(QWidget):
    # 背景右鍵菜單
    context_menu: Menu
    # 所有背景右鍵菜單
    menu: dict[str, QListWidgetItem] = {}
    # 背景右鍵回調
    menu_callable: Callable[[], bool] = None

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        # 設置背景右鍵菜單
        self.context_menu = Menu()

    # 右鍵事件
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self.menu:
            if self.menu_callable:
                if self.menu_callable():
                    self.context_menu.exec(event.globalPos())
            else:
                self.context_menu.exec(event.globalPos())



class Page(QLabel):
    # 左鍵單擊
    left_click = pyqtSignal(int)

    def __init__(self, parent: QWidget, text: str, geometry: tuple[int, ...], state: bool) -> None:
        super().__init__(parent)
        # 設定自身頁數
        self.setText(text)
        # 設定自身大小
        self.setGeometry(*geometry)
        # 設定字體置中
        self.setAlignment(Qt.AlignCenter)
        # 查看 目前狀態是否能夠點擊
        if not state:
            # 根據狀態 設定成 是否能夠點擊
            self.setCursor(Qt.PointingHandCursor)
        # 自訂 狀態屬性
        self.setProperty('state', state)
        # 設定 qss
        self.setStyleSheet('Page{color:rgb(153, 153, 171);}'
                           'Page:hover{color:rgb(6,168,255);}'
                           'Page[state="true"]{color:rgb(6,168,255);}')
        # 顯示
        self.show()

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.left_click.emit(int(self.text()))


class MyScrollArea(ScrollArea):
    def __init__(
            self,
            parent: QWidget,
            visual_contents: QWidget | None = None,
            scroll_contents: QWidget | None = None,
            scroll_size: int = 14,
            single_step: int = 20,
            page_step: int = 60,
            interval: int = 5,
            arrow: bool = True
    ) -> None:
        super().__init__(parent, visual_contents, scroll_contents, scroll_size, single_step, page_step, interval, arrow)

    def scroll_contents_size_by(self) -> None:
        self.scroll_contents.resize(self.visual_contents.width(), self.scroll_contents.height())


class Quantity(QFrame):
    def __init__(
            self,
            parent: QWidget,
            nlist_data: NlistData,
            scroll_area: MyScrollArea,
            text: QText
    ) -> None:
        super().__init__(parent)
        # 設置所有nlist資料
        self.nlist_data: NlistData = nlist_data
        self.text = text
        self.scroll_area: MyScrollArea = scroll_area
        # 設定最大頁數
        self.page_max: int = 1
        # 設置總共多少 text 數量UI
        self.all_text: QLabel = QLabel(self)
        # 設置文字顏色
        self.all_text.setStyleSheet('color:rgb(153, 153, 171)')
        # 設定預設文字
        self.all_text.setText('0項')
        # 自動調整成符合大小
        self.all_text.adjustSize()
        # 設置所有頁數容器
        self.all_page: QWidget = QWidget(self)
        # 所有頁數容器隱藏
        self.all_page.hide()
        # 獲取第一頁UI
        page: Page = Page(self.all_page, '1', (16, 0, 10, 18), True)
        # 連接第一頁UI信號
        page.left_click.connect(self.set_page)
        # 設置頁數列表
        self.page_list: list[Page, ...] = []
        # 頁數列表 新增第一頁
        self.page_list.append(page)
        # 設置總共頁數UI
        self.page_text = QLabel(self.all_page)
        # 設置總共頁數UI顏色
        self.page_text.setStyleSheet('color:rgb(153, 153, 171)')
        # 設置總共頁數UI位置
        self.page_text.move(0, 4)
        # 設置上一頁按鈕
        self.up_ico: MyIco = MyIco(
            self.all_page,
            Image.MIN_GREY_PREVIOUS_PAGE,
            Image.MIN_BLUE_PREVIOUS_PAGE,
            state=True,
            coordinate=(0, 0, 10, 17),
            click=lambda: self.set_page(self.nlist_data['page'] - 1, True)
        )
        # 上一頁按鈕隱藏
        self.up_ico.hide()
        # 設置下一頁按鈕
        self.on_ico: MyIco = MyIco(
            self.all_page,
            Image.MIN_GREY_NEXT_PAGE,
            Image.MIN_BLUE_NEXT_PAGE,
            state=True,
            coordinate=(0, 0, 10, 17),
            click=lambda: self.set_page(self.nlist_data['page'] + 1, True)
        )
        # 下一頁按鈕隱藏
        self.on_ico.hide()
        # 設置統計容器 上方邊框 顏色
        self.setStyleSheet('Quantity{border-style:solid; border-top-width:1px; border-color:rgba(200, 200, 200, 125)}')

    # 設置頁數上限
    def set_all_page(self, index: int) -> None:
        # 獲取目前頁數
        value = len(self.page_list) + 1
        while len(self.page_list) < index:
            # 獲取目前頁數UI
            page = Page(self.all_page, str(value), (16 * value, 0, 10, 18), False)
            # 連接目前頁數UI信號
            page.left_click.connect(self.set_page)
            # 添加置頁數列表
            self.page_list.append(page)
            # 目前頁數 + 1
            value += 1
        # 設定最大頁數
        self.page_max: int = index
        # 頁數顯示
        for page in self.page_list[0:index]:
            # 頁數顯示
            page.show()
        # 設置 多餘的 頁數 隱藏
        for page in self.page_list[index:]:
            # 頁數隱藏
            page.hide()
        self.checking_page()

    # 設置成第幾頁
    def set_page(self, value: int, callable: bool = True) -> None:
        # 獲取頁數
        page: Page = self.page_list[value - 1]
        # 獲取舊的頁數按鈕
        _page: Page = self.page_list[self.nlist_data['page'] - 1]
        # 設定新頁數
        self.nlist_data['page'] = value
        # 設定舊的頁數按鈕成可以互動的狀態
        _page.setProperty('state', False)
        # 設定新的頁數按鈕成不能互動的狀態
        page.setProperty('state', True)
        # 刷新舊的頁數按鈕QSS
        _page.setStyle(_page.style())
        # 刷新新的頁數按鈕QSS
        page.setStyle(_page.style())
        # 設定舊的頁數按鈕滑鼠數標成可點擊狀態
        _page.setCursor(Qt.PointingHandCursor)
        # 設定新的頁數按鈕滑鼠數標成不能擊狀態
        page.setCursor(Qt.ArrowCursor)
        # 設定舊的頁數按鈕可以動作
        _page.setEnabled(True)
        # 設定新的頁數按鈕不能動作
        page.setEnabled(False)
        # 查看目前是否已經有點擊
        if self.nlist_data['first_click']:
            self.nlist_data['first_click'].set_state(False)
            self.nlist_data['first_click'] = None
        # 垂直滾動條歸0
        self.scroll_area.vertical_contents.set_value(0)
        # 橫向滾動條歸0
        self.scroll_area.horizontal_contents.set_value(0)
        # 查看目前頁數 是否等於 最大頁數
        if len(self.page_list) == self.nlist_data['page']:
            # 如果等於就把 下一頁按鈕隱藏
            self.on_ico.hide()
            # 設置全部頁數文字位置
            self.page_text.move(page.x() + 17, 3)
        # 查看目前頁數 是否不等於 最大頁數 and 是否下一頁按鈕沒有顯示
        elif self.page_max != self.nlist_data['page'] and not self.on_ico.isVisible():
            # 如果不等於 and 下一頁按鈕沒有顯示  則把 下一頁按鈕顯示
            self.on_ico.show()
            # 設置全部頁數文字位置
            self.page_text.move(self.on_ico.x() + 17, 3)
        # 設定 頁數容器 寬度
        self.all_page.resize(self.page_text.x() + self.page_text.width(), 17)

        # 查看目前頁數 是否是 第一頁 and 上一頁按鈕是否顯示
        if self.nlist_data['page'] == 1 and self.up_ico.isVisible():
            # 如果是第一頁 and 上一頁按鈕顯示 則把上一頁按鈕隱藏
            self.up_ico.hide()
        # 查看目前頁數 是否不是 第一頁 and 上一頁按鈕是否顯示
        elif self.nlist_data['page'] != 1 and not self.up_ico.isVisible():
            # 如果不是是第一頁 and 上一頁按鈕沒有顯示 則把上一頁按鈕顯示
            self.up_ico.show()
        size = self.text.get_text_size()
        self.nlist_data['scroll_contents'].resize(
            self.nlist_data['scroll_contents'].width(),
            size * self.nlist_data['text_height_max']
        )
        for text in self.text.text_list[0: size]:
            text.refresh()
            text.resize(self.nlist_data['scroll_contents'].width(), text.height())
        self.set_all(size)
        # 查看是否有頁數回調 and 是否能夠回調
        if self.nlist_data['page_callable'] and callable:
            # 調用回調函數
            self.nlist_data['page_callable'](value)

    # 設定 下一頁 上一頁 是否需要 顯示 隱藏 and 位置 and 設定總共頁數 and 頁數容器 大小 位置
    def checking_page(self) -> None:
        # 如果最大頁數 == 1 and 頁數容器顯示 則頁數容器隱藏
        if self.page_max == 1 and self.all_page.isVisible():
            # 頁數容器隱藏
            self.all_page.hide()
        # 如果最大頁數大於1 and 查看頁數容器是否不顯示
        elif self.page_max > 1 and not self.all_page.isVisible():
            # 頁數容器顯示
            self.all_page.show()
            # 查看下一頁按鈕是否不顯示
            if not self.on_ico.isVisible():
                # 如果不顯示則顯示
                self.on_ico.show()
        # 查看目前頁數 是否等於 最大頁數
        elif self.page_max == self.nlist_data['page']:
            # 如果等於就把 下一頁按鈕隱藏
            self.on_ico.hide()
            # 設置全部頁數文字位置
            self.page_text.move(self.page_list[self.page_max - 1].x() + 17, 3)
        # 查看目前頁數 是否不等於 最大頁數 and 是否下一頁按鈕沒有顯示
        elif self.page_max != self.nlist_data['page'] and not self.on_ico.isVisible():
            # 如果不等於 and 下一頁按鈕沒有顯示  則把 下一頁按鈕顯示
            self.on_ico.show()
            # 設置全部頁數文字位置
            self.page_text.move(self.on_ico.x() + 17, 3)
        # 設定下一頁按鈕位置
        self.on_ico.move((self.page_max * 16) + 16, 0)
        # 設置總共頁數文字
        self.page_text.setText(f'共{self.page_max}頁')
        # 自動調整文字大小
        self.page_text.adjustSize()
        # 設置總共頁數文字 位置
        self.page_text.move(self.on_ico.x() + 17, 3)
        # 設置頁數容器大小
        self.all_page.resize(self.page_text.x() + self.page_text.width(), 17)
        # 設置頁數容器位置
        self.all_page.move(
            int((self.width() - self.all_text.width() - 20 - self.all_page.width()) / 2),
            int((self.height() - self.all_page.height()) / 2)
        )

    # 設置所有總共多少項
    def set_all(self, value: int) -> None:
        # 設置文字
        self.all_text.setText(f'{value}項')
        # 文字自動調整大小
        self.all_text.adjustSize()
        # 文字調整位置
        self.all_text.move(
            self.width() - self.all_text.width() - 20,
            int(int(self.height() - self.all_text.height()) / 2)
        )

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        # 文字調整位置
        self.all_text.move(
            self.width() - self.all_text.width() - 20,
            int((self.height() - self.all_text.height()) / 2)
        )
        self.all_page.move(
            int((self.width() - self.all_text.width() - 20 - self.all_page.width()) / 2),
            int((self.height() - self.all_page.height()) / 2)
        )


class NList(QFrame):
    def __init__(self, parent: QWidget | None = None, quantity_limit: int = 1000) -> None:
        super().__init__(parent)
        # 設置 底部統計 窗口 最大大小
        self.quantity_max: int = 34
        # 設置內容窗口UI
        self.scroll_contents = QWidget()
        self.scroll_contents.resize(0, 0)
        self.nlist_data: NlistData = NlistData(
            # 目前頁數
            page=1,
            # 一頁顯示多少text
            quantity_limit=quantity_limit,
            # text高度上限
            text_height_max=39,
            # 最後一個點擊的text
            first_click=None,
            # 內容窗口
            scroll_contents=self.scroll_contents,
            # text右鍵菜單
            context_menu=Menu(),
            # text右鍵菜單內容
            menu={},
            # text右鍵回調
            menu_callable=None,
            # 頁數點擊回調
            page_callable=None
        )

        self.all_widget = AllWidget(self)

        self.visual_contents = VisualContents()

        self.text: QText = QText(self.nlist_data)
        # 設置滾動區
        self.scroll_area: MyScrollArea = MyScrollArea(
            self.all_widget, self.visual_contents, self.scroll_contents
        )
        self.scroll_area.lower()

        self.quantity = Quantity(self.all_widget, self.nlist_data, self.scroll_area, self.text)

    # 新增 新窗口
    def new(self, name: str) -> None:
        # 清空目前點擊
        if self.nlist_data['first_click']:
            self.nlist_data['first_click'].set_state(False)
            self.nlist_data['first_click'] = None
            # self.quantity.set_all(0)
        # 設置新儲存頁數資料
        self.text.new_text_contents(name)
        # 初始化目前頁數
        self.quantity.set_page(1, False)
        # 設置最大頁數為1
        self.quantity.set_all_page(1)
        self.nlist_data['scroll_contents'].resize(
            self.nlist_data['scroll_contents'].width(),
            0
        )

    # 切換窗口
    def switch(self, name: str) -> None:
        # 清空目前點擊
        if self.nlist_data['first_click']:
            self.nlist_data['first_click'].set_state(False)
            self.nlist_data['first_click'] = None
        # 切換窗口
        self.text.switch_text_contents(name)
        # 設置新介面最大頁數
        self.quantity.set_all_page(self.text.text_save_list.page_size())
        # 設置成第一頁 並設置內容窗口大小
        self.quantity.set_page(1, False)
        self.refresh_text()

    def add_text(self, text: list[NTextData, ...]):
        self.text.add_text(text)
        self.refresh_text()

    def refresh_text(self):
        size = self.text.get_text_size()
        self.nlist_data['scroll_contents'].resize(
            self.nlist_data['scroll_contents'].width(),
            size * self.nlist_data['text_height_max']
        )
        for text in self.text.text_list[0: size]:
            text.refresh()
            text.resize(self.scroll_contents.width(), text.height())
        self.quantity.set_all(size)

    # 設置最大頁數
    def set_all_page(self, page: int) -> None:
        self.quantity.set_all_page(page)
        self.text.text_save_list.set_max_page(page)

    # 設置text右鍵回調
    def set_text_menu_callable(self, callable: Callable[[], bool]) -> None:
        self.qlist_data['menu_callable'] = callable

    # 設置背景右鍵回調
    def set_text_backdrop_callable(self, callable: Callable[[], bool]) -> None:
        self.all_widget.menu_callable = callable

    # 設置 頁數回調
    def set_page_callable(self, callable: Callable[[int], None]) -> None:
        self.nlist_data['page_callable'] = callable

    # 初始化當前介面
    def cls(self) -> None:
        self.text.text_save_list.cls()
        # 設置成第一頁
        self.quantity.set_page(1, False)
        # 設置頁數上限
        self.quantity.set_all_page(1)

    def all_cls(self) -> None:
        text_save = self.text.text_save_list.save[None]
        text_save.initialization()
        self.text.text_save_list.save.clear()
        self.text.text_save_list.save[None] = text_save
        self.text.text_save_list.text_save = text_save
        # 設置成第一頁
        self.quantity.set_page(1, False)
        # 設置頁數上限
        self.quantity.set_all_page(1)

        # for text in

    # 連結 text 右鍵 菜單
    def text_menu_click_connect(self, text: str, slot: Callable[[], None], mode: bool = True) -> None:
        action = QAction(QIcon('r:\\10.png'), text)
        action.triggered.connect(slot)
        item: QListWidgetItem = self.nlist_data['context_menu'].addAction(action)
        self.nlist_data['menu'][text] = item
        self.nlist_data['context_menu'].set_item_hidden(item, not mode)

    # 連結 背景 右鍵 菜單
    def backdrop_menu_click_connect(self, text: str, slot: Callable[[], None], mode: bool = True) -> None:
        action = QAction(QIcon('r:\\10.png'), text)
        action.triggered.connect(slot)
        item: QListWidgetItem = self.all_widget.context_menu.addAction(action)
        self.all_widget.menu[text] = item
        self.all_widget.context_menu.set_item_hidden(item, not mode)

    # 返回指定data or 已點擊texts data
    def extra(self, index: int | None = None) -> any:
        if index is not None:
            return self.text.text_list[index].text_data['data']
        else:
            return self.nlist_data['first_click'].text_data['data']

    # 設置 加載GIF 顯示 or 隱藏
    def set_load_visible(self, visible: bool) -> None:
        self.visual_contents.set_load_visible(visible)

    # 設置 text右鍵 是否可顯示
    def set_menu_visible(self, text: str, mode: bool) -> None:
        self.nlist_data['context_menu'].set_item_hidden(self.qlist_data['menu'][text], not mode)

    # 設置 背景右鍵 是否可顯示
    def set_backdrop_menu_visible(self, text: str, mode: bool) -> None:
        self.all_widget.context_menu.set_item_hidden(self.all_widget.menu[text], not mode)

    def set_text_slots(self, text_slots: list[NTextSlots]) -> None:
        self.text.set_text_slots(text_slots)

    # 獲取目前text資料
    def get_text_data(self) -> dict[int, list[NTextData, ...]]:
        return self.text.text_save_list.text_save.text

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.all_widget.resize(
            self.width(),
            self.height() - self.all_widget.y()
        )
        self.scroll_area.resize(self.width(), self.all_widget.height() - self.quantity_max)
        for text in self.text.text_list[0: self.text.get_text_size()]:
            text.resize(self.width() - 2, text.height())
        self.quantity.setGeometry(
            0, self.all_widget.height() - self.quantity_max,
            self.all_widget.width(), self.quantity_max
        )


if __name__ == '__main__':
    from qasync import QEventLoop
    from sys import argv
    from asyncio import set_event_loop
    app = QApplication(argv)
    loop = QEventLoop(app)
    set_event_loop(loop)
    ex = NList()
    ex.show()
    with loop:
        loop.run_forever()