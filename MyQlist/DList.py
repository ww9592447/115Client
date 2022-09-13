from .package import QPushButton, Frame, MyIco, Qt, QLabel, pyqtSignal, picture, QWidget, QFont, QFrame, QLineEdit, gif
from .QList import ListCheck
from .NList import NList


class _SearchButton(QPushButton):
    def __init__(self, parent=None):
        super(_SearchButton, self).__init__(parent)
        # 設置成可切換按鈕
        self.setCheckable(True)
        # 設置成自動排他按鈕
        self.setAutoExclusive(True)
        # 回調
        self.callback = None


class SearchButton(QFrame):
    def __init__(self, parent=None):
        super(SearchButton, self).__init__(parent)
        # 設置 背景空白 按鈕 QSS
        self.setStyleSheet(
            'SearchContents{background-color:rgb(255, 255, 255)}'
            'QPushButton{background-color: rgb(242, 242, 242);border-radius: 5px}'
            'QPushButton:hover{background-color: rgb(229, 229, 229);}'
            'QPushButton:checked{background-color: rgb(204, 204, 204);}'
        )
        self.search_all = _SearchButton(parent=self)
        self.search_all.setChecked(True)
        self.search_all.toggled.connect(self._setcursor)
        self.search_all.setCursor(Qt.ArrowCursor)
        self.search_all.setText('全部')
        self.search_all.resize(48, 25)
        self.search_name = _SearchButton(parent=self)
        self.search_name.toggled.connect(self._setcursor)
        self.search_name.setCursor(Qt.PointingHandCursor)
        self.search_name.move(55, 0)
        self.search_name.hide()
        self.resize(48, 25)
        QFrame.hide(self)

    def _setcursor(self, value):
        if value:
            self.sender().setCursor(Qt.ArrowCursor)
            if self.isVisible():
                if self.sender().callback:
                    self.sender().callback()
        else:
            self.sender().setCursor(Qt.PointingHandCursor)

    def setname(self, text):
        self.search_name.setText(text)
        self.search_name.resize(self.search_name.fontMetrics().horizontalAdvance(text) + 10, 25)
        self.search_name.show()
        self.search_name.setChecked(True)
        self.resize(self.search_name.x() + self.search_name.width(), 25)

    def set_search_name_callback(self, slot):
        self.search_name.callback = slot

    def set_search_all_callback(self, slot):
        self.search_all.callback = slot

    def hide_(self):
        QFrame.hide(self)
        self.search_name.hide()
        self.search_all.setChecked(True)
        self.resize(48, 25)

    def show(self):
        QFrame.show(self)
        self.move(self.parent().width() - 240 - self.width(), 9)


class Directory(QFrame):
    leftclick = pyqtSignal(QWidget)

    def __init__(self, text, data, path, parent):
        super(Directory, self).__init__(parent)
        self.path = path
        self.data = data
        self.text = QLabel(self)
        font = QFont()
        # 設置字體大小
        font.setPointSize(11)
        # 設定標題字體大小
        self.text.setFont(font)
        self.text.setText(text)
        width = self.text.fontMetrics().horizontalAdvance(text)
        self.text.setGeometry(0, 7, width, 25)
        self.ico = QLabel(self)
        self.ico.setGeometry(width + 9, 17, 6, 8)
        self.ico.setPixmap(picture('向右黑色'))
        self.resize(width + 25, 35)

    def text(self):
        return self.text.text()

    # 單擊
    def mousePressEvent(self, event):
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            self.leftclick.emit(self)

    # 鼠標移出label
    def leaveEvent(self, event):
        self.setStyleSheet("QLabel{color:rgb(0,0,0);}")
        self.ico.setPixmap(picture('向右黑色'))

    # 鼠標移入label
    def enterEvent(self, event):
        self.setStyleSheet("QLabel{color:rgb(6,168,255);}")
        self.ico.setPixmap(picture('向右藍色'))


