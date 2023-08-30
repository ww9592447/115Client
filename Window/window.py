import inspect
from os.path import exists
from asyncio import create_task, CancelledError, Future
from enum import Enum
from os import popen
from typing import Callable, Awaitable, Generic, TypeVar, Self
from ctypes import WinDLL
from ctypes import c_int
from ctypes import Structure, byref
from multiprocessing import Lock

from PyQt5.Qt import QMouseEvent, QRect, QCursor, Qt, QWidget, QPoint, QEvent, QGraphicsDropShadowEffect,\
    QResizeEvent, QFrame, QLabel, QProgressBar, QSize, pyqtSignal, QFont
from Modules.image import AllImage, Image
from Modules.type import StateData
from Modules.widgets import MyIco, MyPushButton
from Modules.get_data import pybyte, SetData
from MyQlist.MScroolBar import ScrollArea


T = TypeVar('T')


class Direction(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    LEFT_TOP = 4
    LEFT_BOTTOM = 5
    RIGHT_BOTTOM = 6
    RIGHT_TOP = 7
    NONE = 8


class MARGINS(Structure):
    _fields_ = [
        ("cxLeftWidth", c_int),
        ("cxRightWidth", c_int),
        ("cyTopHeight", c_int),
        ("cyBottomHeight", c_int),
    ]


class NFramelessWindow(QFrame):
    # 標題窗口
    title_widget: QWidget | None
    # 內容窗口
    content_widget = QWidget
    # 標題板機
    title_move_drag: bool
    # 標題板機座標
    title_move_drag_position: QPoint | None

    def __init__(self, parent: QWidget = None, title_widget: QWidget = None,):
        super().__init__(parent=parent)
        dwm_api = WinDLL('dwmapi')
        dwm_api.DwmSetWindowAttribute(int(self.winId()), 2, byref(c_int(2)), 4)
        dwm_api.DwmExtendFrameIntoClientArea(int(self.winId()), byref(MARGINS(-1, -1, -1, -1)))
        # 設定內容窗口
        self.content_widget = QWidget(self)
        # 設置標題
        if title_widget:
            self.set_title(title_widget)
        else:
            self.title_widget = None
        # 標題板機
        self.title_move_drag: bool = False
        # 標題板機座標
        self.title_move_drag_position: QPoint | None = None
        self.setWindowFlags(Qt.FramelessWindowHint)

    def set_title(self, title_widget: QWidget, set_size: bool = True) -> None:
        self.title_widget: QWidget = title_widget
        # 設置標題父類
        self.title_widget.setParent(self)
        # 安裝事件管理器
        self.title_widget.installEventFilter(self)
        if set_size:
            self.title_widget.resize(self.width(), self.title_widget.height())
            self.content_widget.setGeometry(
                0, self.title_widget.height(),
                self.width(), self.height() - self.title_widget.height()
            )

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 判斷是否左鍵
        if event.button() == Qt.LeftButton:
            # 判斷點擊範圍是否是在 標題範圍內
            if self.title_widget and self.title_widget.geometry().contains(event.pos()):
                # 標題板機
                self.title_move_drag: bool = True
                # 標題板機座標
                self.title_move_drag_position: QPoint = event.globalPos() - self.pos()

    # 滑鼠鬆開事件
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        # 設定標題板機 False
        self.title_move_drag = False

    # 滑鼠點擊移動事件
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.title_widget and self.title_move_drag:
            self.move(event.globalPos() - self.title_move_drag_position)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        if self.title_widget:
            self.title_widget.resize(self.width(), self.title_widget.height())
            self.content_widget.setGeometry(
                0, self.title_widget.height(), self.width(), self.height() - self.title_widget.height()
            )
        else:
            self.content_widget.resize(self.width(), self.height())


class YFramelessWindow(QWidget):
    # 陰影大小
    padding: int
    # 原始尺寸
    original_size: QRect
    # 窗口是否最大化
    is_maximize: bool
    # 滑鼠方向
    direction: Direction
    # 滑鼠是否按下
    is_left_press_down: bool
    # 移動中滑鼠位置
    drag_position: QPoint
    # 邊框陰影窗口
    shadow_widget: QWidget
    # 陰影效果
    effect_shadow: QGraphicsDropShadowEffect
    # 標題窗口
    title_widget: QWidget | None
    # 標題板機
    title_move_drag: bool
    # 標題板機座標
    title_move_drag_position: QPoint | None
    # 內容窗口
    content_widget = QWidget

    def __init__(self, parent: QWidget = None, title_widget: QWidget = None, padding: int = 13):
        super().__init__(parent)
        # 設定陰影大小
        self.padding: int = padding
        # 初始化窗口原始尺寸
        self.original_size = QRect()
        # 初始化窗口是否最大化
        self.is_maximize: bool = False
        # 初始化滑鼠方向
        self.direction: Direction = Direction.NONE
        # 初始化滑鼠按下
        self.is_left_press_down: bool = False
        # 標題板機
        self.title_move_drag: bool = False
        # 標題板機座標
        self.title_move_drag_position: QPoint | None = None
        # 設定內容窗口
        self.content_widget = QWidget(self)
        # 移動到可以完全顯示陰影
        self.content_widget.move(padding, padding)
        # 安裝事件管理器
        self.content_widget.installEventFilter(self)
        # 設定邊框陰影窗口
        self.shadow_widget: QWidget = QWidget(self)
        # 設定邊框陰影窗口背景空白
        self.shadow_widget.setStyleSheet('background-color:rgb(255,255,255)')
        # 移動到可以完全顯示陰影
        self.shadow_widget.move(padding, padding)
        # 設定陰影效果
        self.effect_shadow: QGraphicsDropShadowEffect = QGraphicsDropShadowEffect(self)
        # 偏移
        self.effect_shadow.setOffset(0, 0)
        # 設定 陰影半徑  模糊顏色
        self.effect_shadow.setBlurRadius(self.padding)
        # 設定 陰影顏色
        self.effect_shadow.setColor(Qt.gray)
        # 套用陰影設定
        self.shadow_widget.setGraphicsEffect(self.effect_shadow)
        self.shadow_widget.lower()
        # 設置標題
        if title_widget:
            self.set_title(title_widget)
        else:
            self.title_widget = None
        # 設定窗口背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 設定無邊框
        self.setWindowFlag(Qt.FramelessWindowHint)
        # 啟用滑鼠追蹤 為了可以拉伸窗口
        self.setMouseTracking(True)

        self.resize(500, 500)

    def set_title(self, title_widget: QWidget) -> None:
        # 設置標題
        self.title_widget: QWidget = title_widget
        # 設置標題父類
        self.title_widget.setParent(self)
        # 移動到可以完全顯示陰影
        self.title_widget.move(self.padding, self.padding)
        # 安裝事件管理器
        self.title_widget.installEventFilter(self)
        self.title_widget.resize(self.shadow_widget.width(), self.title_widget.height())
        self.content_widget.setGeometry(
            self.padding, self.padding + self.title_widget.height(),
            self.shadow_widget.width(), self.shadow_widget.height() - self.title_widget.height()
        )

    def eventFilter(self, watched: QWidget, event: QEvent) -> bool:
        # 判斷是否進入內容窗口內
        if event.type() == 10:
            # 如果進入 dir 設定成預設
            self.direction: Direction = Direction.NONE
            # 滑鼠設定成預設
            self.setCursor(QCursor(Qt.ArrowCursor))
        return super().eventFilter(watched, event)

    # 設置滑鼠光標形狀
    def set_cursor(self, global_point: QPoint, tl: QPoint, rb: QPoint) -> None:
        x = global_point.x()
        y = global_point.y()
        # 判斷是否右下角
        if rb.x() >= x >= rb.x() - self.padding and rb.y() >= y >= rb.y() - self.padding:
            self.direction: Direction = Direction.RIGHT_BOTTOM
            self.setCursor(QCursor(Qt.SizeFDiagCursor))
        # 判斷是否左下角
        elif tl.x() + self.padding >= x >= tl.x() and rb.y() >= y >= rb.y() - self.padding:
            self.direction: Direction = Direction.LEFT_BOTTOM
            self.setCursor(QCursor(Qt.SizeBDiagCursor))
        # 判斷是否左上角
        elif tl.x() + self.padding >= x >= tl.x() and tl.y() + self.padding >= y >= tl.y() + 13:
            self.direction: Direction = Direction.LEFT_TOP
            self.setCursor(QCursor(Qt.SizeFDiagCursor))
        # 判斷是右上角
        elif rb.x() >= x >= rb.x() - self.padding and tl.y() + self.padding >= y >= tl.y() + 13:
            self.direction: Direction = Direction.RIGHT_TOP
            self.setCursor(QCursor(Qt.SizeBDiagCursor))
        # 判斷是否上邊
        elif tl.y() + self.padding >= y >= tl.y():
            self.direction: Direction = Direction.UP
            self.setCursor(QCursor(Qt.SizeVerCursor))
        # 判斷是否左邊
        elif tl.x() + self.padding >= x >= tl.x():
            self.direction: Direction = Direction.LEFT
            self.setCursor(QCursor(Qt.SizeHorCursor))
        # 判斷是否右邊
        elif rb.x() >= x >= rb.x() - self.padding:
            self.direction: Direction = Direction.RIGHT
            self.setCursor(QCursor(Qt.SizeHorCursor))
        # 判斷是否下邊
        elif rb.y() >= y >= rb.y() - self.padding:
            self.direction: Direction = Direction.DOWN
            self.setCursor(QCursor(Qt.SizeVerCursor))
        # 如果都不是恢復默認
        else:
            # 默认
            self.direction: Direction = Direction.NONE
            self.setCursor(QCursor(Qt.ArrowCursor))

    # 最大化
    def show_maximized(self) -> None:
        # 紀錄最大化前原始尺寸
        self.original_size.setRect(*self.geometry().getRect())
        # 狀態設定成最大化
        self.is_maximize = True
        # 獲取螢幕最大大小
        size = self.screen().availableGeometry()
        # 計算移除陰影後的大小
        size = QRect(
            -self.padding + size.x(),
            -self.padding, size.width() + self.padding * 2, size.height() + self.padding * 2
        )
        # 設定位置大小
        self.setGeometry(size)
        # 取消滑鼠追蹤
        self.setMouseTracking(False)
        # 傳遞消息
        self.window_change(True)
        # 取消陰影大小
        self.effect_shadow.setBlurRadius(0)
        # 套用陰影設定
        self.shadow_widget.setGraphicsEffect(self.effect_shadow)

    # 恢復原本窗口大小
    def show_normal(self):
        # 狀態設定成原本大小
        self.is_maximize = False
        # 還原成原本窗口大小
        self.setGeometry(self.original_size)
        # 恢復滑鼠追蹤
        self.setMouseTracking(True)
        # 傳遞消息
        self.window_change(False)
        # 設定 陰影半徑  模糊距離
        self.effect_shadow.setBlurRadius(self.padding)
        # 套用陰影設定
        self.shadow_widget.setGraphicsEffect(self.effect_shadow)

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 判斷是否左鍵
        if event.button() == Qt.LeftButton:
            # 判斷點擊範圍是否是在 標題範圍內
            if self.title_widget and self.title_widget.geometry().contains(event.pos()):
                # 標題板機
                self.title_move_drag: bool = True
                # 標題板機座標
                self.title_move_drag_position: QPoint = event.globalPos() - self.pos()
                return
            # 設定可以移動窗口
            self.is_left_press_down = True
            # 設定移動滑鼠位置
            self.drag_position = event.globalPos()

    # 滑鼠鬆開事件
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        # 設定不能移動窗口
        self.is_left_press_down = False
        # 滑鼠樣式初始化
        self.direction = Direction.NONE
        # 設定標題板機 False
        self.title_move_drag = False

    # 滑鼠點擊移動事件
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # 獲取滑鼠在全局的座標
        global_point = event.globalPos()
        # 獲取原始尺寸全局左上角的座標
        tl = self.mapToGlobal(self.rect().topLeft())
        # 獲取原始尺寸全局右下角的座標
        rb = self.mapToGlobal(self.rect().bottomRight())
        # 獲取原始尺寸矩形全局大小
        rectangle = QRect(tl, rb)
        # 判斷滑鼠移動是否按下 and 是否移動標題
        if not self.is_left_press_down and not self.title_move_drag:
            self.set_cursor(global_point, tl, rb)
        # 是否需要移動標題
        elif self.title_move_drag:
            # 判斷是否取消滑鼠追蹤
            if not self.hasMouseTracking():
                # 重新啟用滑鼠追蹤
                self.setMouseTracking(True)
            # 判斷是否窗口最大化
            # 如果最大化則還原大小 順便移動到滑鼠位置
            if self.is_maximize and self.original_size:
                # 獲取全局 y座標移動 相差的值
                y = event.globalPos().y() - self.title_move_drag_position.y()
                # 重新設定紀錄原本大小 的左上角座標
                self.original_size.moveTo(int(event.globalPos().x() - self.original_size.width() / 2), y)
                # 獲取目前螢幕的可用大小
                size = self.screen().availableGeometry()
                # 獲取右側的座標
                right = size.x() + size.width()
                # 查看是否小於左側座標
                if self.original_size.x() - self.padding < size.x():
                    # 如果小於左側座標 則移動到跟左側座標一樣的位置
                    self.original_size.moveLeft(-self.padding + size.x())
                # 查看是否大於右側座標
                elif self.original_size.x() + self.original_size.width() + self.padding > right:
                    # 如果大於右側座標 則右側底部移動到跟右側座標一樣的位置
                    self.original_size.moveLeft(right - self.original_size.width() + self.padding)
                # 調用還原大小函數
                self.show_normal()
                # 重新設定標題座標
                self.title_move_drag_position = event.globalPos() - self.pos()
            else:
                # 標題跟隨滑鼠拖曳
                self.move(event.globalPos() - self.title_move_drag_position)
        else:
            x = global_point.x() - self.drag_position.x()
            y = global_point.y() - self.drag_position.y()
            # 右下
            if self.direction == Direction.RIGHT_BOTTOM:
                rectangle.setWidth(rectangle.width() + x)
                rectangle.setHeight(rectangle.height() + y)
            # 左下
            elif self.direction == Direction.LEFT_BOTTOM:
                rectangle.setX(rectangle.x() + x)
                rectangle.setHeight(rectangle.height() + y)
            # 左上
            elif self.direction == Direction.LEFT_TOP:
                rectangle.setX(rectangle.x() + x)
                rectangle.setY(rectangle.y() + y)
            # 右上
            elif self.direction == Direction.RIGHT_TOP:
                rectangle.setWidth(rectangle.width() + x)
                rectangle.setY(rectangle.y() + y)
            # 上邊
            elif self.direction == Direction.UP:
                rectangle.setY(rectangle.y() + y)
            # 左邊
            elif self.direction == Direction.LEFT:
                rectangle.setX(rectangle.x() + x)
            # 右邊
            elif self.direction == Direction.RIGHT:
                rectangle.setWidth(rectangle.width() + x)
            # 下邊
            elif self.direction == Direction.DOWN:
                rectangle.setHeight(rectangle.height() + y)
            self.setGeometry(rectangle)
            self.drag_position = event.globalPos()

    # 左鍵雙擊
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if self.title_widget and self.title_widget.geometry().contains(event.pos()):
            # 查看窗口是否最大化
            if self.is_maximize:
                # 如果最大化 就還原原本大小
                self.show_normal()
            else:
                # 沒有最大化 就最大化
                self.show_maximized()

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.shadow_widget.resize(self.width() - self.padding * 2, self.height() - self.padding * 2)
        if self.title_widget:
            self.title_widget.resize(self.shadow_widget.width(), self.title_widget.height())
            self.content_widget.setGeometry(
                self.padding, self.padding + self.title_widget.height(),
                self.shadow_widget.width(), self.shadow_widget.height() - self.title_widget.height()
            )
        else:
            self.content_widget.resize(self.shadow_widget.width(), self.shadow_widget.height())

    # 獲得窗口最大化 還原 事件
    def window_change(self, value: bool) -> None:
        pass


class MText(QFrame, Generic[T]):
    end = pyqtSignal(QWidget)
    toggle = pyqtSignal(QWidget, bool)

    def __init__(
            self,
            state: dict[str, T],
            uuid: str,
            data: T,
            queue_list: list[Self, ...] | None = None,
            transmission_list: list[Self, ...] | None = None,
            all_text: list[Self, ...] | None = None,
            lock: Lock = None,
            parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        # 共享數據資料
        self.state: dict[str, T] = state
        # 數據鎖
        self.lock: Lock | None = lock
        # 所有qtest 列表
        self.all_text: list[QWidget, ...] | None = all_text
        # 紀錄id
        self.uuid: str = uuid
        # 排隊列表
        self.queue_list: list[QWidget, ...] | None = queue_list
        # 正在傳輸中列表
        self.transmission_list: list[QWidget, ...] | None = transmission_list
        # 任務
        self.task: Future | None = None
        # 是否能夠取消任務
        self.task_cancel: bool = True
        # 檔案名稱
        self.name: str = data['name']
        # 檔案圖標
        self.name_ico: QLabel = QLabel(self)
        # 檔案名稱
        self.file_name: QLabel = QLabel(data['name'], self)
        # 操作按鈕容器
        self.ico_widget: QWidget = QWidget(self)
        # 設定操作按鈕容器背景空白
        self.ico_widget.setStyleSheet('background-color:rgb(255, 255, 255)')
        # 設置傳輸速度 or 狀態文字
        self.progressText: QLabel = QLabel(self.ico_widget)
        # 設文字顏色
        self.progressText.setStyleSheet('color:rgba(50, 50, 50, 150)')
        # 操作按鈕容器置頂
        self.ico_widget.raise_()

        y = lambda height: int((56 - height) / 2)

        # 設置 暫停按鈕
        self.set_pause: MyIco = MyIco(
            self.ico_widget,
            Image.BLACK_PAUSE,
            Image.BLUE_PAUSE,
            state=True,
            coordinate=(219, y(10), 8, 10), click=self.get_event('pause')
        )

        # 設置 恢復按鈕
        self.set_restore: MyIco = MyIco(
            self.ico_widget,
            Image.BLACK_RESTORE_DOWNLOAD,
            Image.BLUE_RESTORE_DOWNLOAD,
            state=True,
            coordinate=(219, y(11), 8, 11), click=self.get_event('restore')
        )

        # 設置 取消按鈕
        self.set_cancel: MyIco = MyIco(
            self.ico_widget,
            Image.BLACK_CLOSE,
            Image.BLUE_CLOSE,
            state=True,
            coordinate=(264, y(10), 9, 10), click=self.get_event('cancel')
        )

        MyIco(
            self.ico_widget,
            Image.BLACK_OPEN_FOLDER,
            Image.BLUE_OPEN_FOLDER,
            state=True,
            coordinate=(308, y(13), 14, 13), click=self.get_event('open')
        )
        self.set_restore.hide()
        self.setStyleSheet(
            'MText{border-style:solid; border-bottom-width:1px; border-color:rgba(200, 200, 200, 125)'
            '; background-color:rgb(255, 255, 255)}'
        )

    # 判斷函數是否是異步並返回相應調用方式
    def get_event(self, name: str) -> Callable[[], Awaitable[None] | None]:
        event = getattr(self, name)
        if inspect.iscoroutinefunction(event):
            return lambda: create_task(event())
        else:
            return event

    def set_state(self, data: StateData, result: str) -> None:
        if data in (StateData.TEXT, StateData.PAUSE):
            self.progressText.setText(result)
        elif data == StateData.COMPLETE:
            self.end.emit(self)
        elif data == StateData.ERROR:
            # 顯示網路錯誤
            self.progressText.setText(result)
            # Text 轉成暫停
            self.set_switch(False)

    # 暫停
    async def pause(self) -> None:
        self.set_switch(False)
        if self.task and not self.task.done():
            self.progressText.setText('等待暫停中...')
            self.set_button(False)
            if 'state' in self.state[self.uuid]:
                with SetData(self.state, self.uuid, self.lock) as state:
                    state.update({'state': StateData.PAUSE})

            if self.task_cancel:
                self.task.cancel()
            try:
                await self.task
            except CancelledError:
                pass
            self.set_button(True)
        self.progressText.setText('暫停中')

    # 關閉
    async def cancel(self) -> None:
        self.set_switch(False)
        if self.task and not self.task.done():
            self.progressText.setText('等待關閉中...')
            self.set_button(False)
            if 'state' in self.state[self.uuid]:
                with SetData(self.state, self.uuid, self.lock) as state:
                    state.update({'state': StateData.CANCEL})
            if self.task_cancel:
                self.task.cancel()
            try:
                await self.task
            except CancelledError:
                pass
        self.end.emit(self)

    # 開啟
    def open(self) -> None:
        if exists(self.path):
            popen(f'explorer.exe /select, {self.path}')

    # 設定暫停開始按鈕狀態
    def set_switch(self, _bool: bool) -> None:
        # 開始
        if _bool:
            self.progressText.setText('')
            self.set_pause.show()
            self.set_restore.hide()
        # 暫停
        else:
            self.set_pause.hide()
            self.set_restore.show()
        self.toggle.emit(self, _bool)

    # 設定按鈕是否可用
    def set_button(self, value: bool) -> None:
        self.set_restore.setEnabled(value)
        self.set_restore.setEnabled(value)

    # 恢復
    def restore(self) -> None:
        self.set_switch(True)
        index = -1
        _index = self.all_text.index(self)
        for wait in self.queue_list:
            if _index < self.all_text.index(wait):
                index = self.queue_list.index(wait)
                break
        if index == -1:
            self.queue_list.append(self)
        else:
            self.queue_list.insert(index, self)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.ico_widget.setGeometry(self.width() - 360, 0, 360, 55)


class MTextA(MText[T]):
    def __init__(
            self,
            state: dict[str, T],
            data: T,
            uuid: str,
            queue_list: list[MText, ...] | None = None,
            transmission_list: list[MText, ...] | None = None,
            all_text: list[MText, ...] | None = None,
            lock: Lock = None,
            parent: QWidget | None = None
            ) -> None:
        super().__init__(state, uuid, data, queue_list, transmission_list, all_text, lock, parent)
        # 檔案大小
        self.length: int = data['file_size']
        self.name_ico.setGeometry(15, 15, 30, 30)
        self.name_ico.setPixmap(AllImage.get_image(data["ico"]))
        self.file_name.setFont(QFont("細明體", 9))
        self.file_name.move(55, 16)

        # 設置檔案大小
        self.file_size: QLabel = QLabel(f'{pybyte(data["all_size"])}/{pybyte(data["file_size"])}', self)
        self.file_size.setFont(QFont("細明體", 9))
        self.file_size.move(55, 37)
        self.file_size.setFixedWidth(120)
        self.file_size.setStyleSheet('color:rgba(50, 50, 50, 150)')
        # 設置進度條
        self.progressBar = QProgressBar(self.ico_widget)
        self.progressBar.setMaximum(100)
        self.progressBar.setGeometry(0, 14, 152, 12)
        self.progressBar.setTextVisible(False)
        if data['all_size'] != 0:
            self.progressBar.setValue(int(data['all_size'] / data['file_size'] * 100))
        self.progressBar.setStyleSheet('QProgressBar{border: 0px; background:rgb(200, 100, 200) ;'
                                       'background-color: rgb(229, 230, 234);color:rgb(60, 104, 137)}'
                                       'QProgressBar:chunk {background-color: rgb(6, 168, 255)}'
                                       )
        self.progressText.setFont(QFont("細明體", 11))
        self.progressText.setGeometry(0, 32, 152, 14)


class MTextB(MText[T]):
    def __init__(
            self,
            state: dict[str, T],
            data: T,
            uuid: str,
            queue_list: list[MText, ...] | None = None,
            transmission_list: list[MText, ...] | None = None,
            all_text: list[MText, ...] | None = None,
            lock: Lock = None,
            parent: QWidget | None = None
            ) -> None:
        super().__init__(state, uuid, data, queue_list, transmission_list, all_text, lock, parent)
        self.name_ico.setGeometry(15, 15, 30, 30)
        self.name_ico.setPixmap(AllImage.get_image(data['ico']))
        self.file_name.setFont(QFont("細明體", 12))
        self.file_name.adjustSize()
        self.file_name.move(55, int((56 - self.file_name.height()) / 2))
        self.progressText.setFont(QFont("細明體", 12))
        self.progressText.setGeometry(0, 20, 160, 16)


class MList(QFrame, Generic[T]):
    def __init__(
            self,
            state: dict[str, T],
            lock: Lock, wait: list[str, ...],
            wait_lock: Lock,
            set_index: Callable[[int], None],
            parent: QWidget
    ) -> None:
        super().__init__(parent)
        # 共用數據
        self.state: dict[str, T] = state
        # 數據鎖
        self.lock: Lock = lock
        # 準備下載列表
        self.wait: list[str, ...] = wait
        # 準備下載列表鎖
        self.wait_lock: Lock = wait_lock
        # 顯示所有數量
        self.set_index: Callable[[int], None] = set_index
        # 所有text
        self.all_text: list[MText, ...] = []
        # 排隊列表
        self.queue_list: list[MText, ...] = []
        # 正在傳輸列表
        self.transmission_list: list[MText, ...] = []
        # 暫停列表
        self.pause_list: list[MText, ...] = []
        # 全部傳輸總量
        self.all_size: int = 0
        # 目前傳輸大小
        self.transmission_size: int = 0
        # 設置 總進度條 容器
        self.progress_widget: QWidget = QWidget(self)
        self.progress_widget.setObjectName('progress_widget')
        self.progress_widget.setStyleSheet(
            '#progress_widget{border-style:solid; border-bottom-width:1px;'
            'border-color:rgba(200, 200, 200, 125)}'
        )
        # 預設 隱藏 總進度條容器
        self.progress_widget.hide()
        # 設置 下載總進度 文字
        self.name: QLabel = QLabel(self.progress_widget)
        # 設置文字
        self.name.setText('下載總進度')
        # 設置文字顏色
        self.name.setStyleSheet('color:rgb(60, 104, 137)')
        # 設置文字位置大小
        self.name.setGeometry(14, 12, 60, 12)
        # 設置總進度條
        self.progressbar = QProgressBar(self.progress_widget)
        # 設置總進度條QSS設置
        self.progressbar.setStyleSheet('QProgressBar{border: 0px; background:rgb(200, 100, 200) ;'
                                       'background-color: rgb(229, 230, 234);color:rgb(60, 104, 137)}'
                                       'QProgressBar::chunk {background-color: rgb(6, 168, 255)}'
                                       )
        # 設置總進度上限
        self.progressbar.setMaximum(100)
        # 設置進度條%數文字置中
        self.progressbar.setAlignment(Qt.AlignCenter)
        # 設置按鈕容器
        self.buttons: QLabel = QLabel(self.progress_widget)
        # 設置全部開始按鈕
        self.start_button: MyPushButton = MyPushButton(
            self.buttons, '全部開始', (0, 0, 80, 24), qss=2, font_size=12, click=self.all_start
        )
        # 默認全部開始按鈕關閉
        self.start_button.setEnabled(False)
        # 設置全部暫停按鈕
        self.pause_button: MyPushButton = MyPushButton(
            self.buttons, '全部暫停', (88, 0, 80, 24), qss=2, font_size=12, click=self.all_pause
        )
        # 設置全部取消按鈕
        MyPushButton(self.buttons, '全部取消', (176, 0, 80, 24), qss=2, click=self.all_cancel, font_size=12)
        # 設置滾動區
        self.scroll_area: ScrollArea = ScrollArea(self)
        # 獲取滾動內容窗口
        self.scroll_contents = self.scroll_area.scroll_contents
        # 關閉橫滾動條
        self.scroll_area.set_horizontal(False)
        # 設置背景空白 左邊邊框
        self.setStyleSheet(
            'MList{background-color:rgb(255, 255, 255);border-style:solid;'
            'border-left-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )

    # 全部開始
    def all_start(self) -> None:
        for text in self.pause_list.copy():
            text.set_restore.left_click.emit(text)

    # 全部暫停
    def all_pause(self) -> None:
        for text in self.transmission_list.copy() + self.queue_list.copy():
            text.set_pause.left_click.emit(text)

    # 全部取消
    def all_cancel(self) -> None:
        for text in self.all_text.copy():
            text.set_cancel.left_click.emit(text)

    # 設置目前傳輸大小
    def set_transmission_size(self, size: int) -> None:
        self.transmission_size += size
        if self.progressbar.value() != (size := int(self.transmission_size / self.all_size * 100)):
            self.progressbar.setValue(size)
    
    # text切換狀態回調
    def toggle(self, text: QWidget, value: bool) -> None:
        # 如果是 恢復下載 and qtxt 在暫停列表內 則刪除 暫停列表內的 text
        if value and text in self.pause_list:
            # 刪除 暫停列表內的 text
            self.pause_list.remove(text)
        # 如果是暫停
        if not value:
            # 查看是否在正在傳輸列表中
            if text in self.transmission_list:
                # 刪除 傳輸列表內的 text
                self.transmission_list.remove(text)
            # 查看是否在等待列表中
            elif text in self.queue_list:
                # 刪除 等待列表內的 text
                self.queue_list.remove(text)
            # 把 text 加入暫停列表
            self.pause_list.append(text)
        # 設定進度條按鈕狀態
        self.set_button(value)

    # 設置進度條按鈕狀態
    def set_button(self, value: bool) -> None:
        if not self.start_button.isEnabled() and self.pause_list and not value:
            self.start_button.setEnabled(True)
        elif self.start_button.isEnabled() and not self.pause_list and not self.queue_list:
            self.start_button.setEnabled(False)
        if not self.pause_button.isEnabled() and self.transmission_list and value:
            self.pause_button.setEnabled(True)
        elif self.pause_button.isEnabled() and not self.transmission_list and not self.queue_list:
            self.pause_button.setEnabled(False)

    def _add(self, data: T, uuid: str, text: QWidget, value: bool) -> None:
        with self.lock:
            self.state.update({uuid: data})
        if 'file_size' in data:
            # 設置全部下載總量
            self.all_size += data['file_size']
            # 查看目前傳輸是否 已有傳輸
            if 'all_size' in data and data['all_size']:
                # 重新設置進度條
                self.set_transmission_size(data['all_size'])
        count = len(self.all_text)
        text.end.connect(self.end)
        # 連接 text 切換信號
        text.toggle.connect(self.toggle)
        text.setGeometry(0, count * 56, self.width() - 2, 56)
        text.show()
        self.scroll_contents.setGeometry(0, 0, self.width() - 2, (count + 1) * 56)
        self.all_text.append(text)
        if value:
            self.queue_list.append(text)
        else:
            text.set_switch(False)
        self.set_index(count + 1)
        # 查看進度條容器是否隱藏  如果隱藏則顯示
        if not self.progress_widget.isVisible():
            # 顯示進度條容器
            self.progress_widget.show()
            # 重新設定大小布局
            self.resize(self.size() - QSize(1, 1))

    # 關閉事件
    def end(self, text: MText) -> None:
        with self.lock:
            state = self.state[text.uuid].copy()
        if 'state' in state:
            if state['state'] == StateData.CANCEL:
                self.cancel(text, state)
            elif state['state'] == StateData.COMPLETE:
                self.complete(text, state)
        index = self.all_text.index(text)
        self.all_text.remove(text)
        for i in range(index, len(self.all_text)):
            self.all_text[i].setGeometry(0, i * 56, self.width(), 56)
        self.scroll_contents.setGeometry(0, 0, self.width() - 2, len(self.all_text) * 56)
        if text in self.transmission_list:
            self.transmission_list.remove(text)
        elif text in self.queue_list:
            self.queue_list.remove(text)
        self.set_index(len(self.all_text))
        text.setParent(None)
        text.deleteLater()

        # 查看 所有text 是否還有
        if self.all_text:
            # 如果還有 重新設置 進度條按鈕 狀態
            self.set_button(True)
        # 如果 text 沒有 則初始化 內容
        else:
            # 所有傳輸大小歸0
            self.all_size = 0
            # 目前傳輸大小歸0
            self.transmission_size = 0
            # 進度條歸0
            self.progressbar.setValue(0)
            # 進度條容器隱藏
            self.progress_widget.hide()
            # 全部開始按鈕初始化
            self.start_button.setEnabled(False)
            # 全部暫停按鈕初始化
            self.pause_button.setEnabled(True)
            # 重新設定大小布局
            self.resize(self.size() - QSize(1, 1))

        with self.lock:
            del self.state[text.uuid]

    # 完成任務回調
    def complete(self, text: QWidget, state: dict[str, T]) -> None:
        pass

    # 關閉任務回調
    def cancel(self, text: QWidget, state: dict[str, T]) -> None:
        pass

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        y = 35 if self.all_text else 0
        self.scroll_area.setGeometry(0, y, self.width(), self.height() - y)
        self.scroll_contents.setGeometry(0, 0, self.width() - 2, self.scroll_contents.height())
        self.progress_widget.resize(self.width(), 35)
        self.buttons.setGeometry(self.width() - 290, 5, 256, 24)
        self.progressbar.setGeometry(88, 10, self.width() - 459, 14)
        for text in self.all_text:
            text.setGeometry(0, text.y(), self.width() - 2, 56)



if __name__ == '__main__':
    import sys
    from PyQt5.Qt import QWidget, QApplication
    app = QApplication(sys.argv)
    w = NFramelessWindow(None)
    w.show()
    sys.exit(app.exec_())