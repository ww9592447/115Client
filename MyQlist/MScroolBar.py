from typing import Callable

from PyQt5.Qt import QFrame, QCursor, QApplication, Qt, QPushButton, QResizeEvent, QMouseEvent,\
    QPainter, QPainterPath, QColor, QObject, QRect, QWidget, QEvent, QWheelEvent


# 滾動區
class ScrollArea(QFrame):
    # scroll_size=滾動條大小 single_step=箭頭步進距離 interval=滾動條離邊框距離 arrow=是否顯示箭頭
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
        super().__init__(parent=parent)
        # 滾動條大小
        self.scroll_size: int = scroll_size
        # 滾動條箭頭移動距離
        self.single_step: int = single_step
        # 滾條條背景點擊移動距離
        self.page_step: int = page_step
        # 內容容器  可視窗口 為了防止擋到邊框 還有滾動條
        if visual_contents:
            # 設置 self 成為 內容容器 可視窗口 的父類
            visual_contents.setParent(self)
            self.visual_contents = visual_contents
        else:
            self.visual_contents = QFrame(self)
        self.visual_contents.move(1, 1)
        self.visual_contents.show()
        # 設置內容窗口
        if scroll_contents:
            # 設置 self.visual_contents 成為 內容窗口 的父類
            scroll_contents.setParent(self.visual_contents)
            self.scroll_contents = scroll_contents
        else:
            self.scroll_contents = QFrame(self.visual_contents)
        # 安裝事件過濾
        self.scroll_contents.installEventFilter(self)
        # 設置直滾動條容器
        self.vertical_contents: ScrollContainer = ScrollContainer(self, 1, single_step, interval, arrow)
        # 設置橫滾動條容器
        self.horizontal_contents: ScrollContainer = ScrollContainer(self, 2, single_step, interval, arrow)

    # 添加新的內容窗口
    def set_widget(self, scroll_contents: QFrame) -> None:
        # 查看是否有舊的內窗口
        if self.scroll_contents:
            # 如果有則隱藏以便下次調用
            self.scroll_contents.hide()
            # 解除事件過濾器
            self.scroll_contents.removeEventFilter(self)
        # 設置 self.visual_contents 成為 內容窗口 的父類
        scroll_contents.setParent(self.visual_contents)
        # 設置內容窗口
        self.scroll_contents = scroll_contents
        # 安裝事件過濾
        self.scroll_contents.installEventFilter(self)
        # 內容窗口顯示
        self.scroll_contents.show()

    # 手動設置直滾動條是否能夠顯示
    def set_vertical(self, status: bool) -> None:
        # 設置垂直滾動條狀態
        self.vertical_contents.status = status
        # 重新設置滾動條相關數據
        self.set_scroll()

    # 手動設置橫滾動條是否能夠顯示
    def set_horizontal(self, status: bool) -> None:
        # 設置橫滾動條狀態
        self.horizontal_contents.status = status
        # 重新設置滾動條相關數據
        self.set_scroll()

    # 調整內容容器位置  orientation 滾動條方向 direction 滾動條箭頭方向 move 移動數值
    def set_value(self, orientation: int, direction: bool, move: int) -> None:
        # 獲取內容容器yx座標
        yx = getattr(self.scroll_contents, 'y' if orientation == 1 else 'x')
        # 獲取內容容器相反yx座標
        _yx = getattr(self.scroll_contents, 'x' if orientation == 1 else 'y')
        # 獲取滾動條上限
        limit = self.vertical_contents.limit if orientation == 1 else self.horizontal_contents.limit
        # 獲取滾動條步進距離
        scroll_jump = self.vertical_contents.scroll_jump if orientation == 1 else self.horizontal_contents.scroll_jump
        # 獲取滾動條滑塊
        slider = self.vertical_contents.slider if orientation == 1 else self.horizontal_contents.slider
        # 獲取滾動條是否可動
        isvisible = self.vertical_contents.limit > 0 if orientation == 1 else self.horizontal_contents.limit > 0
        # 判斷內容窗口是否存在 and 滾動條是否顯示
        if self.scroll_contents and isvisible:
            # 判斷滾動方向  True 往上移動  False 往下移動
            if direction:
                # yx越靠近0是往最上面移動
                # 判斷 滾動後 yx 是否是大於0
                if (_move := yx() + move) > 0:
                    # 大於0就 數值改成0
                    _move = 0
            else:
                # 負值 yx越小是往下面移動
                # 判斷 滾動後 yx 是否是小於滾動條上限
                if (_move := yx() - move) < -limit:
                    # 小於滾動條上限 設置成滾動條上限
                    _move = -limit
            # 獲取內容窗口移動數據
            _move = (_yx(), _move) if orientation == 1 else (_move, _yx())
            # 設定內容窗口移動
            self.scroll_contents_move(*_move)
            # 判斷步進距離是否不等於0
            if scroll_jump != 0:
                # 獲取滑塊移動數據
                _move = (0, -int(yx() / scroll_jump)) if orientation == 1 else (-int(yx() / scroll_jump), 0)
                # 設定滑塊移動
                slider.move(*_move)

    # 滾輪事件
    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.scroll_contents:
            if QApplication.keyboardModifiers() == Qt.ShiftModifier and self.horizontal_contents.limit > 0:
                if event.angleDelta().y() > 0:
                    self.set_value(2, True, self.page_step)
                else:
                    self.set_value(2, False, self.page_step)
            elif self.scroll_contents and self.vertical_contents.limit > 0:
                if event.angleDelta().y() > 0:
                    self.set_value(1, True, self.page_step)
                else:
                    self.set_value(1, False, self.page_step)

    # 設置滾動條相關數據
    def set_scroll(self) -> None:
        if self.scroll_contents:
            # 獲取 橫滾動條是否顯示
            width = (_width := (self.width() - 2) - self.scroll_contents.width()) < 0
            # 獲取 直滾動條是否顯示
            height = (_height := (self.height() - 2) - self.scroll_contents.height()) < 0
            # 如果 橫滾動條顯示進入
            if width and not height and self.horizontal_contents.status:
                # (直可視範圍 - 直容器) - 橫滾動條 獲取 是否還有空間 如果沒有則顯示 直滾動條
                height = _height - self.scroll_size < 0
            # 如果 直滾動條顯示進入
            elif height and not width and self.vertical_contents.status:
                # (橫視範圍 - 橫容器) - 直滾動條 獲取 是否還有空間 如果沒有則顯示 橫滾動條
                width = _width - self.scroll_size < 0
            # 判斷是否主動隱藏直滑動條
            if not self.vertical_contents.status:
                height = False
            # 判斷是否主動隱藏橫滑動條
            if not self.horizontal_contents.status:
                width = False
            # 判斷是否需要顯示 直滾動條
            self.vertical_contents.show() if height else self.vertical_contents.hide()

            # 判斷是否需要顯示 橫滾動條
            self.horizontal_contents.show() if width else self.horizontal_contents.hide()
            # 設定 容器背景 可視窗口 大小
            self.visual_contents.resize(
                self.width() - 2 - (self.scroll_size if height else 0),
                self.height() - 2 - (self.scroll_size if width else 0)
            )
            # 設定 直滾動條 大小
            self.vertical_contents.setGeometry(
                self.width() - (self.scroll_size + 1), 1, self.scroll_size,
                self.height() - 1 - (self.scroll_size if height and width else 0)
            )
            # 設定 橫滾動條 大小
            self.horizontal_contents.setGeometry(
                1, self.height() - (self.scroll_size + 1),
                self.width() - 1 - (self.scroll_size if height and width else 0),
                self.scroll_size
            )

            # 計算內容窗口底部 距離可視窗口 是否有還有多於距離 有就移動到底
            self.set_distance()

            # 獲取直滑塊大小 設定步進距離
            vertical_slider_height = self.vertical_contents.slider_size
            # 獲取橫滑塊大小
            horizontal_width = self.horizontal_contents.slider_size

            y = 0
            if self.vertical_contents.scroll_jump != 0:
                y = int(self.vertical_contents.value() / self.vertical_contents.scroll_jump)
            # 設置直滑塊大小
            self.vertical_contents.slider.setGeometry(0, y, self.scroll_size, vertical_slider_height)

            x = 0
            if self.horizontal_contents.scroll_jump != 0:
                x = int(self.horizontal_contents.value() / self.horizontal_contents.scroll_jump)
            # 設置橫滑塊大小
            self.horizontal_contents.slider.setGeometry(x, 0, horizontal_width, self.scroll_size)

    # 獲取內容窗口移動距離
    def scroll_contents_by(self, dx: int, dy: int) -> None:
        pass

    # 內容窗口大小變化回調
    def scroll_contents_size_by(self) -> None:
        pass

    # 設定內容窗口移動
    def scroll_contents_move(self, x: int, y: int) -> None:
        # 獲取內容窗口 x 移動距離
        dx = x - self.scroll_contents.x()
        # 獲取內容窗口 y 移動距離
        dy = y - self.scroll_contents.y()
        # 移動內容窗口
        self.scroll_contents.move(x, y)
        # 傳遞 移動距離給函數
        self.scroll_contents_by(dx, dy)

    # 當內容窗口有變化 刷新 內容窗口 相關數據
    def refresh(self) -> None:
        # 獲取目前內容窗口y座標
        y = self.scroll_contents.y()
        # 獲取目前內容窗口x座標
        x = self.scroll_contents.x()
        # 判斷 y座標是否被移動過
        if self.scroll_contents.y() != 0:
            # (內容窗口y+內容窗口長度) = 目前內容窗口 y底部位置
            # 內容窗口 底部位置 - 內容容器長度 如果小於0 則代表需要重新設定內容窗口y座標
            if (dy := self.scroll_contents.y() + self.scroll_contents.height() - self.visual_contents.height()) <= 0:
                # 0是y座標最頂部位置
                # 判斷 內容窗口y + 移動座標 是否大於0 代表超過移動極限
                if (y := self.scroll_contents.y() + -dy) > 0:
                    # 設置移動座標y = 0
                    y = 0
        # 判斷 x座標是否被移動過
        if self.scroll_contents.x() != 0:
            # (內容窗口X+內容窗口長度) = 目前內容窗口 X底部位置
            # 內容窗口 底部位置 - 內容容器長度 如果小於0 則代表需要重新設定內容窗口X座標
            if (dx := self.scroll_contents.x() + self.scroll_contents.width() - self.visual_contents.width()) <= 0:
                # 0是x座標最頂部位置
                # 判斷 內容窗口x + 移動座標 是否大於0 代表超過移動極限
                if (x := self.scroll_contents.x() + -dx) > 0:
                    # 設置移動座標x = 0
                    x = 0
        # 設定內容窗口新座標
        self.scroll_contents_move(x, y)
        # 重新設置滾動條相關數據
        self.set_scroll()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # 內容窗口 有調整大小 事件 進入  窗口大小有變化自動調整內容窗口座標  自動調整滑塊數據
        if event.type() == 14:
            # 刷新滾動條相關資料
            self.refresh()
            self.scroll_contents_size_by()
        return super().eventFilter(watched, event)

    # 計算內容窗口底部 距離可視窗口 是否有還有多於距離  有就移動到底
    def set_distance(self) -> None:
        # 當滾動窗口超過 y高度 內容窗口往下移動
        if -self.scroll_contents.y() > 0:
            bottom = (self.scroll_contents.y() + self.scroll_contents.height())
            # 內容容器 - 底部
            if (y := self.visual_contents.height() - bottom) > 0\
                    and self.scroll_contents.height() >= self.visual_contents.height():
                self.scroll_contents_move(self.scroll_contents.x(), self.scroll_contents.y() + y)
            elif self.visual_contents.height() - bottom > 0:
                self.scroll_contents_move(self.scroll_contents.x(), 0)
        # 當滾動窗口超過 x高度 內容窗口往右移動
        if -self.scroll_contents.x() > 0:
            bottom = (self.scroll_contents.x() + self.scroll_contents.width())
            # 內容容器 - 底部
            if (x := self.visual_contents.width() - bottom) > 0 \
                    and self.scroll_contents.width() >= self.visual_contents.width():
                self.scroll_contents_move(self.scroll_contents.x() + x, self.scroll_contents.y())
            elif self.visual_contents.width() - bottom > 0:
                self.scroll_contents_move(0, self.scroll_contents.y())

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        # 重新設置滾動條相關數據
        self.refresh()
        # 計算內容窗口底部 距離可視窗口 是否有還有多於距離  有就移動到底
        self.set_distance()


