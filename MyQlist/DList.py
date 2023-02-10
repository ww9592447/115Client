from .module import QApplication, sys, QResizeEvent, Optional, QPushButton, Frame, MyIco,\
    Qt, QLabel, pyqtSignal, picture, QWidget, QFont, QFrame, QLineEdit, gif,\
    Callable, QMouseEvent, QEvent, QButtonGroup
from .QList import ListCheck
from .NList import NList


class SearchButton(QPushButton):
    def __init__(self, parent=None) -> None:
        super(SearchButton, self).__init__(parent)
        # 設置成可切換按鈕
        self.setCheckable(True)
        # 設置成自動排他按鈕
        self.setAutoExclusive(True)
        # 回調
        self.callback = None


# 搜索容器
class SearchContents(QFrame):
    def __init__(self, parent=None) -> None:
        super(SearchContents, self).__init__(parent)
        # 設置搜索所有按鈕
        self.search_all: SearchButton = SearchButton(parent=self)
        # 設置搜索所有按鈕切換回調
        self.search_all.toggled.connect(self._setcursor)
        # 設置滑鼠上方圖案
        self.search_all.setCursor(Qt.ArrowCursor)
        # 設置搜索所有按鈕文字
        self.search_all.setText('全部')
        # 設置搜索所有按鈕大小
        self.search_all.resize(48, 25)
        # 設置搜索路徑按鈕
        self.search_name = SearchButton(parent=self)
        # 設置搜索路徑按鈕點擊
        self.search_all.setChecked(True)
        # 設置搜索路徑按鈕切換回調
        self.search_name.toggled.connect(self._setcursor)
        # 設置滑鼠上方圖案
        self.search_name.setCursor(Qt.PointingHandCursor)
        # 設置搜索路徑按鈕位置
        self.search_name.move(55, 0)
        # 搜索路徑按鈕隱藏
        self.search_name.hide()

        self.btngroup = QButtonGroup(self)
        self.btngroup.addButton(self.search_all)
        self.btngroup.addButton(self.search_name)
        # 設置搜索按鈕容器大小
        self.resize(48, 25)
        # 隱藏搜索容器
        QFrame.hide(self)
        # 設置 背景空白 按鈕 QSS
        self.setStyleSheet(
            'SearchContents{background-color:rgb(255, 255, 255)}'
            'QPushButton{background-color: rgb(242, 242, 242);border-radius: 5px}'
            'QPushButton:hover{background-color: rgb(229, 229, 229);}'
            'QPushButton:checked{background-color: rgb(204, 204, 204);}'
        )

    # 設置滑鼠狀態
    def _setcursor(self, value: bool) -> None:
        if value:
            self.sender().setCursor(Qt.ArrowCursor)
            if self.isVisible():
                if self.sender().callback:
                    self.sender().callback()
        else:
            self.sender().setCursor(Qt.PointingHandCursor)

    # 設置搜索路徑按鈕 名稱
    def setname(self, text: str) -> None:
        self.search_name.setText(text)
        self.search_name.resize(self.search_name.fontMetrics().horizontalAdvance(text) + 10, 25)
        self.search_name.show()
        self.search_name.setChecked(True)
        self.resize(self.search_name.x() + self.search_name.width(), 25)

    # 設置 搜索路徑按鈕 回調
    def set_search_name_callback(self, slot: Callable) -> None:
        self.search_name.callback = slot

    # 設置 搜索所有按鈕 回調
    def set_search_all_callback(self, slot: Callable) -> None:
        self.search_all.callback = slot

    # 隱藏搜索按鈕
    def hide_(self) -> None:
        QFrame.hide(self)
        self.search_name.hide()
        self.search_all.setChecked(True)
        self.resize(48, 25)

    # 顯示搜索按鈕
    def show(self) -> None:
        QFrame.show(self)
        self.move(self.parent().width() - 240 - self.width(), 9)


