from typing import Callable, Awaitable

from PyQt5.Qt import QPushButton, QFrame, QButtonGroup, QWidget, Qt, QLabel, pyqtSignal, QMouseEvent, QEvent, QFont, \
    QResizeEvent

from .QList import QList
from .NList import NList

from Modules.image import AllImage, GifLabel, Image, GifImage
from Modules.widgets import MyIco, Frame, LineEdit


class SearchButton(QPushButton):
    # 回調
    callable: Callable[[], None] | None

    def __init__(self, parent) -> None:
        super(SearchButton, self).__init__(parent)
        # 設置成可切換按鈕
        self.setCheckable(True)
        # 設置成自動排他按鈕
        self.setAutoExclusive(True)
        # 回調
        self.callable: Callable[[], None] | None = None
        self.setStyleSheet(
            'SearchButton{background-color: rgb(242, 242, 242);border-radius: 5px}'
            'SearchButton:hover{background-color: rgb(229, 229, 229);}'
            'SearchButton:checked{background-color: rgb(204, 204, 204);}'
        )
        self.toggled.connect(self.set_cursor)

    # 設置滑鼠狀態
    def set_cursor(self, visible: bool) -> None:
        if visible:
            self.setCursor(Qt.ArrowCursor)
            if self.isVisible():
                if self.callable:
                    self.callable()
        else:
            self.setCursor(Qt.PointingHandCursor)


# 搜索容器
class SearchContainer(QFrame):
    # 搜索所有按鈕
    search_all: SearchButton
    # 搜索路徑按鈕
    search_name: SearchButton
    # 搜索按鈕組
    btn_group: QButtonGroup

    def __init__(self, parent: QWidget) -> None:
        super(SearchContainer, self).__init__(parent)
        # 設置搜索所有按鈕
        self.search_all: SearchButton = SearchButton(self)
        # 設置滑鼠上方圖案
        self.search_all.setCursor(Qt.ArrowCursor)
        # 設置搜索所有按鈕文字
        self.search_all.setText('全部')
        # 設置搜索所有按鈕大小
        self.search_all.resize(48, 25)
        # 設置搜索路徑按鈕點擊
        self.search_all.setChecked(True)
        # 設置搜索路徑按鈕
        self.search_name: SearchButton = SearchButton(self)
        # 設置滑鼠上方圖案
        self.search_name.setCursor(Qt.PointingHandCursor)
        # 設置搜索路徑按鈕位置
        self.search_name.move(55, 0)
        # 搜索路徑按鈕隱藏
        self.search_name.hide()
        # 設置搜索按鈕組
        self.btn_group: QButtonGroup = QButtonGroup(self)
        self.btn_group.addButton(self.search_all)
        self.btn_group.addButton(self.search_name)
        # 設置搜索按鈕容器大小
        self.resize(48, 25)
        # 隱藏搜索容器
        self.hide()


class TextQLabel(QWidget):
    # 文字
    text: QLabel
    # 鼠標移出圖案
    leave_ico: QLabel
    # 鼠標移入圖案
    enter_ico: QLabel

    def __init__(self, text: str, parent: QWidget):
        super(TextQLabel, self).__init__(parent)
        # 設置文字
        self.text.setText(text)
        # 獲取文字寬度
        width = self.text.fontMetrics().horizontalAdvance(text)
        # 設置文字位置大小
        self.text.setGeometry(0, 7, width, 25)
        self.leave_ico = QLabel(self)


