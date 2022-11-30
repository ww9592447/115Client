from PyQt5.Qt import QFrame, QCursor, QWidget, QApplication, Qt, QPushButton,\
                     QPainter, QPainterPath, QColor
from PyQt5 import QtGui, QtCore
from typing import Callable


# 滾動條背景
class Scroll(QPushButton):
    def __init__(self, parent, orientation):
        super().__init__(parent=parent)
        self.setStyleSheet("background-color:rgb(227, 227, 227); border-radius:5px")
        # 背景方向
        self.orientation = orientation
        # 滑塊
        self.slider = None
        # 滑鼠座標
        self.yx = 0
        # 連接滑鼠點擊事件
        self.clicked.connect(self.click_move)
        # 按鈕按著計時
        self.setAutoRepeatDelay(0)
        # 按鈕重複調用時間
        self.setAutoRepeatInterval(100)
        # 啟用點擊連續調用
        self.setAutoRepeat(True)

    # 滑鼠點擊
    def mousePressEvent(self, event):
        # 查看是否有滑塊
        if self.slider:
            # 獲取點擊座標
            self.yx = event.y() if self.orientation == 1 else event.x()
            # 調用原按鈕點擊事件  用於連續調用
            QPushButton.mousePressEvent(self, event)
        # 沒有滑塊 就從子類獲取
        elif self.children():
            # 獲取滑塊
            self.slider = self.children()[0]
            # 重新調用
            self.mousePressEvent(event)

    # 滑鼠點擊移動
    def mouseMoveEvent(self, event):
        # 獲取點擊座標
        self.yx = event.y() if self.orientation == 1 else event.x()

    # 滑鼠持續點擊事件
    def click_move(self):
        # 滑塊yx
        slider_yx = getattr(self.slider, 'y' if self.orientation == 1 else 'x')()
        # 滑塊大小
        slider_resize = getattr(self.slider, 'height' if self.orientation == 1 else 'width')()
        # 判斷 滑塊yx 是否比 點擊座標 還要下面 還要大
        if slider_yx > self.yx:
            # 調用父類設定內容窗口 往上移動
            self.parent().parent().setvalue(self.orientation, True, self.parent().singlestep)
        elif slider_yx + slider_resize < self.yx:
            # 調用父類設定內容窗口 往下移動
            self.parent().parent().setvalue(self.orientation, False, self.parent().singlestep)


# 滑塊
class Slider(QPushButton):
    def __init__(self, parent, orientation):
        super().__init__(parent)
        self.setStyleSheet("QPushButton{background-color:#d7d7d7;border-radius:5px;}\n"
                           "QPushButton:hover{background-color:#b3b3b3;}")
        self.yx = 0
        # 滑塊方向
        self.orientation = orientation

    # 滑鼠點擊
    def mousePressEvent(self, event):
        # 只接收左鍵
        if event.button() == Qt.LeftButton:
            self.yx = event.globalPos() - self.pos()  # 这个是获得滚动按钮的顶点值距离中心点的值
            self.setCursor(QCursor(Qt.PointingHandCursor))  # 改变鼠标指针

    # 滑鼠釋放
    def mouseReleaseEvent(self, event):
        # 只接收左鍵
        if event.button() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ArrowCursor))

    # 滑鼠點擊移動
    def mouseMoveEvent(self, event):
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
        scrollcontents = self.parent().parent().parent().scrollcontents
        # 獲取移動內容窗口函數
        scrollcontentsMove = self.parent().parent().parent().scrollcontentsMove
        # 把 滑塊yx值 轉換成 內容窗口應該讀到哪裡
        _result = -round(result * self.parent().parent().scrolljump)
        # 獲取滑塊應該移動的值
        move = (0, result) if self.orientation == 1 else (result, 0)
        # 獲取內容窗口應該移動的值
        _move = (scrollcontents.x(), _result) if self.orientation == 1 else (_result, scrollcontents.y())
        # 移動滑塊
        self.move(*move)
        # 移動內容窗口
        scrollcontentsMove(*_move)