def ListDirectory(value, _parent):
    if value:
        _value = ListCheck
    else:
        _value = NList

    class _ListDirectory(_value):
        def __init__(self, parent=None):
            super().__init__(parent)
            # 所有路徑
            self.all_path = []
            # 所有目錄
            self.alldirectory = []
            # 目錄容器
            self.directorycontainer = QFrame(self)
            # 設定目錄容器名稱
            self.directorycontainer.setObjectName('directory')
            # 跟據名稱設定 上下 邊框
            self.directorycontainer.setStyleSheet('#directory{border-style:solid; border-bottom-width:1px;'
                                                  'border-top-width:1px; border-color:rgba(200, 200, 200, 125)}')
            # 移動目錄容器位置
            # 刪除路徑回調 返回 text data
            self.directory_slot = None
            # 設定 上一頁 按鈕
            self.pgup_button = MyIco('返回透明', '返回藍色', coordinate=(18, 14, 8, 12), parent=self.directorycontainer)
            # 設定 下一頁 按鈕
            self.pgon_button = MyIco('前進透明', '前進藍色', coordinate=(49, 14, 8, 12), parent=self.directorycontainer)
            # 重新整理按鈕
            self.refresh_button = MyIco('重新整理黑色', '重新整理藍色', coordinate=(75, 14, 13, 12), state=True,
                                        parent=self.directorycontainer)
            # 移動所有容器位置
            self.allqwidget.move(0, 41)
            # 設置左側直線
            self.left_line = Frame(self.directorycontainer)
            self.left_line.setGeometry(100, 13, 1, 16)
            # 設置搜索容器
            self.searchcontainer = QFrame(self.directorycontainer)
            # 設置搜索容器背景白色
            self.searchcontainer.setStyleSheet('QFrame{background-color: rgb(255, 255, 255)}')
            # 設置搜索容器大小
            self.searchcontainer.resize(230, 39)
            # 設置右側直線
            self.right_line = Frame(self.searchcontainer)
            self.right_line.setGeometry(0, 12, 1, 16)
            # 設定 搜索窗口
            self.lineEdit = QLineEdit(self.searchcontainer)
            self.lineEdit.setGeometry(12, 0, 218, 39)
            self.lineEdit.setPlaceholderText('搜索你的文件')
            font = QFont()
            # 設置字體大小
            font.setPointSize(10)
            self.lineEdit.setFont(font)
            self.lineEdit.setStyleSheet("QLineEdit{border-width:0;border-style:outset}")

            self.searchbutton = SearchButton(self)

            # 重新整理gif動畫
            self.refresh_gif = gif(self, '重新整理')
            self.refresh_gif.setGeometry(74, 13, 14, 14)

        # 隱藏重新整理GIF
        def refresh_hide(self):
            self.refresh_gif.hide()

        # 顯示重新整理GIF
        def refresh_show(self):
            self.refresh_gif.show()

        def get_pgup(self):
            return self.pgup_button.state

        def get_pgon(self):
            return self.pgon_button.state

        # 設定上一頁 顯示狀態
        def set_pgup(self, _bool):
            self.pgup_button.state = _bool
            if _bool:
                self.pgup_button.setimage('返回黑色')
            else:
                self.pgup_button.setimage('返回透明')

        # 設定 下一頁 顯示狀態
        def set_pgon(self, _bool):
            self.pgon_button.state = _bool
            if _bool:
                self.pgon_button.setimage('前進黑色')
            else:
                self.pgon_button.setimage('前進透明')

        # 設定 目錄 點擊回調
        def menu_callback(self, slot):
            self.menu_callback = slot

        # 設置搜尋窗口回調
        def linedit_connect(self, slot):
            self.lineEdit.returnPressed.connect(slot)

        # 設置 上一頁 回調
        def pgup_connect(self, slot):
            self.pgup_button.left_click.connect(slot)

        # 設置 下一頁 回調
        def pgon_connect(self, slot):
            self.pgon_button.left_click.connect(slot)

        # 設置 重新整理 回調
        def rectangle_connect(self, slot):
            self.refresh_button.left_click.connect(slot)

        # 添加 新的 目錄
        def directory_add(self, text, data=None):
            self.all_path.append((text, data))
            label = Directory(text, data, self.all_path.copy(), self.directorycontainer)
            label.leftclick.connect(self._directory_delete)
            label.lower()
            label.show()
            if self.alldirectory:
                x = self.alldirectory[-1].x() + self.alldirectory[-1].width()
                label.move(x, 0)
            else:
                label.move(110, 0)
            self.alldirectory.append(label)
            # x = label.x() + label.width()
            # label.resize(x, 41)

        # 清空 目錄
        def directory_cls(self):
            self.all_path = []
            for _label in self.alldirectory.copy():
                index = self.alldirectory.index(_label)
                self.alldirectory[index].setParent(None)
                self.alldirectory[index].deleteLater()
                self.alldirectory.pop(index)

        def setname(self, text):
            self.searchbutton.setname(text)

        def set_search_name_connect(self, slot):
            self.searchbutton.set_search_name_callback(slot)

        def set_search_all_connect(self, slot):
            self.searchbutton.set_search_all_callback(slot)

        # 刪除目錄
        def _directory_delete(self, label):
            if self.alldirectory[-1] == label:
                return
            index = self.alldirectory.index(label)
            if self.directory_slot:
                self.directory_slot(self.alldirectory[index])
            for _label in self.alldirectory[index + 1:].copy():
                index = self.alldirectory.index(_label)
                self.alldirectory[index].setParent(None)
                self.alldirectory[index].deleteLater()
                self.alldirectory.pop(index)

        def resizeEvent(self, event):
            _value.resizeEvent(self, event)
            self.directorycontainer.resize(self.width(), 41)
            self.allqwidget.resize(self.width(), self.height() - 41)
            self.searchcontainer.move(self.width() - 230, 1)
            self.searchbutton.move(self.width() - 240 - self.searchbutton.width(), 9)

    return _ListDirectory(parent=_parent)