# 滾動條容器
class ScrollContainer(QFrame):
    def __init__(self, parent: ScrollArea, orientation: int, single_step: int, interval: int, arrow: bool) -> None:
        super().__init__(parent)
        # 方向  1 是直  2 是橫
        self.orientation: int = orientation
        # 是否主動顯示
        self.status: bool = True
        # 設置是否需要箭頭
        self.arrow: bool = arrow
        # 步進距離
        self.scroll_jump: int = 0
        # 箭頭步進距離 背景點擊步進距離
        self.single_step: int = single_step
        # 滾動上限
        self.limit: int = 0
        # 滑塊大小
        self.slider_size: int = 0
        # 滑塊容器 滑動全部空間
        self.scroll_background: Scroll = Scroll(self, orientation)
        # 設定滑塊
        self.slider: Slider = self.scroll_background.slider
        # 是否顯示箭頭
        if arrow:
            # 距離邊緣距離
            self.interval: int = interval
            # 設置 上箭頭
            self.top: Button = Button(
                self, 1 if orientation == 1 else 3,
                clicked=lambda: parent.set_value(self.orientation, True, single_step)
            )
            # 根據方向移動上箭頭
            if orientation == 1:
                self.top.move(0, self.interval)
            else:
                self.top.move(self.interval, 0)
            # 設置 下箭頭
            self.bottom: Button = Button(
                self, 2 if orientation == 1 else 4,
                clicked=lambda: parent.set_value(self.orientation, False, single_step)
            )

    # 返回內容窗口目前的位置
    def value(self) -> int:
        return abs(self.parent().scroll_contents.y()) if self.orientation == 1 else abs(self.parent().scroll_contents.x())

    def setGeometry(self, *rect: QRect | int) -> None:
        QFrame.setGeometry(self, *rect)
        if self.arrow:
            # 獲取箭頭長度
            top_resize = self.top.height if self.orientation == 1 else self.top.width
            # 獲取頂部箭頭yx
            top_yx = self.top.y if self.orientation == 1 else self.top.x
            # 獲取底部箭頭yx
            bottom_yx = self.bottom.y if self.orientation == 1 else self.bottom.x
            # 獲取按鈕大小
            button_resize = (rect[2], int(rect[2] / 2)) if self.orientation == 1 else (int(rect[3] / 2), rect[3])
            # 獲取按鈕位置
            bottom_move = (0, self.height() - (button_resize[1] + self.interval)) if self.orientation == 1 else \
                (self.width() - (button_resize[0] + self.interval), 0)
            # 查看箭頭大小是否有變動 設定箭頭大小
            if (self.top.width() if self.orientation == 1 else self.top.height()) \
                    != rect[(2 if self.orientation == 1 else 3)]:
                # 設置 上箭頭大小
                self.top.resize(*button_resize)
                # 設置 下箭頭大小
                self.bottom.resize(*button_resize)
            self.bottom.move(*bottom_move)
            #  獲取起始位置 = top 底部位置 + 間隔箭頭距離
            yx = (top_yx() + top_resize()) + 7
            # 獲取大小 = bottom 頭部位置 - 間隔箭頭距離 - y
            resize = bottom_yx() - 7 - yx
            # 獲取按鈕背景大小
            background_resize = (0, yx, self.top.width(), resize) if self.orientation == 1 else \
                (yx, 0, resize, self.top.height())
            # 設定按鈕背景大小
            self.scroll_background.setGeometry(*background_resize)
        else:
            # 獲取按鈕背景大小
            background_resize = (0, 0, self.width(), self.height() - 1) \
                if self.orientation == 1 else \
                (0, 0, self.width() - 1, self.height())
            # 設定按鈕背景大小
            self.scroll_background.setGeometry(*background_resize)

        # 可視範圍
        viewport = self.parent().visual_contents.height() if self.orientation == 1\
            else self.parent().visual_contents.width()
        # 總範圍
        content = self.parent().scroll_contents.height() if self.orientation == 1\
            else self.parent().scroll_contents.width()
        if content == 0:
            return
        # 可視範圍/總範圍 = 總共多少頁
        viewableratio = viewport / content
        # 獲取可滑動距離
        scrollbararea = self.scroll_background.height() if self.orientation == 1 else self.scroll_background.width()
        # 設定滑塊大小
        self.slider_size = int(scrollbararea * viewableratio)
        # 查看是否小於滑塊最低大小
        if self.slider_size < 18:
            # 設置成最低滑塊大小
            self.slider_size = 18
        # 設定滾動上限
        self.limit = content - viewport
        # 滑塊可動空間
        scrollthumbspace = scrollbararea - self.slider_size
        # 如果可動空間 不等於0就進入
        if scrollthumbspace != 0:
            # 設定步進距離
            self.scroll_jump = self.limit / scrollthumbspace

    # 調整內容容器位置 value 移動數值
    def set_value(self, value: int) -> None:
        # 獲取內容容器yx座標
        yx = getattr(self.parent().scroll_contents, 'y' if self.orientation == 1 else 'x')
        # 獲取內容容器相反yx座標
        _yx = getattr(self.parent().scroll_contents, 'x' if self.orientation == 1 else 'y')
        # 判斷內容窗口是否存在 and 滾動條是否顯示
        if self.parent().scroll_contents and self.limit > 0:
            # 判斷數值是否小於0
            if value < 0:
                # 如果小於0就設定成0
                value = 0
            # 判斷數值是否超過上限
            elif value < -self.limit:
                # 如果超過上限則設定成上限值
                value = -self.limit
            # 獲取內容窗口移動數據
            move = (_yx(), value) if self.orientation == 1 else (value, _yx())
            # 設定內容窗口移動
            self.parent().scroll_contents_move(*move)
            # 判斷步進距離是否不等於0
            if self.scroll_jump != 0:
                # 獲取滑塊移動數據
                _move = (0, -int(yx() / self.scroll_jump)) if self.orientation == 1 \
                    else (-int(yx() / self.scroll_jump), 0)
                # 設定滑塊移動
                self.slider.move(*_move)