# 滾動條容器
class ScrolContainer(QFrame):
    def __init__(self, parent, orientation, singlestep, interval, arrow):
        super().__init__(parent)
        # 方向  1 是直  2 是橫
        self.orientation = orientation
        # 是否主動顯示
        self.status = True
        # 設置是否需要箭頭
        self.arrow = arrow
        # 步進距離
        self.scrolljump = 0
        # 箭頭步進距離 背景點擊步進距離
        self.singlestep = singlestep
        # 滾動上限
        self.limit = 0
        # 滑塊大小
        self.slidersize = 0
        # 按鈕背景 滑動全部空間
        self.scrollbackground = Scroll(self, orientation)
        # 設定滑塊
        self.slider = Slider(self.scrollbackground, orientation)
        if arrow:
            # 距離邊緣距離
            self.interval = interval
            # 設置 上箭頭
            self.top = Button(
                self, 1 if orientation == 1 else 3,
                clicked=lambda: parent.setvalue(self.orientation, True, singlestep)
            )
            # 根據方向移動上箭頭
            if orientation == 1:
                self.top.move(0, self.interval)
            else:
                self.top.move(self.interval, 0)
            # 設置 下箭頭
            self.bottom = Button(
                self, 2 if orientation == 1 else 4,
                clicked=lambda: parent.setvalue(self.orientation, False, singlestep)
            )

    # 返回內容窗口目前的位置
    def value(self):
        return abs(self.parent().scrollcontents.y()) if self.orientation == 1 else abs(self.parent().scrollcontents.x())

    def setGeometry(self, *rect):
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
            # 查看箭頭大小是否有變動 設定箭頭大小
            if (self.top.width() if self.orientation == 1 else self.top.height())\
               != rect[(2 if self.orientation == 1 else 3)]:
                # 設置 上箭頭大小
                self.top.resize(*button_resize)
                # 設置 下箭頭大小
                self.bottom.resize(*button_resize)

            bottom_move = (0, self.height() - (self.bottom.height() + self.interval)) if self.orientation == 1 else\
                          (self.width() - (self.bottom.width() + self.interval), 0)
            self.bottom.move(*bottom_move)
            #  獲取起始位置 = top 底部位置 + 間隔箭頭距離
            yx = (top_yx() + top_resize()) + 7
            # 獲取大小 = bottom 頭部位置 - 間隔箭頭距離 - y
            resize = bottom_yx() - 7 - yx
            # 獲取按鈕背景大小
            background_resize = (0, yx, self.top.width(), resize) if self.orientation == 1 else\
                                (yx, 0, resize, self.top.height())
            # 設定按鈕背景大小
            self.scrollbackground.setGeometry(*background_resize)
        else:
            # 獲取按鈕背景大小
            background_resize = (0, 0, self.width(), self.height() - 1)\
                                if self.orientation == 1 else\
                                (0, 0, self.width() - 1, self.height())
            # 設定按鈕背景大小
            self.scrollbackground.setGeometry(*background_resize)

        # 可視範圍
        viewport = self.parent().visualcontents.height() if self.orientation == 1 else self.parent().visualcontents.width()
        # 總範圍
        content = self.parent().scrollcontents.height() if self.orientation == 1 else self.parent().scrollcontents.width()
        if content == 0:
            return
        # 可視範圍/總範圍 = 總共多少頁
        viewableratio = viewport / content
        # 獲取可滑動距離
        scrollbararea = self.scrollbackground.height() if self.orientation == 1 else self.scrollbackground.width()
        # 設定滑塊大小
        self.slidersize = int(scrollbararea * viewableratio)
        # 查看是否小於滑塊最低大小
        if self.slidersize < 18:
            # 設置成最低滑塊大小
            self.slidersize = 18
        # 設定滾動上限
        self.limit = content - viewport
        # 滑塊可動空間
        scrollthumbspace = scrollbararea - self.slidersize
        # 如果可動空間 不等於0就進入
        if scrollthumbspace != 0:
            # 設定步進距離
            self.scrolljump = self.limit / scrollthumbspace

    # 調整內容容器位置 value 移動數值
    def setvalue(self, value):
        # 獲取內容容器yx座標
        yx = getattr(self.parent().scrollcontents, 'y' if self.orientation == 1 else 'x')
        # 獲取內容容器相反yx座標
        _yx = getattr(self.parent().scrollcontents, 'x' if self.orientation == 1 else 'y')
        # 判斷內容窗口是否存在 and 滾動條是否顯示
        if self.parent().scrollcontents and self.limit > 0:
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
            self.parent().scrollcontentsMove(*move)
            # 判斷步進距離是否不等於0
            if self.scrolljump != 0:
                # 獲取滑塊移動數據
                _move = (0, -int(yx() / self.scrolljump)) if self.orientation == 1 else (-int(yx() / self.scrolljump), 0)
                # 設定滑塊移動
                self.slider.move(*_move)


