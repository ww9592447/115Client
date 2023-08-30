import math
from typing import Callable, Awaitable

from PyQt5.Qt import QFrame, pyqtSignal, QWidget, Qt, QPainter, QPen, QLabel, QFont, QPoint, QColor,\
    QPaintEvent, QIcon, QListWidgetItem, QContextMenuEvent, QAction, QMouseEvent, QWheelEvent, QResizeEvent,\
    QFontMetrics

from .MScroolBar import ScrollArea
from .QText import QText, Title, TextDataList

from Modules.type import QlistData, NClickCallable, TextData, TextSlots, MyDict
from Modules.image import AllImage, Image, GifImage
from Modules.widgets import MyIco
from Modules.menu import Menu


# 可拖曳窗口 等待gui
class Select(QWidget):
    def __init__(self, parent: QWidget, rect: list[int, int, int, int]):
        super().__init__(parent)
        self.rect = rect
        self.load = AllImage.get_gif(self, GifImage.MIN_LOAD, geometry=(0, 0, 20, 20))
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def set_load_visible(self, visible: bool) -> None:
        if visible:
            self.load.raise_()
        self.load.setVisible(visible)

    # 繪畫事件
    def paintEvent(self, event: QPaintEvent) -> None:
        # 初始化繪圖工具
        qp = QPainter()
        # 開始在窗口繪製
        qp.begin(self)
        # 自定義畫筆方法
        if self.rect != [0, 0, 0, 0]:
            self.draw_rect(qp)
        # 結束在窗口的繪製
        qp.end()

    def draw_rect(self, qp: QPainter) -> None:
        # 獲得 畫筆 顏色 大小
        pen = QPen(QColor(6, 168, 255, 255), 1)
        # 設定 畫筆 顏色 大小
        qp.setPen(pen)
        # 畫出矩形
        qp.drawRect(*self.rect)
        # 為矩形內容上色
        qp.fillRect(*self.rect, QColor(6, 168, 255, 128))

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
    menu_callable: Callable[[], bool] | None = None

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        # 設置背景右鍵菜單
        self.context_menu: Menu = Menu()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self.menu:
            if self.menu_callable:
                if self.menu_callable():
                    self.context_menu.exec(event.globalPos())
            else:
                self.context_menu.exec(event.globalPos())


# 可視窗口容器
class VisualContents(QWidget):
    def __init__(self, select: Select) -> None:
        super().__init__(None)
        self.select = select

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.select.resize(self.size())


class QScrollArea(ScrollArea):
    def __init__(
            self,
            parent: QWidget,
            visual_contents: VisualContents,
            scroll_contents: QWidget,
            qlist_data: QlistData,
            text: QText
    ) -> None:
        super().__init__(parent, visual_contents, scroll_contents)
        self.text = text
        self.qlist_data = qlist_data

    # 滾動條移動回調
    def scroll_contents_by(self, dx: int, dy: int) -> None:
        # 當橫滾動條移動後 標題需要跟著移動
        self.text.title.move(self.text.title.x() + dx, 0)
        _max = math.ceil(
            (abs(self.scroll_contents.y()) + self.visual_contents.height()) / self.qlist_data['text_height_max']
                         )
        if self.text.text_save_list.get_read() < _max <= self.text.text_save_list.get_text_size():
            for text in self.text.text_list[self.text.text_save_list.get_read(): _max]:
                text.refresh()
            self.text.text_save_list.set_read(_max)


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