# 滑塊容器
class Scroll(QPushButton):
    def __init__(self, parent: ScrollContainer, orientation: int) -> None:
        super().__init__(parent)
        # 背景方向
        self.orientation: int = orientation
        # 滑塊
        self.slider: Slider = Slider(self, orientation)
        # 滑鼠座標
        self.yx: int = 0
        # 連接滑鼠點擊事件
        self.clicked.connect(self.click_move)
        # 按鈕按著計時
        self.setAutoRepeatDelay(0)
        # 按鈕重複調用時間
        self.setAutoRepeatInterval(100)
        # 啟用點擊連續調用
        self.setAutoRepeat(True)
        # 設置qss
        self.setStyleSheet("background-color:rgb(227, 227, 227); border-radius:5px")

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 獲取點擊座標
        self.yx = event.y() if self.orientation == 1 else event.x()
        # 調用原按鈕點擊事件  用於連續調用
        QPushButton.mousePressEvent(self, event)

    # 滑鼠點擊移動
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # 獲取點擊座標
        self.yx = event.y() if self.orientation == 1 else event.x()

    # 滑鼠持續點擊事件
    def click_move(self) -> None:
        # 滑塊yx
        slider_yx = getattr(self.slider, 'y' if self.orientation == 1 else 'x')()
        # 滑塊大小
        slider_resize = getattr(self.slider, 'height' if self.orientation == 1 else 'width')()
        # 判斷 滑塊yx 是否比 點擊座標 還要下面 還要大
        if slider_yx > self.yx:
            # 調用父類設定內容窗口 往上移動
            self.parent().parent().set_value(self.orientation, True, self.parent().single_step)
        elif slider_yx + slider_resize < self.yx:
            # 調用父類設定內容窗口 往下移動
            self.parent().parent().set_value(self.orientation, False, self.parent().single_step)