class Button(QPushButton):
    def __init__(self, parent: ScrolContainer, direction: int, clicked: Callable=None) -> None:
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
        self.direction = direction
        # 按鈕按著計時
        self.setAutoRepeatDelay(500)
        # 按鈕重複調用時間
        self.setAutoRepeatInterval(100)

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        # 手動觸發 clicked 信號
        self.clicked.emit()
        # 開啟持續觸發按鈕
        self.setAutoRepeat(True)
        # 手動觸發 父類單擊 事件
        QPushButton.mousePressEvent(self, event)

    # 滑鼠放開事件
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        # 關閉持續觸發按鈕
        self.setAutoRepeat(False)

    # 鼠標移出事件
    def leaveEvent(self, event: QtCore.QEvent) -> None:
        # 設置目前顏色
        self.currently = self.color_2
        # 手動更新
        self.update()

    # direction 箭頭方向
    def resize(self, *size):
        QPushButton.resize(self, *size)
        if self.direction == 1:
            self.coordinate = ((self.height(), 0), (0, self.height()), (self.width(), self.height()))
        elif self.direction == 2:
            self.coordinate = ((0, 0), (self.height(), self.height()), (self.width(), 0))
        elif self.direction == 3:
            self.coordinate = ((self.width(), 0), (0, self.width()), (self.width(), self.height()))
        elif self.direction == 4:
            self.coordinate = ((0, 0), (self.width(), self.width()), (0, self.height()))

    def paintEvent(self, event):
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


class ScrollContents(QFrame):
    def __init__(self, parent):
        super().__init__(parent)


    def move(self, *__args):
        QFrame.move(self, *__args)


