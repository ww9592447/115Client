from PyQt5.Qt import QFrame, pyqtSignal, QWidget, Qt, QLabel, QPixmap, QEvent, QMouseEvent, QFont, QPushButton, \
    QColor, QTimer, QPainter, QRect, QPainterPath, QRectF, QPaintEvent, QRadioButton, QIcon, QResizeEvent, QLineEdit, \
    QAction, QListWidgetItem, QContextMenuEvent, QApplication
from typing import Callable, Awaitable
from Modules.image import AllImage, Image, IcoImage
from Modules.menu import Menu


class MyPushButton(QPushButton):
    def __init__(
            self,
            parent: QWidget | None,
            text: str = '',
            geometry: tuple[int, int, int, int] | None = None,
            move: tuple[int, int] | None = None,
            qss: int | None = None,
            padding: tuple[int, int, int, int] | str = '',
            font: str = '',
            font_size: int = 11,
            icon: QIcon | None = None,
            click: Callable[[], None | bool | Awaitable[any]] = None
    ) -> None:
        super().__init__(parent)
        _qss = ''
        if qss == 1:
            _qss = """
                MyPushButton {
                    color: white;
                    background-color: rgb(0, 159, 170);
                    border-radius: 5px;
                }
                MyPushButton:hover {background-color: rgb(0, 167, 179);}
                MyPushButton:pressed {
                    color: rgba(255, 255, 255, 0.63);
                    background-color: rgb(62, 171, 179);
                }
                MyPushButton:disabled {
                    color: rgba(255, 255, 255, 0.9);
                    background-color: rgb(205, 205, 205);
                }
                """

        elif qss == 2:
            _qss = """
                MyPushButton {
                    color: black;
                    background: rgb(251, 251, 251);
                    border: 1px solid rgb(229, 229, 229);
                    border-radius: 5px;
                    vertical-align:middle;
                }
                MyPushButton:hover {
                    background: rgb(246, 246, 246);
                }
                MyPushButton:pressed {
                    color: rgba(0, 0, 0, 0.63);
                    background: rgb(245, 245, 245);
                }
                MyPushButton:disabled{
                    border-color: rgb(227, 227, 227);
                    background-color: rgb(247, 247, 247);
                    color: rgb(155, 155, 155)
                }
                """
        elif qss == 3:
            _qss = """                
                MyPushButton {
                    color: blue;
                    border: 0px;
                    background-color: transparent;
                }
                """

        if padding:
            padding = f'padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;'
        if qss:
            _qss += f"MyPushButton {{font: {font_size}px '{font}'; {padding}}}"

        if icon:
            self.setIcon(icon)
            self.setStyleSheet('MyPushButton{background-color: transparent}')
        else:
            self.setStyleSheet(_qss)
            self.setText(text)

        self.setCursor(Qt.PointingHandCursor)

        if geometry:
            self.setGeometry(*geometry)
        if move:
            self.move(*move)
        if click:
            self.clicked.connect(click)


class RadioButton(QRadioButton):
    def __init__(
            self,
            parent: QWidget,
            text: str,
            move: tuple[int, int] | None = None,
            geometry: tuple[int, int, int, int] | None = None,
            font_size: int | None = None,
            checked: bool | None = None,
            click: Callable[[], Awaitable[any] | bool | None] | None = None
    ) -> None:
        super().__init__(parent)
        if font_size:
            # 獲取字體
            font = QFont()
            # 設置字體大小
            font.setPointSize(font_size)
            # 替換字體
            self.setFont(font)
        # 設置文字
        self.setText(text)
        # 自動調整大小
        self.adjustSize()
        if checked:
            self.setChecked(checked)
        if move:
            self.move(*move)
        if geometry:
            self.setGeometry(*geometry)
        if click:
            self.clicked.connect(click)


class TextLabel(QLabel):
    def __init__(
            self,
            parent: QWidget,
            text: str,
            move: tuple[int, int] | None = None,
            geometry: tuple[int, int, int, int] | None = None,
            font_size: int | None = None
    ) -> None:
        super().__init__(parent)
        if font_size:
            # 獲取字體
            font = QFont()
            # 設置字體大小
            font.setPointSize(font_size)
            # 替換字體
            self.setFont(font)
        # 設置文字
        self.setText(text)
        # 自動調整大小
        self.adjustSize()
        if move:
            self.move(*move)
        if geometry:
            self.setGeometry(*geometry)


class MyLabel(QLabel):
    # 左鍵單擊
    left_click: pyqtSignal = pyqtSignal(QWidget)
    # 右鍵單擊
    right_click: pyqtSignal = pyqtSignal(QWidget)
    # 左鍵雙擊
    double_click: pyqtSignal = pyqtSignal(QWidget)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)


class MyFrame(QFrame):
    # 左鍵單擊
    left_click = pyqtSignal(QWidget)
    # 右鍵單擊
    right_click = pyqtSignal(QWidget)
    # 左鍵雙擊
    double_click = pyqtSignal(QWidget)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)