# 滑塊
class Slider(QPushButton):
    def __init__(self, parent: Scroll, orientation: int) -> None:
        super().__init__(parent)
        # 點擊移動後yx的值
        self.yx: int = 0
        # 滑塊方向
        self.orientation: int = orientation
        # 設置qss
        self.setStyleSheet("QPushButton{background-color:#d7d7d7;border-radius:5px;}\n"
                           "QPushButton:hover{background-color:#b3b3b3;}")

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 只接收左鍵
        if event.button() == Qt.LeftButton:
            # 獲取滑塊頂部座標
            self.yx = event.globalPos() - self.pos()

            # 改變鼠標指針
            self.setCursor(QCursor(Qt.PointingHandCursor))

    # 滑鼠放開事件
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        # 只接收左鍵
        if event.button() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ArrowCursor))

    # 滑鼠點擊移動
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # 滑塊大小長度
        resize = getattr(self, 'height' if self.orientation == 1 else 'width')()
        # 背景大小長度
        scroll_resize = getattr(self.parent(), 'height' if self.orientation == 1 else 'width')()
        # 獲取移動後 滑塊yx值
        yx = getattr(event.globalPos() - self.yx, 'y' if self.orientation == 1 else 'x')()
        # 獲取移動後 yx+高度 = 滑塊底部值
        _yx = yx + resize
        # 不大於背景大小 不小於0
        if _yx <= scroll_resize and yx >= 0:
            result = yx
        # 移動後滑塊底部值  不等於 背景大小長度  滑塊yx大於0
        elif _yx != scroll_resize and yx > 0:
            # 獲取可移動的上限 背景-滑塊
            result = scroll_resize - resize
        # 如果 yx值小於0
        elif yx < 0:
            # yx小於0一律變成0
            result = 0
        else:
            return
        # 獲取 內容窗口
        scroll_contents = self.parent().parent().parent().scroll_contents
        # 獲取移動內容窗口函數
        scroll_contents_move = self.parent().parent().parent().scroll_contents_move
        # 把 滑塊yx值 轉換成 內容窗口應該讀到哪裡
        _result = -round(result * self.parent().parent().scroll_jump)
        # 獲取滑塊應該移動的值
        move = (0, result) if self.orientation == 1 else (result, 0)
        # 獲取內容窗口應該移動的值
        _move = (scroll_contents.x(), _result) if self.orientation == 1 else (_result, scroll_contents.y())
        # 移動滑塊
        self.move(*move)
        # 移動內容窗口
        scroll_contents_move(*_move)