class Quantity(QFrame):
    def __init__(
            self,
            parent: QWidget,
            qlist_data: QlistData,
            scroll_area: QScrollArea,
            text: QText,
            cls_click: NClickCallable
    ) -> None:
        super().__init__(parent)
        # 設置所有qlist資料
        self.qlist_data: QlistData = qlist_data
        # 設置標題 and text
        self.text: QText = text
        # 設定最大頁數
        self.page_max: int = 1
        # 設置滾動區
        self.scroll_area: QScrollArea = scroll_area
        # 設置清空點擊回調
        self.cls_click: NClickCallable = cls_click
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
            click=lambda: self.set_page(self.qlist_data['page'] - 1, True)
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
            click=lambda: self.set_page(self.qlist_data['page'] + 1, True)
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

    # 設置成第幾頁 and 是否刷新text資料
    def set_page(self, value: int, callable: bool = True, refresh: bool = True) -> None:
        # 獲取頁數
        page: Page = self.page_list[value - 1]
        # 獲取舊的頁數按鈕
        _page: Page = self.page_list[self.qlist_data['page'] - 1]
        # 設定新頁數
        self.qlist_data['page'] = value
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
        # 清空所有點擊
        self.cls_click()
        # 垂直滾動條歸0
        self.scroll_area.vertical_contents.set_value(0)
        # 橫向滾動條歸0
        self.scroll_area.horizontal_contents.set_value(0)
        # 查看目前頁數 是否等於 最大頁數
        if len(self.page_list) == self.qlist_data['page']:
            # 如果等於就把 下一頁按鈕隱藏
            self.on_ico.hide()
            # 設置全部頁數文字位置
            self.page_text.move(page.x() + 17, 3)
        # 查看目前頁數 是否不等於 最大頁數 and 是否下一頁按鈕沒有顯示
        elif self.page_max != self.qlist_data['page'] and not self.on_ico.isVisible():
            # 如果不等於 and 下一頁按鈕沒有顯示  則把 下一頁按鈕顯示
            self.on_ico.show()
            # 設置全部頁數文字位置
            self.page_text.move(self.on_ico.x() + 17, 3)
        # 設定 頁數容器 寬度
        self.all_page.resize(self.page_text.x() + self.page_text.width(), 17)

        # 查看目前頁數 是否是 第一頁 and 上一頁按鈕是否顯示
        if self.qlist_data['page'] == 1 and self.up_ico.isVisible():
            # 如果是第一頁 and 上一頁按鈕顯示 則把上一頁按鈕隱藏
            self.up_ico.hide()
        # 查看目前頁數 是否不是 第一頁 and 上一頁按鈕是否顯示
        elif self.qlist_data['page'] != 1 and not self.up_ico.isVisible():
            # 如果不是是第一頁 and 上一頁按鈕沒有顯示 則把上一頁按鈕顯示
            self.up_ico.show()

        size = self.text.text_save_list.get_text_size()
        self.qlist_data['scroll_contents'].resize(
            self.qlist_data['scroll_contents'].width(),
            size * self.qlist_data['text_height_max']
        )
        if refresh:
            for text in self.text.text_list[self.text.text_save_list.get_read(): size]:
                text.refresh()
        else:
            size = math.ceil(
                (abs(self.scroll_area.scroll_contents.y()) + self.scroll_area.visual_contents.height())
                / self.qlist_data['text_height_max']
            )
            size = min(self.text.text_save_list.get_text_size(), size)
        for text in self.text.text_list[0: size]:
            text.refresh()
        self.text.text_save_list.set_read(size)
        # 查看是否有頁數回調 and 是否能夠回調
        if self.qlist_data['page_callable'] and callable:
            # 調用回調函數
            self.qlist_data['page_callable'](value)

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
        elif self.page_max == self.qlist_data['page']:
            # 如果等於就把 下一頁按鈕隱藏
            self.on_ico.hide()
            # 設置全部頁數文字位置
            self.page_text.move(self.page_list[self.page_max - 1].x() + 17, 3)
        # 查看目前頁數 是否不等於 最大頁數 and 是否下一頁按鈕沒有顯示
        elif self.page_max != self.qlist_data['page'] and not self.on_ico.isVisible():
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

    # 設置已選中多少項
    def set_value(self, value: int) -> None:
        if value == 0:
            self.set_all(self.text.text_save_list.get_text_size())
            return
        # 設置文字
        self.all_text.setText(f'已選中{value}項')
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