class Directory(QFrame):
    leftclick = pyqtSignal(QWidget)

    def __init__(self, text: str, data: any, parent) -> None:
        super(Directory, self).__init__(parent)
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
        # 設置 向右黑色 箭頭
        self.ico = QLabel(self)
        # 設置 向右黑色 大小
        self.ico.setGeometry(width + 9, 17, 6, 8)
        # 設置 向右黑色 箭頭 圖片
        self.ico.setPixmap(picture('向右黑色'))
        # 設置 目錄大小
        self.resize(width + 25, 35)

    def text(self) -> None:
        return self.text.text()

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            self.leftclick.emit(self)

    # 鼠標移出事件
    def leaveEvent(self, event: QEvent) -> None:
        self.setStyleSheet("QLabel{color:rgb(0,0,0);}")
        self.ico.setPixmap(picture('向右黑色'))

    # 鼠標移入事件
    def enterEvent(self, event: QEvent) -> None:
        self.setStyleSheet("QLabel{color:rgb(6,168,255);}")
        self.ico.setPixmap(picture('向右藍色'))


def ListDirectory(value, _parent=None):
    if value:
        _value = ListCheck
    else:
        _value = NList

    class _ListDirectory(_value):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            # 所有路徑
            self.allpath: list[tuple[str, any], ...] = []
            # 所有目錄
            self.alldirectory: list[Directory, ...] = []
            # 目錄容器
            self.directorycontainer: QFrame = QFrame(self)
            # 設定目錄容器名稱
            self.directorycontainer.setObjectName('directory')
            # 跟據名稱設定 上下 邊框
            self.directorycontainer.setStyleSheet('#directory{border-style:solid; border-bottom-width:1px;'
                                                  'border-top-width:1px; border-color:rgba(200, 200, 200, 125)}')

            # 設定 上一頁 按鈕
            self.pgup_button: MyIco = MyIco(
                '返回黑色', '返回藍色', coordinate=(18, 14, 8, 12), false='返回透明',parent=self.directorycontainer
            )
            # 設定 下一頁 按鈕
            self.pgon_button: MyIco = MyIco(
                '前進黑色', '前進藍色', coordinate=(49, 14, 8, 12), false='前進透明', parent=self.directorycontainer
            )
            # 重新 整理按鈕
            self.refresh_button: MyIco = MyIco(
                '重新整理黑色', '重新整理藍色', coordinate=(75, 14, 13, 12), state=True, parent=self.directorycontainer
            )
            # 設置搜索框容器
            self.searchcontainer: QFrame = QFrame(self.directorycontainer)
            # 設置搜索框容器背景白色
            self.searchcontainer.setStyleSheet('QFrame{background-color: rgb(255, 255, 255)}')
            # 設置搜索框容器大小
            self.searchcontainer.resize(230, 39)
            # 設置 搜索按鈕容器
            self.searchcontents: SearchContents = SearchContents(self)
            # 設置 左側直線
            self.left_line: Frame = Frame(self.directorycontainer)
            # 設置 左側直線 大小位置
            self.left_line.setGeometry(100, 13, 1, 16)
            # 設置 右側直線
            self.right_line: Frame = Frame(self.searchcontainer)
            # 設置 右側直線 大小位置
            self.right_line.setGeometry(0, 12, 1, 16)
            # 設定 搜索窗口
            self.lineEdit: QLineEdit = QLineEdit(self.searchcontainer)
            # 設定 搜索窗口 大小位置
            self.lineEdit.setGeometry(12, 0, 218, 39)
            # 設置 搜索窗口 顯示文字
            self.lineEdit.setPlaceholderText('搜索你的文件')
            # 獲取 字體
            font = QFont()
            # 設置字體大小
            font.setPointSize(10)
            # 替換字體
            self.lineEdit.setFont(font)
            # 設置 搜索窗口 qss
            self.lineEdit.setStyleSheet("QLineEdit{border-width:0;border-style:outset}")
            # 重新整理 gif動畫
            self.refresh_gif: QLabel = gif(self, '重新整理')
            # 設定 重新整理 gif大小位置
            self.refresh_gif.setGeometry(74, 13, 14, 14)
            # 刪除目錄回調
            self.directory_slot: Optional[Callable] = None
            # 移動所有容器位置
            self.allqwidget.move(0, 41)

        # 添加 新的 目錄
        def directory_add(self, text: str, data: any = None) -> None:
            # 添加至所有路徑
            self.allpath.append((text, data))
            # 獲取目錄
            label = Directory(text, data, self.directorycontainer)
            # 連接目錄點擊回調
            label.leftclick.connect(self._directory_delete)
            # 目錄置底 為了防止穿透搜索欄被看到
            label.lower()
            # 目錄顯示
            label.show()
            # 查看是否是第一個
            if self.alldirectory:
                # 獲取最後一個底部位置
                x = self.alldirectory[-1].x() + self.alldirectory[-1].width()
                # 移動目錄位置
                label.move(x, 0)
            else:
                # 移動目錄位置
                label.move(110, 0)
            # 添加至所有目錄
            self.alldirectory.append(label)

        # 刪除目錄
        def _directory_delete(self, label: Directory) -> None:
            # 查看 需要刪除的目錄 是否是最後一個
            if self.alldirectory[-1] == label:
                # 如果是就不刪除
                return
            # 獲取 需要刪除的目錄 是在第幾個
            index = self.alldirectory.index(label)
            # 查看是否有 刪除目錄回調
            if self.directory_slot:
                # 執行回調
                self.directory_slot(self.alldirectory[index])
            # 獲取需要刪除目錄之後的目錄
            for label in self.alldirectory[index + 1:].copy():
                # 目錄設置隱藏
                label.setParent(None)
                # 目錄刪除
                label.deleteLater()
                # 從目錄列表刪除
                self.alldirectory.remove(label)

        # 清空 目錄
        def directory_cls(self) -> None:
            self.allpath = []
            for label in self.alldirectory.copy():
                # 目錄設置隱藏
                label.setParent(None)
                # 目錄刪除
                label.deleteLater()
                # 從目錄列表刪除
                self.alldirectory.remove(label)

        # 設置 重新整理gif 是否顯示
        def set_refresh_gif_visible(self, visible: bool) -> None:
            self.refresh_gif.setVisible(visible)

        # 設定上一頁 顯示狀態
        def set_pgup(self, visible: bool) -> None:
            self.pgup_button.setimage(visible)

        # 設定下一頁 顯示狀態
        def set_pgon(self, visible: bool) -> None:
            self.pgon_button.setimage(visible)

        # 獲取 上一頁 是否可用
        def get_pgup(self) -> bool:
            return self.pgup_button.state

        # 獲取 下一頁 是否可用
        def get_pgon(self) -> bool:
            return self.pgon_button.state

        # 設置搜尋窗口回調
        def linedit_connect(self, slot: Callable) -> None:
            self.lineEdit.returnPressed.connect(slot)

        # 設置 上一頁 回調
        def pgup_connect(self, slot: Callable) -> None:
            self.pgup_button.leftclick.connect(slot)

        # 設置 下一頁 回調
        def pgon_connect(self, slot: Callable) -> None:
            self.pgon_button.leftclick.connect(slot)

        # 設置 重新整理 回調
        def rectangle_connect(self, slot: Callable) -> None:
            self.refresh_button.leftclick.connect(slot)

        # 調整大小事件
        def resizeEvent(self, event: QResizeEvent) -> None:
            super(_ListDirectory, self).resizeEvent(event)
            # 目錄容器 調整大小
            self.directorycontainer.resize(self.width(), 41)
            # 所有容器 調整大小
            self.allqwidget.resize(self.width(), self.height() - 41)
            # 搜索容器 調整位置
            self.searchcontainer.move(self.width() - 230, 1)
            # 搜索按鈕容器 調整位置
            self.searchcontents.move(self.width() - 240 - self.searchcontents.width(), 9)

    return _ListDirectory(parent=_parent)