# 複選紐
class ClickLabel(MyLabel):
    state: bool = False
    image: dict[bool, QPixmap] = {}
    hover: QPixmap
    slot: QWidget = None

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.image.update({
            True: AllImage.get_image(Image.SELECTED_CHECK_BUTTON),
            False: AllImage.get_image(Image.BLACK_CHECK_BUTTON)
        })
        self.hover = AllImage.get_image(Image.BLUE_CHECK_BUTTON)
        # 設定預設圖片
        self.set_image(False)
        # 設置本身大小跟圖案一樣
        self.resize(self.image[False].size())
        # 圖片置中
        self.setAlignment(Qt.AlignCenter)

    def set_image(self, state: bool) -> None:
        # 設置複選紐狀態
        self.state = state
        # 設置複選紐圖片
        self.setPixmap(self.image[state])

    # 鼠標移出事件
    def leaveEvent(self, event: QEvent) -> None:
        if not self.state:
            self.setPixmap(self.image[self.state])

    # 鼠標移入事件
    def enterEvent(self, event: QEvent) -> None:
        if not self.state:
            self.setPixmap(self.hover)

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            self.left_click.emit(self.slot)
        # 右鍵
        elif event.buttons() == Qt.RightButton:
            self.right_click.emit(self.slot)


# 前進後退子控件
class MyIco(QLabel):
    left_click = pyqtSignal(QLabel)
    state: bool
    leave: QPixmap
    enter: QPixmap
    false: QPixmap | None

    def __init__(
            self,
            parent: QWidget,
            leave: Image,
            enter: Image,
            coordinate: tuple[int, ...],
            false: Image | None = None,
            state: bool = False,
            click: Callable[[], Awaitable[None] | bool | None] = None
    ) -> None:
        super().__init__(parent)
        # 設定是否能夠變色 or 是否能夠發出點擊訊號
        self.state: bool = state
        # 滑鼠預設圖片文字
        self.leave: QPixmap = AllImage.get_image(leave)
        # 滑鼠進入圖片文字
        self.enter: QPixmap = AllImage.get_image(enter)
        # 禁止圖片
        self.false: QPixmap | None = AllImage.get_image(false) if false else None
        # 初始化預設圖片
        self.setPixmap(self.false if self.state is False and self.false else self.leave)
        # 圖片置中
        self.setAlignment(Qt.AlignCenter)
        # 是否設定大小
        if coordinate:
            self.setGeometry(*coordinate)
        # 是否設定左鍵點擊事件
        if click:
            self.left_click.connect(click)

    # 初始化圖片
    def initialization(self) -> None:
        # 初始化預設圖片
        self.setPixmap(self.false if self.state is False and self.false else self.leave)

    # 設定圖片狀態
    def set_image(self, state: bool) -> None:
        if self.false:
            # 設定是否能夠變色 or 是否能夠發出點擊訊號
            self.state = state
            # 初始化預設圖片
            self.setPixmap(self.leave if state else self.false)

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 左鍵
        if event.buttons() == Qt.LeftButton and self.state:
            self.left_click.emit(self)

    # 鼠標移出事件
    def leaveEvent(self, event: QEvent) -> None:
        if self.state:
            self.setPixmap(self.leave)

    # 鼠標移入事件
    def enterEvent(self, event: QEvent) -> None:
        if self.state:
            self.setPixmap(self.enter)


# 灰色邊框
class Frame(QFrame):
    def __init__(
            self,
            parent: QWidget
            , geometry: tuple[int, int, int, int] | None = None,) -> None:
        super().__init__(parent)

        if geometry:
            self.setGeometry(*geometry)

        self.setStyleSheet('background-color:rgba(200, 200, 200, 125)')