class QList(QFrame):
    # 所有qlist資料
    qlist_data: QlistData
    # 字體大小
    font_size: int
    # 統計UI
    quantity: Quantity
    # 所有容器
    all_widget: AllWidget
    # 內容窗口UI
    scroll_contents: QWidget
    # 滾動區
    scroll_area: QScrollArea
    # 標題 and text
    text: QText
    # 可拖曳窗口 等待gui
    select: Select
    # 初始化矩形座標
    rect: list[int, int, int, int] = [0, 0, 0, 0]
    # 保存第一次點擊Y座標
    click_y: int = 0
    # 保存內容窗口移動Y座標
    by: int = 0
    # 內容窗口初始座標
    title_size: QPoint

    def __init__(
            self,
            parent: QWidget | None = None,
            quantity_limit: int = 1000,
            text_height_max: int = 39,
            font_size: int = 11,
            spacer_symbol: str = '...',
            spacer_space: int = 5
    ) -> None:
        super().__init__(parent)
        # 設置內容窗口UI
        self.scroll_contents: QWidget = QWidget()
        # 初始化內容窗口大小
        self.scroll_contents.resize(0, 0)
        # 設置 底部統計 窗口 最大大小
        self.quantity_max: int = 34
        # 設置字體大小
        self.font_size = font_size
        # 獲取字體設置
        (_font := QFont()).setPointSize(font_size)

        font: QFontMetrics = QFontMetrics(_font)

        self.qlist_data: QlistData = QlistData(
            # 目前頁數
            page=1,
            # 一頁顯示多少text
            quantity_limit=quantity_limit,
            # text高度上限
            text_height_max=text_height_max,
            # 標題高度上限
            title_max=31,
            # 標題文字間隔邊緣多遠
            title_interval=3,
            # 標題移動條可觸碰大小
            title_moving_bar_size=7,
            # 最後一個點擊的text
            first_click=None,
            # my_text字體
            font=_font,
            # 字體高度
            my_text_y=int((text_height_max - font.height()) / 2),
            # 間隔符號
            spacer_symbol=spacer_symbol,
            # 間隔符號大小
            spacer_symbol_size=font.horizontalAdvance(spacer_symbol),
            # 空白數量
            spacer_space=spacer_space,
            # 空白數量大小
            spacer_space_size=font.horizontalAdvance(' ') * spacer_space,
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
        # 所有容器
        self.all_widget: AllWidget = AllWidget(self)
        # 初始化矩形座標
        self.rect: list[int, int, int, int] = [0, 0, 0, 0]
        # 標題 and text
        self.text: QText = QText(self.all_widget, self.qlist_data)
        # 設置內容窗口初始座標
        self.title_size: QPoint = QPoint(1, self.qlist_data['title_max'] + 1)
        # 設置可拖曳窗口 等待gui
        self.select: Select = Select(self.all_widget, self.rect)
        # 移動位置跟內容窗口等同位置
        self.select.move(self.title_size)
        # 可視窗口容器
        self.visual_contents = VisualContents(self.select)
        # 設置滾動區
        self.scroll_area: QScrollArea = QScrollArea(
            self.all_widget, self.visual_contents,
            self.scroll_contents, self.qlist_data, self.text
        )
        # 設置滾動區置底
        self.scroll_area.lower()
        # 設置滾動區位置
        self.scroll_area.move(0, self.qlist_data['title_max'])

        self.quantity = Quantity(self.all_widget, self.qlist_data, self.scroll_area, self.text, self.cls_click)

        self.text.change_quantity.connect(self.quantity.set_value)

    # 新增 新窗口
    def new(self, name: str) -> None:
        # 清空目前點擊
        self.cls_click()
        # 設置新儲存頁數資料 並且切換
        self.text.new_text_contents(name)
        # 初始化目前頁數
        self.quantity.set_page(1, False, False)
        # 設置最大頁數為1
        self.quantity.set_all_page(1)
        self.qlist_data['scroll_contents'].resize(
            self.qlist_data['scroll_contents'].width(),
            0
        )

    # 切換窗口
    def switch(self, name: str, refresh=False) -> None:
        # 清空目前點擊
        self.cls_click()
        # 切換窗口 and 刷新text資料
        self.text.switch_text_contents(name)
        # 設置新介面最大頁數
        self.quantity.set_all_page(self.text.text_save_list.page_size())
        # 設置成第一頁
        self.quantity.set_page(1, False, refresh)
        # 設置新窗口已讀取變0
        self.text.text_save_list.set_read(0)
        self.refresh_text(refresh)

    def add_text(self, text: list[TextData, ...], refresh: bool = False):
        # refresh 是否需要全部一起刷新
        self.text.add_text(text)
        self.quantity.set_all(len(text))
        self.refresh_text(refresh)

    def refresh_text(self, refresh: bool):
        size = self.text.text_save_list.get_text_size()
        self.qlist_data['scroll_contents'].resize(
            self.qlist_data['scroll_contents'].width(),
            size * self.qlist_data['text_height_max']
        )
        if refresh:
            for text in self.text.text_list[0: size]:
                text.refresh()
            self.text.text_save_list.set_read(size)
        else:
            _max = math.ceil(
                (abs(self.scroll_contents.y()) + self.visual_contents.height()) / self.qlist_data['text_height_max']
            )
            if self.text.text_save_list.get_read() < _max <= size:
                for text in self.text.text_list[self.text.text_save_list.get_read(): _max]:
                    text.refresh()
                self.text.text_save_list.set_read(_max)

    # 獲取所有標題
    def get_all_title(self) -> MyDict[Title]:
        return self.text.text_save_list.title_all

    # 獲取目前標題
    def get_title(self) -> MyDict[Title]:
        return self.text.text_save_list.title

    # 獲取目前text資料
    def get_text_data(self) -> dict[int, TextDataList]:
        return self.text.text_save_list.text_save.text

    # 獲取已點擊text數量
    def get_current_click(self) -> int:
        return len(self.text.current_click)

    # 設置最大頁數
    def set_all_page(self, page: int) -> None:
        self.quantity.set_all_page(page)
        self.text.text_save_list.set_max_page(page)

    # 設置text右鍵回調
    def set_text_menu_callable(self, slots: Callable[[], bool]) -> None:
        self.qlist_data['menu_callable'] = slots

    # 設置背景右鍵回調
    def set_text_backdrop_callable(self, slots: Callable[[], bool]) -> None:
        self.all_widget.menu_callable = slots

    # 設置 頁數回調
    def set_page_callable(self, callable: Callable[[int], None]) -> None:
        self.qlist_data['page_callable'] = callable

    # 設置text右鍵
    def set_text_slots(self, text_slots: list[TextSlots]) -> None:
        self.text.set_text_slots(text_slots)

    # 清空 text資料 and 設定成第一頁 and 設定內容窗口大小 and 刷新text資料
    def cls(self, cid: str | None = None) -> None:
        if cid:
            self.text.text_save_list.save[cid].cls()
        else:
            self.text.text_save_list.cls()

        if cid is None or self.text.text_name == cid:
            # 設置成第一頁
            self.quantity.set_page(1, False, False)
            # 設置頁數上限
            self.quantity.set_all_page(1)

    # 設置標題
    def title_add(self, text: str, width: int = 50, least: int = 50) -> None:
        self.text.title_add(text, width, least)

    # 連結 text 右鍵 菜單
    def text_menu_click_connect(
            self,
            text: str,
            slot: Callable[[], Awaitable[None] | any],
            ico: QIcon | None = None,
            mode: bool = True
    ) -> None:
        if ico:
            action = QAction(ico, text)
        else:
            action = QAction(text)
        action.triggered.connect(slot)
        item: QListWidgetItem = self.qlist_data['context_menu'].addAction(action)
        self.qlist_data['menu'][text] = item
        self.qlist_data['context_menu'].set_item_hidden(item, not mode)

    # 連結 背景 右鍵 菜單
    def backdrop_menu_click_connect(
            self,
            text: str,
            slot: Callable[[], Awaitable[None] | None],
            ico: QIcon | None = None,
            mode: bool = True
    ) -> None:
        if ico:
            action = QAction(ico, text)
        else:
            action = QAction(text)
        action.triggered.connect(slot)
        item: QListWidgetItem = self.all_widget.context_menu.addAction(action)
        self.all_widget.menu[text] = item
        self.all_widget.context_menu.set_item_hidden(item, not mode)

    # 清空所有點擊
    def cls_click(self) -> None:
        for text in self.text.current_click.copy():
            self.text.set_text_state(text)
        self.text.emit_change_quantity()

    # 返回指定data or 已點擊texts data
    def extra(self, index: int | None = None) -> any:
        if index is not None:
            return self.text.text_list[index].text_data['data']
        if len(self.text.current_click) == 0:
            return None
        data: list = []
        for text in self.text.current_click:
            data.append(text.text_data['data'])
        if len(data) == 1:
            return data[0]
        else:
            return data

    # 設置標題是否顯示
    def set_title_visible(self, name: str, visible: bool) -> None:
        if name in self.text.text_save_list.title_all:
            self.text.set_title_visible(self.text.text_save_list.title_all[name], visible)

    # 設置 加載GIF 顯示 or 隱藏
    def set_load_visible(self, visible: bool) -> None:
        self.select.set_load_visible(visible)

    # 設置 text右鍵 是否可顯示
    def set_menu_visible(self, text: str, mode: bool) -> None:
        self.qlist_data['context_menu'].set_item_hidden(self.qlist_data['menu'][text], not mode)

    # 設置 背景右鍵 是否可顯示
    def set_backdrop_menu_visible(self, text: str, mode: bool) -> None:
        self.all_widget.context_menu.set_item_hidden(self.all_widget.menu[text], not mode)

    def _set_update(self, pos: QPoint) -> None:
        # 刷新矩形
        self.select.update()
        # 獲取第一次點擊內容窗口y座標, 目前內容窗口y相對座標
        y = [self.click_y, pos.y() - self.scroll_contents.y()]
        # 排序相對座標
        y.sort()
        # 查看最小相對y座標是否大於 內容窗口大小  小於0
        if self.scroll_contents.height() >= y[0] >= 0:
            # 獲取 最低相對座標 在哪個texys上面
            _min = int(y[0] / self.qlist_data['text_height_max'])
            # 獲取 最高相對座標 在哪個text上面
            if (_max := self.text.text_save_list.get_text_size()) > int(y[1] / self.qlist_data['text_height_max']):
                _max = int(y[1] / self.qlist_data['text_height_max']) + 1
            # 獲取最低到最高的迭代器
            select = self.text.text_list[_min: _max]
            # 開始循環迭代器
            for text in select:
                # 查看index 是否在 以點擊裡面
                if text not in self.text.current_click:
                    # 不在就 index 變成已點擊
                    # self.text.set_text_state(text)
                    self.text.vbox_right_select(text)
            # 查看迭代器 是否空白
            if select:
                # 設定最後一次點擊
                self.qlist_data['first_click'] = select[-1]
            # 查看所有已點擊的 是否有多餘的
            for text in set(self.text.current_click) ^ set(select):
                # 多餘的點擊取消
                # self.text.set_text_state(text)
                self.text.vbox_right_select(text)

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 清空所有已點擊
        self.cls_click()
        # 獲取窗口相對座標
        pos: QPoint = event.pos() - self.title_size - self.all_widget.pos()
        # 查看相對座標 是否 不是負數 and 左鍵點擊
        if pos.x() > 0 < pos.y() and event.buttons() == Qt.LeftButton:
            # 設定第一次點擊 內容窗口y相對座標
            self.click_y: int = pos.y() - self.scroll_contents.y()
            # 設定內容窗口移動Y座標
            self.by: int = self.scroll_contents.y()
            # 設定矩形座標
            self.rect[0] = pos.x()
            # 設定矩形座標
            self.rect[1] = pos.y()

    # 滑鼠放開事件
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        # 清空矩形座標
        self.rect.clear()
        # 初始化矩形座標
        self.rect.extend([0, 0, 0, 0])
        # 刷新矩形
        self.select.update()

    # 滑鼠點擊移動
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.rect[0:2] != [0, 0]:
            # 獲取窗口相對座標
            pos: QPoint = event.pos() - self.title_size - self.all_widget.pos()
            # 設定矩形要多大
            self.rect[2] = pos.x() - self.rect[0]
            self.rect[3] = pos.y() - self.rect[1]
            # 設定刷新矩形相關資料
            self._set_update(pos)

    # 滾輪事件
    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.rect != [0, 0, 0, 0]:
            # 獲取內容窗口移動多少
            y: int = abs(self.by - self.scroll_contents.y())
            # 設置新內容窗口y座標
            self.by = self.scroll_contents.y()
            # 查看往滾輪移動方向
            if event.angleDelta().y() > 0:
                # 調整 矩形y座標
                self.rect[1] = self.rect[1] + y
                self.rect[3] = self.rect[3] - y
            else:
                # 調整 矩形y座標
                self.rect[1] = self.rect[1] - y
                self.rect[3] = self.rect[3] + y
            # 獲取窗口相對座標
            pos: QPoint = self.mapFromGlobal(event.globalPos()) - self.title_size - self.all_widget.pos()
            # 設定刷新矩形相關資料
            self._set_update(pos)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.all_widget.resize(
            self.width(),
            self.height() - self.all_widget.y()
        )
        bottom = self.text.title.x() + self.text.title.width()
        self.text.title.resize(1 + self.text.title.width() + (self.width() - bottom), self.qlist_data['title_max'])
        self.scroll_area.resize(self.width(), self.all_widget.height() - self.qlist_data['title_max'] - self.quantity_max)
        self.quantity.setGeometry(
            0, self.all_widget.height() - self.quantity_max,
            self.all_widget.width(), self.quantity_max
        )