class Button(QPushButton):
    def __init__(self, parent: ScrollContainer, direction: int, clicked: Callable) -> None:
        super().__init__(parent)
        # 連接點擊信號
        self.clicked.connect(clicked)
        # 預設顏色
        self.color_1: tuple[int, ...] = (183, 188, 192)
        # 移動上方顏色
        self.color_2: tuple[int, ...] = (147, 154, 159)
        # 目前顏色
        self.currently: tuple[int, ...] = (183, 188, 192)
        # 三角形座標
        self.coordinate: tuple[tuple[int, int], tuple[int, int], tuple[int, int]] = ((0, 0), (0, 0), (0, 0))
        # 方向
        self.direction: int = direction
        # 按鈕按著計時
        self.setAutoRepeatDelay(500)
        # 按鈕重複調用時間
        self.setAutoRepeatInterval(100)

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 手動觸發 clicked 信號
        self.clicked.emit()
        # 開啟持續觸發按鈕
        self.setAutoRepeat(True)
        # 手動觸發 父類單擊 事件
        QPushButton.mousePressEvent(self, event)

    # 滑鼠放開事件
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        # 關閉持續觸發按鈕
        self.setAutoRepeat(False)

    # 鼠標移入事件
    def enterEvent(self, event: QEvent):
        self.currently = self.color_2
        self.update()

    # 鼠標移出事件
    def leaveEvent(self, event: QEvent) -> None:
        # 設置目前顏色
        self.currently = self.color_1
        # 手動更新
        self.update()

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        # 根據按鈕方向 來設置 按鈕大小
        # 上方按鈕
        if self.direction == 1:
            self.coordinate = ((self.height(), 0), (0, self.height()), (self.width(), self.height()))
        # 下方按鈕
        elif self.direction == 2:
            self.coordinate = ((0, 0), (self.height(), self.height()), (self.width(), 0))
        # 左邊按鈕
        elif self.direction == 3:
            self.coordinate = ((self.width(), 0), (0, self.width()), (self.width(), self.height()))
        # 右邊按鈕
        elif self.direction == 4:
            self.coordinate = ((0, 0), (self.width(), self.width()), (0, self.height()))

    # 繪製事件
    def paintEvent(self, event: QMouseEvent) -> None:
        # 查看是否有三角形座標
        if self.coordinate:
            painter = QPainter()
            painter.begin(self)
            path = QPainterPath()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(*self.currently))
            painter.setPen(QColor(*self.currently))
            path.moveTo(*self.coordinate[0])
            path.lineTo(*self.coordinate[1])
            path.lineTo(*self.coordinate[2])
            path.lineTo(*self.coordinate[0])
            painter.drawPath(path)
            painter.end()