class SwitchBtn(QWidget):
    # 切換信號
    checkedChanged = pyqtSignal(bool)

    def __init__(
            self,
            parent: QWidget,
            text_off: str = '關',
            text_on: str = '開',
            geometry: tuple[int, int, int, int] | None = None,
            move: tuple[int, int] | None = None,
            click: Callable[[], None | bool | Awaitable[None]] = None
    ) -> None:
        super(QWidget, self).__init__(parent)
        # 設置目前按鈕狀態
        self.checked: bool = True
        # 設置關閉背景顏色
        self.bgColor_off: QColor = QColor(213, 213, 213)
        # 設置開啟背景顏色
        self.bgColor_on: QColor = QColor(255, 255, 255)
        # 設置滑塊關閉顏色
        self.sliderColor_off: QColor = QColor(255, 255, 255)
        # 設置滑塊開啟顏色
        self.sliderColor_on: QColor = QColor(39, 119, 248)
        # 設置文字關閉顏色
        self.textColor_off = QColor(255, 255, 255)
        # 設置文字開啟顏色
        self.textColor_on = QColor(39, 119, 248)
        # 設置關閉文字
        self.text_off: str = text_off
        # 設置開啟文字
        self.text_on: str = text_on
        # 設置滑塊距離邊框多少距離
        self.space: int = 3
        # 設置滑塊步進
        self.step: float = 0
        # 設置滑塊開始位置
        self.start_x: int = 0
        # 設置滑塊結束位置
        self.end_x: int = 0
        # 設置滑塊動畫定時器
        self.timer = QTimer(self)
        # 連接動畫定時器方法
        self.timer.timeout.connect(self.update_value)
        if click:
            self.checkedChanged.connect(click)
        if geometry:
            self.setGeometry(*geometry)
        if move:
            self.move(*move)

    def update_value(self) -> None:
        if self.checked:
            if self.start_x < self.end_x:
                self.start_x = self.start_x + self.step
            else:
                self.start_x = self.end_x
                self.timer.stop()
        else:
            if self.start_x > self.end_x:
                self.start_x = self.start_x - self.step
            else:
                self.start_x = self.end_x
                self.timer.stop()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        # 設置畫圖
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 繪製背景
        self.draw_background(painter)
        # 繪製滑塊
        self.draw_slider(painter)
        # 繪製文字
        self.draw_text(painter)
        painter.end()

    def draw_background(self, painter: QPainter) -> None:
        painter.save()

        if self.checked:
            painter.setPen(QColor(39, 119, 248))
        else:
            painter.setPen(Qt.NoPen)
        # 查看點擊狀態 並設置 背景顏色
        if self.checked:
            painter.setBrush(self.bgColor_on)
        else:
            painter.setBrush(self.bgColor_off)
        # 獲取滑塊按鈕大小
        rect = QRect(0, 0, self.width(), self.height())
        # 半径为高度的一半
        radius = int(rect.height() / 2)
        # 圆的宽度为高度
        circle_width = rect.height()

        path = QPainterPath()
        path.moveTo(radius, rect.left())
        path.arcTo(QRectF(rect.left(), rect.top(), circle_width, circle_width), 90, 180)
        path.lineTo(rect.width() - radius, rect.height())
        path.arcTo(QRectF(rect.width() - rect.height(), rect.top(), circle_width, circle_width), 270, 180)
        path.lineTo(radius, rect.top())

        painter.drawPath(path)
        painter.restore()

    def draw_slider(self, painter: QPainter) -> None:
        painter.save()
        painter.setPen(Qt.NoPen)
        if self.checked:
            painter.setBrush(self.sliderColor_on)
        else:
            painter.setBrush(self.sliderColor_off)

        rect = QRect(0, 0, self.width(), self.height())
        slider_width = rect.height() - self.space * 2
        slider_rect = QRect(int(self.start_x + self.space), self.space, slider_width, slider_width)
        painter.drawEllipse(slider_rect)

        painter.restore()

    def draw_text(self, painter: QPainter) -> None:
        painter.save()

        if self.checked:
            painter.setPen(self.textColor_on)
            painter.drawText(0, 0, int(self.width() / 2 + self.space * 2), self.height(), Qt.AlignCenter, self.text_on)
        else:
            painter.setPen(self.textColor_off)
            painter.drawText(
                int(self.width() / 2), 0, int(self.width() / 2 - self.space),
                self.height(), Qt.AlignCenter, self.text_off
            )

        painter.restore()

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.checked = not self.checked
        # 發送點擊信號
        self.checkedChanged.emit(self.checked)

        # 每次移动的步长为宽度的50分之一
        self.step = self.width() / 50
        # 状态切换改变后自动计算终点坐标
        if self.checked:
            self.end_x = self.width() - self.height()
        else:
            self.end_x = 0
        self.timer.start(5)

    def resizeEvent(self, event: QResizeEvent) -> None:
        if self.checked:
            self.end_x = self.width() - self.height()
            self.start_x = self.width() - self.height()


class LineEdit(QLineEdit):
    def __init__(
            self,
            parent: QWidget,
            placeholder_text: str,
            text: str,
            geometry: tuple[int, int, int, int],
            qss: int = 1,
            ico_image: IcoImage | None = None
    ) -> None:
        super().__init__(parent)
        # 設置 佔位符文本
        self.setPlaceholderText(placeholder_text)

        self.setText(text)

        self.setGeometry(*geometry)

        if qss == 1:
            self.setStyleSheet(
                "LineEdit{"
                "background:transparent;"
                "border-width:0;"
                "border-style:outset;"
                "font-size:13px"
                "}")
        elif qss == 2:
            # 設置 搜索窗口 qss
            self.setStyleSheet(
                "LineEdit{"
                "border: 1px;"
                "border-style:none none solid none;"
                "border-bottom-color: rgb(237, 240, 247);"
                "font-size:20px;"
                "background-color: transparent;"
                "}"
            )
        elif qss == 3:
            self.setStyleSheet(
                "LineEdit{"
                "border:1px solid rgb(230, 230, 230);"
                "font-size:18px;"
                "background-color: transparent;"
                "}"
            )
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
        if ico_image is not None:
            self.addAction(AllImage.get_ico(ico_image), QLineEdit.LeadingPosition)

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