# 滾動條容器
class ScrollArea(QFrame):
    # scrollsize=滾動條大小 singlestep=箭頭步進距離 interval=滾動條離邊框距離 arrow=是否顯示箭頭
    def __init__(self, parent, visualcontents=None, scrollcontents=None, scrollsize=14, singlestep=20, pagestep=60, interval=5, arrow=True):
        super().__init__(parent=parent)
        # 設定名稱
        self.setObjectName('ScrollArea')
        # 滾動條大小
        self.scrollsize = scrollsize
        # 滾動條箭頭移動距離
        self.singlestep = singlestep
        # 滾條條背景點擊移動距離
        self.pagestep = pagestep
        # 內容容器  可視窗口 為了防止擋到邊框 還有滾動條
        if visualcontents:
            # 設置 self 成為 內容容器 可視窗口 的父類
            visualcontents.setParent(self)
            self.visualcontents = visualcontents
        else:
            self.visualcontents = QFrame(self)
        self.visualcontents.move(1, 1)
        self.visualcontents.show()
        # self.visualcontents.setStyleSheet('border:1px solid rgb(200, 200, 100)')
        # 設置內容窗口
        if scrollcontents:
            # 設置 self.visualcontents 成為 內容窗口 的父類
            scrollcontents.setParent(self.visualcontents)
            self.scrollcontents = scrollcontents
        else:
            self.scrollcontents = QFrame(self.visualcontents)
            # self.scrollcontents = ScrollContents(self.visualcontents)
        # 安裝事件過濾
        self.scrollcontents.installEventFilter(self)
        # 直滾動條容器
        self.verticalcontents = ScrolContainer(self, 1, singlestep, interval, arrow)
        # 橫滾動條容器
        self.hrizontalcontents = ScrolContainer(self, 2, singlestep, interval, arrow)

    # 添加新的內容窗口
    def setwidget(self, scrollcontents):
        # 查看是否有舊的內窗口
        if self.scrollcontents:
            # 如果有則隱藏以便下次調用
            self.scrollcontents.hide()
            # 解除事件過濾器
            self.scrollcontents.removeEventFilter(self)
        # 設置 self.visualcontents 成為 內容窗口 的父類
        scrollcontents.setParent(self.visualcontents)
        # 設置內容窗口
        self.scrollcontents = scrollcontents
        # 安裝事件過濾
        self.scrollcontents.installEventFilter(self)
        # 內容窗口顯示
        self.scrollcontents.show()

    # 手動設置直滾動條是否能夠顯示
    def setvertical(self, status):
        self.verticalcontents.status = status
        self.setscroll()


    # 手動設置橫滾動條是否能夠顯示
    def sethrizontal(self, status):
        self.hrizontalcontents.status = status
        self.setscroll()

    # 調整內容容器位置  orientation 滾動條方向 direction 滾動條箭頭方向 move 移動數值
    def setvalue(self, orientation, direction, move):
        # 獲取內容容器yx座標
        yx = getattr(self.scrollcontents, 'y' if orientation == 1 else 'x')
        # 獲取內容容器相反yx座標
        _yx = getattr(self.scrollcontents, 'x' if orientation == 1 else 'y')
        # 獲取滾動條上限
        limit = self.verticalcontents.limit if orientation == 1 else self.hrizontalcontents.limit
        # 獲取滾動條步進距離
        scrolljump = self.verticalcontents.scrolljump if orientation == 1 else self.hrizontalcontents.scrolljump
        # 獲取滾動條滑塊
        slider = self.verticalcontents.slider if orientation == 1 else self.hrizontalcontents.slider
        # 獲取滾動條是否可動
        isvisible = self.verticalcontents.limit > 0 if orientation == 1 else self.hrizontalcontents.limit > 0
        # 判斷內容窗口是否存在 and 滾動條是否顯示
        if self.scrollcontents and isvisible:
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
            self.scrollcontentsMove(*_move)
            # 判斷步進距離是否不等於0
            if scrolljump != 0:
                # 獲取滑塊移動數據
                _move = (0, -int(yx() / scrolljump)) if orientation == 1 else (-int(yx() / scrolljump), 0)
                # 設定滑塊移動
                slider.move(*_move)

    # 滾輪事件
    def wheelEvent(self, event):
        if self.scrollcontents:
            if QApplication.keyboardModifiers() == Qt.ShiftModifier and self.hrizontalcontents.limit > 0:
                if event.angleDelta().y() > 0:
                    self.setvalue(2, True, self.pagestep)
                else:
                    self.setvalue(2, False, self.pagestep)
            elif self.scrollcontents and self.verticalcontents.limit > 0:
                if event.angleDelta().y() > 0:
                    self.setvalue(1, True, self.pagestep)
                else:
                    self.setvalue(1, False, self.pagestep)

    # 設置滾動條相關數據
    def setscroll(self):
        if self.scrollcontents:
            # 獲取 橫滾動條是否顯示
            width = (_width := (self.width() - 2) - self.scrollcontents.width()) < 0
            # 獲取 直滾動條是否顯示
            height = (_height := (self.height() - 2) - self.scrollcontents.height()) < 0
            # 如果 橫滾動條顯示進入
            if width and not height and self.hrizontalcontents.status:
                # (直可視範圍 - 直容器) - 橫滾動條 獲取 是否還有空間 如果沒有則顯示 直滾動條
                height = _height - self.scrollsize < 0
            # 如果 直滾動條顯示進入
            elif height and not width and self.verticalcontents.status:
                # (橫視範圍 - 橫容器) - 直滾動條 獲取 是否還有空間 如果沒有則顯示 橫滾動條
                width = _width - self.scrollsize < 0
            # 判斷是否主動隱藏直滑動條
            if not self.verticalcontents.status:
                height = False
            # 判斷是否主動隱藏橫滑動條
            if not self.hrizontalcontents.status:
                width = False
            # 判斷是否需要顯示 直滾動條
            self.verticalcontents.show() if height else self.verticalcontents.hide()

            # 判斷是否需要顯示 橫滾動條
            self.hrizontalcontents.show() if width else self.hrizontalcontents.hide()
            # 設定 容器背景 可視窗口 大小
            self.visualcontents.resize(self.width() - 2 - (self.scrollsize if height else 0),
                                   self.height() - 2 - (self.scrollsize if width else 0))
            # 設定 直滾動條 大小
            self.verticalcontents.setGeometry(self.width() - (self.scrollsize + 1), 1, self.scrollsize,
                                             self.height() - 1 - (self.scrollsize if height and width else 0))
            # 設定 橫滾動條 大小
            self.hrizontalcontents.setGeometry(1, self.height() - (self.scrollsize + 1),
                                              self.width() - 1 - (self.scrollsize if height and width else 0),
                                              self.scrollsize)


            # 計算內容窗口底部 距離可視窗口 是否有還有多於距離 有就移動到底
            self.setdistance()


            # 獲取直滑塊大小 設定步進距離
            verticalsliderheight = self.verticalcontents.slidersize
            # 獲取橫滑塊大小
            hrizontalwidth = self.hrizontalcontents.slidersize

            y = 0
            if self.verticalcontents.scrolljump != 0:
                y = int(self.verticalcontents.value() / self.verticalcontents.scrolljump)
            # 設置直滑塊大小
            self.verticalcontents.slider.setGeometry(0, y, self.scrollsize, verticalsliderheight)

            x = 0
            if self.hrizontalcontents.scrolljump != 0:
                x = int(self.hrizontalcontents.value() / self.hrizontalcontents.scrolljump)
            # 設置橫滑塊大小
            self.hrizontalcontents.slider.setGeometry(x, 0, hrizontalwidth, self.scrollsize)



    # 獲取內容窗口移動距離
    def scrollContentsBy(self, dx, dy):
        pass

    # 設定內容窗口移動
    def scrollcontentsMove(self, x, y):
        # 獲取內容窗口 x 移動距離
        dx = x - self.scrollcontents.x()
        # 獲取內容窗口 y 移動距離
        dy = y - self.scrollcontents.y()
        # 移動內容窗口
        self.scrollcontents.move(x, y)
        # 傳遞 移動距離給函數
        self.scrollContentsBy(dx, dy)

    # 當內容窗口有變化 刷新 內容窗口 相關數據
    def refresh(self):
        # 獲取目前內容窗口y座標
        y = self.scrollcontents.y()
        # 獲取目前內容窗口x座標
        x = self.scrollcontents.x()
        # 判斷 y座標是否被移動過
        if self.scrollcontents.y() != 0:
            # (內容窗口y+內容窗口長度) = 目前內容窗口 y底部位置
            # 內容窗口 底部位置 - 內容容器長度 如果小於0 則代表需要重新設定內容窗口y座標
            if (dy := self.scrollcontents.y() + self.scrollcontents.height() - self.visualcontents.height()) <= 0:
                # 0是y座標最頂部位置
                # 判斷 內容窗口y + 移動座標 是否大於0 代表超過移動極限
                if (y := self.scrollcontents.y() + -dy) > 0:
                    # 設置移動座標y = 0
                    y = 0
        # 判斷 x座標是否被移動過
        if self.scrollcontents.x() != 0:
            # (內容窗口X+內容窗口長度) = 目前內容窗口 X底部位置
            # 內容窗口 底部位置 - 內容容器長度 如果小於0 則代表需要重新設定內容窗口X座標
            if (dx := self.scrollcontents.x() + self.scrollcontents.width() - self.visualcontents.width()) <= 0:
                # 0是x座標最頂部位置
                # 判斷 內容窗口x + 移動座標 是否大於0 代表超過移動極限
                if (x := self.scrollcontents.x() + -dx) > 0:
                    # 設置移動座標x = 0
                    x = 0
        # 設定內容窗口新座標
        self.scrollcontentsMove(x, y)
        # 重新設置滾動條相關數據
        self.setscroll()

    def eventFilter(self, watched, event):
        # 內容窗口 有調整大小 事件 進入  窗口大小有變化自動調整內容窗口座標  自動調整滑塊數據
        if event.type() == 14:
            # 刷新滾動條相關資料
            self.refresh()
        return super().eventFilter(watched, event)

    # 計算內容窗口底部 距離可視窗口 是否有還有多於距離  有就移動到底
    def setdistance(self):
        # 當滾動窗口超過 y高度 內容窗口往下移動
        if -self.scrollcontents.y() > 0:
            bottom = (self.scrollcontents.y() + self.scrollcontents.height())
            # 內容容器 - 底部
            if (y := self.visualcontents.height() - bottom) > 0 and self.scrollcontents.height() >= self.visualcontents.height():
                self.scrollcontentsMove(self.scrollcontents.x(), self.scrollcontents.y() + y)
            elif self.visualcontents.height() - bottom > 0:
                self.scrollcontentsMove(self.scrollcontents.x(), 0)
        # 當滾動窗口超過 x高度 內容窗口往右移動
        if -self.scrollcontents.x() > 0:
            bottom = (self.scrollcontents.x() + self.scrollcontents.width())
            # 內容容器 - 底部
            if (x := self.visualcontents.width() - bottom) > 0 and self.scrollcontents.width() >= self.visualcontents.width():
                self.scrollcontentsMove(self.scrollcontents.x() + x, self.scrollcontents.y())
            elif self.visualcontents.width() - bottom > 0:
                self.scrollcontentsMove(0, self.scrollcontents.y())

    def resizeEvent(self, event):
        # 重新設置滾動條相關數據
        self.refresh()
        # 計算內容窗口底部 距離可視窗口 是否有還有多於距離  有就移動到底
        self.setdistance()