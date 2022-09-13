from PyQt5.Qt import QFrame, pyqtSignal, QWidget, QCursor, QMenu, Qt, QScrollArea, QVBoxLayout, QApplication, QColor,\
    QPainter, QPen, QLabel, QFont, QLineEdit, QPixmap, QPoint, QPushButton

from PyQt5.QtCore import QMetaMethod
import sys
import base64
from .QImag import backdrop, picture, gif, font


# 設定邊框
class Frame(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet('background-color:rgba(200, 200, 200, 125)')


class MyLabel(QWidget):
    left_click = pyqtSignal(QWidget)

    def __init__(self, text, data=None, path=None, parent=None):
        super(MyLabel, self).__init__(parent)
        self.path = path
        self.data = data
        self.label_1 = QLabel(self)
        font = QFont()
        # 設置字體大小
        font.setPointSize(11)
        # 設定標題字體大小
        self.label_1.setFont(font)
        self.label_1.setText(text)
        width = self.label_1.fontMetrics().boundingRect(self.label_1.text()).width()
        self.label_1.setGeometry(0, 7, width, 25)
        self.label_2 = QLabel(self)
        self.label_2.setGeometry(width + 13, 17, 6, 8)
        self.label_2.setPixmap(picture('向右黑色'))
        self.resize(width + 32, 35)
        self.setStyleSheet("QLabel{color:rgb(0,0,0);}"
                           "QLabel:hover{color:rgb(6,168,255);}")

    def text(self):
        return self.label_1.text()

    # 單擊
    def mousePressEvent(self, event):
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            self.left_click.emit(self)

    # 鼠標移出label
    def leaveEvent(self, event):
        self.label_2.setPixmap(picture('向右黑色'))

    # 鼠標移入label
    def enterEvent(self, event):
        self.label_2.setPixmap(picture('向右藍色'))


class NewString(str):
    def __new__(cls, value, othervalue):
        return str.__new__(cls, value)

    def __init__(self, value, data):
        self.data = data


# 前進後退子控件
class MyIco(QLabel):
    left_click = pyqtSignal(QWidget)

    def __init__(self, leave, enter, coordinate=None, state=False, click=None, parent=None):
        super().__init__(parent)
        # 設定是否能夠變色 or 是否能夠發出點擊訊號
        self.state = state
        # 初始化預設圖片
        self.setPixmap(picture(leave))
        # 滑鼠預設圖片
        self.leave = leave
        # 滑鼠進入圖片
        self.enter = enter
        # 圖片置中
        self.setAlignment(Qt.AlignCenter)
        # 是否設定大小
        if coordinate:
            self.setGeometry(*coordinate)
        # 是否設定左鍵點擊事件
        if click:
            self.left_click.connect(click)

    def setimage(self, leave):
        self.leave = leave
        self.setPixmap(picture(leave))

    # 單擊
    def mousePressEvent(self, event):
        # 左鍵
        if event.buttons() == Qt.LeftButton and self.state:
            self.left_click.emit(self)

    # 鼠標移出label
    def leaveEvent(self, event):
        if self.state:
            self.setPixmap(picture(self.leave))

    # 鼠標移入label
    def enterEvent(self, event):
        if self.state:
            self.setPixmap(picture(self.enter))


class MyQLabel(QLabel):
    # 左鍵點擊
    leftclick = pyqtSignal(object)
    # 右鍵點擊
    rightclick = pyqtSignal(object)
    # 左鍵雙擊
    doubleclick = pyqtSignal(object)
    # # 當前點擊
    # currentlyclick = pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)
        self.slot = None

    # 單擊
    def mousePressEvent(self, event):
        # 發送自己是第幾格的訊號
        # self.currentlyclick.emit(self if isinstance(self, Label) else self.parent())
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            self.leftclick.emit(self.slot)

        # 右鍵
        elif event.buttons() == Qt.RightButton:
            self.rightclick.emit(self.slot)

    # 雙擊
    def mouseDoubleClickEvent(self, event):
        # self.currentlyclick.emit(self)
        self.doubleclick.emit(self.slot)


# 複選紐
class ClickQLabel(MyQLabel):
    def __init__(self, parent):
        super().__init__(parent)
        # 複選紐選中狀態
        self.status = False
        # 複選紐全部圖片
        self.image = {False: picture('複選空白'), True: picture('複選打勾'), 'hover': picture('複選空白藍色')}
        # 設定預設圖片
        self.setimage(False)
        # 設置本身大小跟圖案一樣
        self.resize(self.image[False].size())
        # 圖片置中
        self.setAlignment(Qt.AlignCenter)

    # 設定是否選中圖片
    def setimage(self, status):
        self.setPixmap(self.image[status])
        self.status = status

    # 鼠標移出label
    def leaveEvent(self, event):
        if not self.status:
            self.setPixmap(self.image[self.status])

    # 鼠標移入label
    def enterEvent(self, event):
        if not self.status:
            self.setPixmap(self.image['hover'])