# 路徑目錄
class Directory(QFrame):
    left_click: pyqtSignal = pyqtSignal(QWidget)
    # 額外資料
    data: any
    # 目錄
    text: QLabel
    # 右箭頭圖案容器
    ico: QLabel

    def __init__(self, text: str, parent: QWidget, data: any = None) -> None:
        super(Directory, self).__init__(parent)
        # 設置額外資料
        self.data: any = data
        # 設定目錄
        self.text: QLabel = QLabel(self)
        # 獲取字體
        font = QFont()
        # 設置字體大小
        font.setPointSize(11)
        # 替換字體
        self.text.setFont(font)
        # 設置目錄文字
        self.text.setText(text)
        # 獲取文字寬度
        width = self.text.fontMetrics().horizontalAdvance(text)
        # 設置目錄位置大小
        self.text.setGeometry(0, 7, width, 25)
        # 設置 右箭頭圖案容器
        self.ico = QLabel(self)
        # 設置 向右黑色 大小
        self.ico.setGeometry(width + 9, 17, 6, 8)
        # 設置 向右黑色 箭頭 圖片
        self.ico.setPixmap(AllImage.get_image(Image.BLACK_RIGHT_ARROW))
        # 設置 目錄大小
        self.resize(width + 25, 35)

    def set_data(self, text: str, data: any) -> None:
        self.text.setText(text)
        self.data: any = data
        # 獲取文字寬度
        width = self.text.fontMetrics().horizontalAdvance(text)
        # 設置目錄位置大小
        self.text.setGeometry(0, 7, width, 25)
        # 設置 向右黑色 大小
        self.ico.setGeometry(width + 9, 17, 6, 8)
        # 設置 目錄大小
        self.resize(width + 25, 35)

    def text(self) -> None:
        return self.text.text()

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            self.left_click.emit(self)

    # 鼠標移出事件
    def leaveEvent(self, event: QEvent) -> None:
        if self.isEnabled():
            self.setStyleSheet("QLabel{color:rgb(0,0,0);}")
            self.ico.setPixmap(AllImage.get_image(Image.BLACK_RIGHT_ARROW))

    # 鼠標移入事件
    def enterEvent(self, event: QEvent) -> None:
        if self.isEnabled():
            self.setStyleSheet("QLabel{color:rgb(6,168,255);}")
            self.ico.setPixmap(AllImage.get_image(Image.BLUE_RIGHT_ARROW))


class QListDirectory(QList):
    def __init__(
            self,
            parent: QWidget = None,
            quantity_limit: int = 1000,
            text_height_max: int = 39,
            font_size: int = 11,
            spacer_symbol: str = '...',
            spacer_space: int = 5
    ) -> None:
        super(QListDirectory, self).__init__(
            parent, quantity_limit, text_height_max, font_size, spacer_symbol, spacer_space
        )
        # 設置所有目錄
        self.all_directory: list[Directory, ...] = []
        # 設置未使用目錄
        self.unused_directory: list[Directory, ...] = []
        # 設置背景白色
        self.setStyleSheet('QListDirectory{background-color: rgb(255, 255, 255)}')
        # 設置目錄容器
        self.directory_container: QWidget = QWidget(self)
        # 設定目錄容器名稱
        self.directory_container.setObjectName('directory')
        # 根據名稱設定 上下 邊框
        self.directory_container.setStyleSheet(
            '#directory{border-style:solid; border-bottom-width:1px;'
            'border-top-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )
        # 設置搜索框容器
        self.search_container: QWidget = QWidget(self.directory_container)
        # 設置搜索框容器大小
        self.search_container.resize(230, 39)
        # 設置 搜索按鈕容器
        self.search_button_container: SearchContainer = SearchContainer(self)
        # 設置 左側直線
        self.left_line: Frame = Frame(self.directory_container)
        # 設置 左側直線 大小位置
        self.left_line.setGeometry(100, 13, 1, 16)
        # 設置 右側直線
        self.right_line: Frame = Frame(self.search_container)
        # 設置 右側直線 大小位置
        self.right_line.setGeometry(0, 12, 1, 16)
        # 設定 搜索窗口
        self.lineedit = LineEdit(self.search_container, '搜索', '', (12, 0, 218, 39), qss=1)
        # 設定 上一頁 按鈕
        self.pgup_button: MyIco = MyIco(
            self.directory_container,
            Image.MAX_BLACK_PREVIOUS_PAGE,
            Image.MAX_BLUE_PREVIOUS_PAGE,
            (18, 14, 8, 12),
            false=Image.MAX_GREY_PREVIOUS_PAGE
        )

        # 設定 下一頁 按鈕
        self.pgon_button: MyIco = MyIco(
            self.directory_container,
            Image.MAX_BLACK_NEXT_PAGE,
            Image.MAX_BLUE_NEXT_PAGE,
            (49, 14, 8, 12),
            false=Image.MAX_GREY_NEXT_PAGE
        )
        # 設定 刷新 按鈕
        self.refresh_button: MyIco = MyIco(
            self.directory_container,
            Image.BLACK_REFRESH,
            Image.BLUE_REFRESH,
            (75, 14, 13, 12),
            state=True
        )
        # 設置 重新整理 gif動畫
        self.refresh_gif: GifLabel = AllImage.get_gif(self, GifImage.REFRESH, (74, 13, 14, 14))
        # 初始化目錄回調
        self.directory_callable = None
        # 移動所有容器位置
        self.all_widget.move(0, 41)

    # 添加 新的 目錄
    def directory_add(self, text: str, data: any = None) -> None:
        if self.unused_directory:
            directory = self.unused_directory.pop()
            directory.set_data(text, data)
        else:
            # 獲取目錄
            directory = Directory(text, self.directory_container, data)
            # 連接目錄點擊回調
            directory.left_click.connect(self._directory_delete)
        # 目錄置底 為了防止穿透搜索欄被看到
        directory.lower()
        # 目錄顯示
        directory.show()
        # 查看是否是第一個
        if self.all_directory:
            # 獲取最後一個底部位置
            x = self.all_directory[-1].x() + self.all_directory[-1].width()
            # 移動目錄位置
            directory.move(x, 0)
        else:
            # 移動目錄位置
            directory.move(110, 0)
        # 添加至所有目錄
        self.all_directory.append(directory)

    # 刪除目錄
    def _directory_delete(self, directory: Directory) -> None:
        # 查看 需要刪除的目錄 是否是最後一個
        if self.all_directory[-1] == directory:
            # 如果是就不刪除
            return
        # 獲取 需要刪除的目錄 是在第幾個
        index = self.all_directory.index(directory)
        # 查看是否有 刪除目錄回調
        if self.directory_callable:
            # 執行回調
            self.directory_callable(self.all_directory[index])
        # 獲取需要刪除目錄之後的目錄
        for directory in self.all_directory[index + 1:].copy():
            # 目錄設置隱藏
            directory.hide()
            # 從目錄列表刪除
            self.all_directory.remove(directory)
            # 添加到未使用目錄
            self.unused_directory.append(directory)

    # 清空 目錄
    def directory_cls(self) -> None:
        for directory in self.all_directory.copy():
            # 目錄設置隱藏
            directory.hide()
            # 從目錄列表刪除
            self.all_directory.remove(directory)
            # 添加到未使用目錄
            self.unused_directory.append(directory)

    # 獲取 上一頁 是否可用
    def get_pgup(self) -> bool:
        return self.pgup_button.state

    # 獲取 下一頁 是否可用
    def get_pgon(self) -> bool:
        return self.pgon_button.state

    # 設置 重新整理gif 是否顯示
    def set_refresh_gif_visible(self, visible: bool) -> None:
        self.refresh_gif.setVisible(visible)

    # 設定上一頁 顯示狀態
    def set_pgup(self, visible: bool) -> None:
        self.pgup_button.set_image(visible)

    # 設定下一頁 顯示狀態
    def set_pgon(self, visible: bool) -> None:
        self.pgon_button.set_image(visible)

    # 設定目錄點擊回調
    def set_directory_callable(self, slot: Callable[[Directory], Awaitable[None] | None]) -> None:
        self.directory_callable = slot

    # 設置搜尋窗口回調
    def set_linedit_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.lineedit.returnPressed.connect(slot)

    # 設置 上一頁 回調
    def set_pgup_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.pgup_button.left_click.connect(slot)

    # 設置 下一頁 回調
    def set_pgon_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.pgon_button.left_click.connect(slot)

    # 設置 重新整理 回調
    def set_rectangle_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.refresh_button.left_click.connect(slot)

    # 設置 搜索路徑按鈕 回調
    def set_search_name_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.search_button_container.search_name.callable = slot

    # 設置 搜索所有按鈕 回調
    def set_search_all_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.search_button_container.search_all.callable = slot

    # 設置 搜索按鈕是否顯示 and 第二按鈕文字
    def set_search_visible(self, visible: bool, name: str = '') -> None:
        if visible:
            self.search_button_container.search_name.setText(name)
            self.search_button_container.search_name.resize(
                self.search_button_container.search_name.fontMetrics().horizontalAdvance(name) + 10, 25
            )
            self.search_button_container.search_name.setChecked(True)
            self.search_button_container.resize(
                self.search_button_container.search_name.x() + self.search_button_container.search_name.width(), 25
            )
            self.search_button_container.search_name.show()
            self.search_button_container.show()
        else:
            self.search_button_container.hide()
            self.search_button_container.search_name.hide()
            self.search_button_container.search_all.setChecked(True)
            self.search_button_container.resize(48, 25)
        self.search_button_container.move(self.width() - 240 - self.search_button_container.width(), 9)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        super(QListDirectory, self).resizeEvent(event)
        # 目錄容器 調整大小
        self.directory_container.resize(self.width(), 41)
        # 所有容器 調整大小
        self.all_widget.resize(self.width(), self.height() - 41)
        # 搜索容器 調整位置
        self.search_container.move(self.width() - 230, 1)
        # 搜索按鈕容器 調整位置
        self.search_button_container.move(self.width() - 240 - self.search_button_container.width(), 9)


class NListDirectory(NList):
    def __init__(self, parent: QWidget | None = None, quantity_limit: int = 1000, ) -> None:
        super().__init__(parent, quantity_limit)
        # 設置所有目錄
        self.all_directory: list[Directory, ...] = []
        # 設置未使用目錄
        self.unused_directory: list[Directory, ...] = []
        # 設置背景白色
        self.setStyleSheet('QListDirectory{background-color: rgb(255, 255, 255)}')
        # 設置目錄容器
        self.directory_container: QWidget = QWidget(self)
        # 設定目錄容器名稱
        self.directory_container.setObjectName('directory')
        # 根據名稱設定 上下 邊框
        self.directory_container.setStyleSheet(
            '#directory{border-style:solid; border-bottom-width:1px;'
            'border-top-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )
        # 設置搜索框容器
        self.search_container: QWidget = QWidget(self.directory_container)
        # 設置搜索框容器大小
        self.search_container.resize(230, 39)
        # 設置 搜索按鈕容器
        self.search_button_container: SearchContainer = SearchContainer(self)
        # 設置 左側直線
        self.left_line: Frame = Frame(self.directory_container)
        # 設置 左側直線 大小位置
        self.left_line.setGeometry(100, 13, 1, 16)
        # 設置 右側直線
        self.right_line: Frame = Frame(self.search_container)
        # 設置 右側直線 大小位置
        self.right_line.setGeometry(0, 12, 1, 16)
        # 設定 搜索窗口
        self.lineedit = LineEdit(self.search_container, '搜索', '', (12, 0, 218, 39), qss=1)
        # 設定 搜索窗口 大小位置
        self.lineedit.setGeometry(12, 0, 218, 39)

        # 設定 上一頁 按鈕
        self.pgup_button: MyIco = MyIco(
            self.directory_container,
            Image.MAX_BLACK_PREVIOUS_PAGE,
            Image.MAX_BLUE_PREVIOUS_PAGE,
            (18, 14, 8, 12),
            false=Image.MAX_GREY_PREVIOUS_PAGE
        )

        # 設定 下一頁 按鈕
        self.pgon_button: MyIco = MyIco(
            self.directory_container,
            Image.MAX_BLACK_NEXT_PAGE,
            Image.MAX_BLUE_NEXT_PAGE,
            (49, 14, 8, 12),
            false=Image.MAX_GREY_NEXT_PAGE
        )
        # 設定 刷新 按鈕
        self.refresh_button: MyIco = MyIco(
            self.directory_container,
            Image.BLACK_REFRESH,
            Image.BLUE_REFRESH,
            (75, 14, 13, 12),
            state=True
        )
        # 設置 重新整理 gif動畫
        self.refresh_gif: GifLabel = AllImage.get_gif(self, GifImage.REFRESH, (74, 13, 14, 14))
        # 初始化目錄回調
        self.directory_callable = None
        # 移動所有容器位置
        self.all_widget.move(0, 41)

    # 添加 新的 目錄
    def directory_add(self, text: str, data: any = None) -> None:
        if self.unused_directory:
            directory = self.unused_directory.pop()
            directory.set_data(text, data)
        else:
            # 獲取目錄
            directory = Directory(text, self.directory_container, data)
            # 連接目錄點擊回調
            directory.left_click.connect(self._directory_delete)
        # 目錄置底 為了防止穿透搜索欄被看到
        directory.lower()
        # 目錄顯示
        directory.show()
        # 查看是否是第一個
        if self.all_directory:
            # 獲取最後一個底部位置
            x = self.all_directory[-1].x() + self.all_directory[-1].width()
            # 移動目錄位置
            directory.move(x, 0)
        else:
            # 移動目錄位置
            directory.move(110, 0)
        # 添加至所有目錄
        self.all_directory.append(directory)

    # 刪除目錄
    def _directory_delete(self, directory: Directory) -> None:
        # 查看 需要刪除的目錄 是否是最後一個
        if self.all_directory[-1] == directory:
            # 如果是就不刪除
            return
        # 獲取 需要刪除的目錄 是在第幾個
        index = self.all_directory.index(directory)
        # 查看是否有 刪除目錄回調
        if self.directory_callable:
            # 執行回調
            self.directory_callable(self.all_directory[index])
        # 獲取需要刪除目錄之後的目錄
        for directory in self.all_directory[index + 1:].copy():
            # 目錄設置隱藏
            directory.hide()
            # 從目錄列表刪除
            self.all_directory.remove(directory)
            # 添加到未使用目錄
            self.unused_directory.append(directory)

    # 清空 目錄
    def directory_cls(self) -> None:
        for directory in self.all_directory.copy():
            # 目錄設置隱藏
            directory.hide()
            # 從目錄列表刪除
            self.all_directory.remove(directory)
            # 添加到未使用目錄
            self.unused_directory.append(directory)

    # 獲取 上一頁 是否可用
    def get_pgup(self) -> bool:
        return self.pgup_button.state

    # 獲取 下一頁 是否可用
    def get_pgon(self) -> bool:
        return self.pgon_button.state

    # 設置 重新整理gif 是否顯示
    def set_refresh_gif_visible(self, visible: bool) -> None:
        self.refresh_gif.setVisible(visible)

    # 設定上一頁 顯示狀態
    def set_pgup(self, visible: bool) -> None:
        self.pgup_button.set_image(visible)

    # 設定下一頁 顯示狀態
    def set_pgon(self, visible: bool) -> None:
        self.pgon_button.set_image(visible)

    # 設定目錄點擊回調
    def set_directory_callable(self, slot: Callable[[Directory], Awaitable[None] | None]) -> None:
        self.directory_callable = slot

    # 設置搜尋窗口回調
    def set_linedit_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.lineedit.returnPressed.connect(slot)

    # 設置 上一頁 回調
    def set_pgup_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.pgup_button.left_click.connect(slot)

    # 設置 下一頁 回調
    def set_pgon_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.pgon_button.left_click.connect(slot)

    # 設置 重新整理 回調
    def set_rectangle_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.refresh_button.left_click.connect(slot)

    # 設置 搜索路徑按鈕 回調
    def set_search_name_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.search_button_container.search_name.callable = slot

    # 設置 搜索所有按鈕 回調
    def set_search_all_callable(self, slot: Callable[[], Awaitable[None] | None]) -> None:
        self.search_button_container.search_all.callable = slot

    # 設置 搜索按鈕是否顯示 and 第二按鈕文字
    def set_search_visible(self, visible: bool, name: str = '') -> None:
        if visible:
            self.search_button_container.search_name.setText(name)
            self.search_button_container.search_name.resize(
                self.search_button_container.search_name.fontMetrics().horizontalAdvance(name) + 10, 25
            )
            self.search_button_container.search_name.setChecked(True)
            self.search_button_container.resize(
                self.search_button_container.search_name.x() + self.search_button_container.search_name.width(), 25
            )
            self.search_button_container.search_name.show()
            self.search_button_container.show()
        else:
            self.search_button_container.hide()
            self.search_button_container.search_name.hide()
            self.search_button_container.search_all.setChecked(True)
            self.search_button_container.resize(48, 25)
        self.search_button_container.move(self.width() - 240 - self.search_button_container.width(), 9)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        # 目錄容器 調整大小
        self.directory_container.resize(self.width(), 41)
        # 所有容器 調整大小
        self.all_widget.resize(self.width(), self.height() - 41)
        # 搜索容器 調整位置
        self.search_container.move(self.width() - 230, 1)
        # 搜索按鈕容器 調整位置
        self.search_button_container.move(self.width() - 240 - self.search_button_container.width(), 9)
