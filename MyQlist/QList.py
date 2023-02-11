from .module import QFrame, QWidget, QApplication, sys, Qt, QPoint, QPainter, QPen, QColor, \
    gif, QCursor, QMenu, QLabel, MyIco, QObject, QWheelEvent, QResizeEvent, QMouseEvent, TitleList,\
    Union, math, Callable, Optional, QPaintEvent, QAction, TextSave, MyTextSave
from .MScroolBar import ScrollArea
from .QTitle import QTitle, Title, MovingBar
from .QText import QText, Text


class ListCheck(QFrame):
    def __init__(self, parent: QObject = None) -> None:
        QFrame.__init__(self, parent)
        # 設置 text 最大大小
        self.textmax: int = 39
        # 設置標題 窗口 最大大小
        self.titlemax: int = 31
        # 設置標題離左邊框多遠
        self.titleinterval: int = 3
        # 設置標題移動條可觸碰大小
        self.titllinesize: int = 7
        # 上限多少個text
        self.pagemax: int = 1000
        # 目前已顯示多少text
        self.textvalue: int = 0
        # 當前頁數多少text
        self.textall: int = 0
        # 底部統計 窗口 最大大小
        self.quantitymax: int = 34
        # 設置 text 右鍵菜單
        self.contextmenu: QMenu = QMenu(self)
        # 所有 text 右鍵菜單
        self.menu: dict[str, QAction] = {}
        # text最後一次點擊
        self.firstclick: Optional[Text] = None
        # 複選紐 手動調整可觸碰大小
        self.touchable: Union[tuple[int, ...], None] = None
        # 換頁回調
        self.page_callback: Optional[Callable] = None
        # 右鍵回調
        self.menu_callback: Optional[Callable] = None
        # 背景右鍵回調
        self.backdrop_menu_callback: Optional[Callable] = None
        # 所有容器
        self.allqwidget: AllQWidget = AllQWidget(self)
        # 設置統計容器
        self.quantity: Quantity = Quantity(self.allqwidget, self)
        # 內容窗口
        self.scrollcontents: ScrollContents = ScrollContents(self)
        # 初始化內容窗口大小
        self.scrollcontents.resize(0, 0)
        # 設置滾動區
        self.scrollarea: QScrollArea = QScrollArea(self.allqwidget, self, self.scrollcontents, VisualContents(self))
        # 移動滾動區到標題之下
        self.scrollarea.move(0, self.titlemax)
        # 可拖曳窗口 等待gui
        self.select = Select(self.allqwidget)
        # 移動位置跟內容窗口等同位置
        self.select.move(1, self.titlemax + 1)
        # 所有標題
        self.titlelist: TitleList[tuple[Title, MovingBar], ...] = TitleList()
        # 目前所有複選紐點擊
        self.currentclick: Currentclick[Text, ...] = Currentclick(self)
        # 所有text
        self.textlist: list[Text, ...] = []
        # 儲存頁數資料
        self.textsave: List = List(self, self.pagemax)
        # 儲存所有介面的頁數資料
        self.savecontents: dict[Optional[str], List] = {None: self.textsave}
        # 設置標題
        self.title = QTitle(self.allqwidget, self)
        # 設置text
        self.text = QText(self)
        # 初始化頁數
        self.addallpage(1)
        # 設置空白背景
        self.setStyleSheet('ListCheck{background-color: rgb(255, 255, 255)}')

    # 設定目前所有頁數
    def addallpage(self, value: int) -> None:
        self.quantity.addallpage(value)
        self.textsave.addallpage(value)

    # 新增 新窗口
    def new(self, name: str) -> None:
        # 初始化目前已顯示多少text
        self.textvalue = 0
        # 初始化當前頁數多少text
        self.textall = 0
        # 紀錄目前標題
        self.textsave.addtitle(self.titlelist.text())
        # 設置新儲存頁數資料
        self.textsave: List = List(self, self.pagemax)
        # 更新 儲存所有介面的頁數資料
        self.savecontents[name] = self.textsave
        # 初始化目前頁數
        self.quantity.setpage(1, False)
        # 設置最大頁數為1
        self.addallpage(1)

    # 切換窗口
    def switch(self, name: Optional[str]) -> None:
        # 清空目前點擊
        self.cls_click()
        # 紀錄當前標題
        self.textsave.addtitle(self.titlelist.text())
        # 設置新的頁數資料
        self.textsave = self.savecontents[name]
        # 查看是否需要變更標題
        if titlelist := (set(self.titlelist.text()) - set(self.textsave.gettitle())):
            for title in titlelist:
                self.title.set_title_visible(title, False)
        elif titlelist := (set(self.titlelist.text()) ^ set(self.textsave.gettitle())):
            for title in titlelist:
                self.title.set_title_visible(title, True)
        # 設置新介面最大頁數
        self.quantity.addallpage(len(self.textsave))
        # 設置成第一頁
        self.quantity.setpage(1, False)

    # 初始化當前介面
    def cls(self) -> None:
        # text資料清空
        self.textsave.cls()
        # 初始化目前已顯示多少text
        self.textvalue = 0
        # 初始化當前頁數多少text
        self.textall = 0
        # 設置成第一頁
        self.quantity.setpage(1, False)
        # 設置頁數上限
        self.addallpage(1)

    # 重新設定texts資料
    def textadd(
            self,
            text: dict[str, MyTextSave],
            data: any = None,
            ico: Optional[str] = None,
            leftclick: Optional[list[Callable, ...]] = None,
            doubleclick: Optional[list[Callable, ...]] = None
    ) -> None:

        textsave: TextSave = {
            'text': text,
            'data': data,
            'ico': ico,
            'leftclick': leftclick,
            'doubleclick': doubleclick
        }
        self.textsave.append(textsave)
        self.textall += 1
        self.scrollarea.textrefresh()

    # 批量重新設定texts資料
    def textadds(self, text: list[TextSave, ...]) -> None:
        for save in text:
            self.textsave.append(save)
            self.textall += 1
        self.scrollarea.textrefresh()

    # 設置標題
    def title_add(self, text: str, width: int = 50, least: int = 50) -> None:
        self.title.add(text, width, least)

    # 返回指定data or 已點擊texts data
    def extra(self, index: Optional[int] = None) -> any:
        if index is not None:
            return self.textlist[index].data
        if len(self.currentclick) == 0:
            return None
        data = []
        for text in self.currentclick:
            data.append(text.data)
        if len(data) == 1:
            return data[0]
        else:
            return data

    # 設定 vbox 可觸碰大小
    def settouchable(self, resize: int) -> None:
        self.touchable = resize

    # 清空所有點擊
    def cls_click(self) -> None:
        for text in self.currentclick.copy():
            text.setstate()

    # 連結 text 右鍵 菜單
    def text_menu_click_connect(self, text: str, slot: Callable, mode: bool = True) -> None:
        cp = self.contextmenu.addAction(text)
        cp.triggered.connect(slot)
        cp.setVisible(mode)
        self.menu[text] = cp

    # 連結 背景 右鍵 菜單
    def backdrop_menu_click_connect(self, text: str, slot: Callable, mode: bool = True) -> None:
        cp = self.allqwidget.contextmenu.addAction(text)
        cp.triggered.connect(slot)
        cp.setVisible(mode)
        self.allqwidget.menu[text] = cp

    # 設置標題是否顯示
    def set_title_visible(self, name: str, visible: bool) -> None:
        self.title.set_title_visible(name, visible)

    # 設置 加載GIF 顯示 or 隱藏
    def set_load_visible(self, visible: bool) -> None:
        self.select.set_load_visible(visible)

    # 設置 text右鍵 是否可顯示
    def set_menu_visible(self, text: str, mode: bool) -> None:
        self.menu[text].setVisible(mode)

    # 設置 背景右鍵 是否可顯示
    def set_backdrop_menu_visible(self, text: str, mode: bool) -> None:
        self.allqwidget.menu[text].setVisible(mode)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.allqwidget.resize(
            self.width(),
            self.height() - self.allqwidget.y()
        )
        bottom = self.title.x() + self.title.width()
        self.title.resize(1 + self.title.width() + (self.width() - bottom), self.titlemax)
        self.scrollarea.resize(self.width(), self.allqwidget.height() - self.titlemax - self.quantitymax)
        self.quantity.setGeometry(
            0, self.allqwidget.height() - self.quantitymax,
            self.allqwidget.width(), self.quantitymax
        )


class List:
    def __init__(self, listcheck: ListCheck, _max: int) -> None:
        self.listcheck: ListCheck = listcheck
        # 所有 text 資料
        self.text: dict[int, list[TextSave, ...]] = {1: []}
        # 一頁顯示多少個
        self.max: int = _max
        # 儲存目前標題
        self.title: list[str, ...] = []

    # 初始化資料
    def cls(self):
        # 初始化 所有 text 資料
        self.text.clear()
        # 設置新數值
        self.text[1] = []
        # 初始化 目前標題
        self.title.clear()

    # 新增標題
    def addtitle(self, title: list[str, ...]) -> None:
        self.title.clear()
        self.title.extend(title.copy())

    # 獲取標題
    def gettitle(self) -> list[str, ...]:
        return self.title

    # 設置最大頁數
    def addallpage(self, index: int) -> None:
        for value in range(len(self.text) + 1, index + 1):
            # 設置最大頁數
            self.text[value] = []

    # 新增新text資料
    def append(self, value: TextSave) -> None:
        # 新增 text 資料
        self.text[self.listcheck.quantity.page].append(value)

    # ==
    def __eq__(self, other: list[TextSave, ...]) -> bool:
        return self.text[self.listcheck.quantity.page] == other

    # dict[key]
    def __getitem__(self, index: int) -> TextSave:
        return self.text[self.listcheck.quantity.page][index]

    def len(self) -> int:
        return len(self.text[self.listcheck.quantity.page])

    def __len__(self) -> int:
        return len(self.text)


# 所有點擊
class Currentclick(list):
    def __init__(self, listcheck: ListCheck) -> None:
        super().__init__()
        self.listcheck: ListCheck = listcheck

    def append(self, __object: Text) -> None:
        super().append(__object)
        value = len(self)
        self.listcheck.quantity.setvalue(value)
        if value == self.listcheck.textall:
            self.listcheck.title.clickqlabel.setstate(True)

    def remove(self, __value: Text) -> None:
        super().remove(__value)
        if len(self) == 0:
            self.listcheck.quantity.all(self.listcheck.textall)
        else:
            self.listcheck.quantity.setvalue(len(self))
        if self.listcheck.title.clickqlabel.state:
            self.listcheck.title.clickqlabel.setstate(False)


# 所有容器
class AllQWidget(QWidget):
    def __init__(self, parent: ListCheck) -> None:
        super().__init__(parent)
        self.listcheck: ListCheck = parent
        # 初始化矩形座標
        self.rect: list[int, int, int, int] = [0, 0, 0, 0]
        # 保存第一次點擊Y座標
        self._y: int = 0
        # 保存內容窗口移動Y座標
        self.by: int = 0
        # 內容窗口初始座標
        self.titlesize: QPoint = QPoint(1, self.listcheck.titlemax + 1)
        # 設置 背景 右鍵菜單
        self.contextmenu: QMenu = QMenu(self)
        # 所有 背景 右鍵菜單
        self.menu: dict[str, QAction] = {}
        # 設置右鍵策略
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # 設置右鍵連接事件
        self.customContextMenuRequested.connect(self.display)

    # 右鍵事件
    def display(self) -> None:
        if self.menu:
            if self.listcheck.backdrop_menu_callback:
                self.listcheck.backdrop_menu_callback(lambda: self.contextmenu.exec_(QCursor.pos()))
            else:
                self.contextmenu.exec_(QCursor.pos())

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 清空所有已點擊
        self.listcheck.cls_click()
        # 獲取窗口相對座標
        pos = event.pos() - self.titlesize
        # 查看相對座標 是否 不是負數 and 左鍵點擊
        if pos.x() > 0 < pos.y() and event.buttons() == Qt.LeftButton:
            # 設定第一次點擊 內容窗口y相對座標
            self._y = pos.y() - self.listcheck.scrollcontents.y()
            # 設定內容窗口移動Y座標
            self.by = self.listcheck.scrollcontents.y()
            # 設定矩形座標
            self.rect[0] = pos.x()
            # 設定矩形座標
            self.rect[1] = pos.y()

    # 滑鼠放開事件
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        # 還原矩形座標
        self.rect = [0, 0, 0, 0]
        # 刷新矩形
        self.listcheck.select.update_(self.rect)

    # 滾輪事件
    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.rect != [0, 0, 0, 0]:
            # 獲取內容窗口移動多少
            y = abs(self.by - self.listcheck.scrollcontents.y())
            # 設置新內容窗口y座標
            self.by = self.listcheck.scrollcontents.y()
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
            pos = self.mapFromGlobal(event.globalPos()) - self.titlesize
            # 設定刷新矩形相關資料
            self.setupdate(pos)

    # 滑鼠點擊移動
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.rect[0:2] != [0, 0]:
            # 獲取窗口相對座標
            pos = event.pos() - self.titlesize
            # 設定矩形要多大
            self.rect[2] = pos.x() - self.rect[0]
            self.rect[3] = pos.y() - self.rect[1]
            # 設定刷新矩形相關資料
            self.setupdate(pos)

    # 設定刷新矩形相關資料
    def setupdate(self, pos: QPoint) -> None:
        # 刷新矩形
        self.listcheck.select.update_(self.rect)
        # 獲取第一次點擊內容窗口y座標, 目前內容窗口y相對座標
        y = [self._y, pos.y() - self.listcheck.scrollcontents.y()]
        # 排序相對座標
        y.sort()
        # 查看最小相對y座標是否大於 內容窗口大小  小於0
        if self.listcheck.scrollcontents.height() >= y[0] >= 0:
            # 獲取 最低相對座標 在哪個texys上面
            _min = int(y[0] / self.listcheck.textmax)
            # 獲取 最高相對座標 在哪個text上面
            if (_max := self.listcheck.textall) > int(y[1] / self.listcheck.textmax):
                _max = int(y[1] / self.listcheck.textmax) + 1
            # 獲取最低到最高的迭代器
            select = self.listcheck.textlist[_min: _max]
            # 開始循環迭代器
            for texts in select:
                # 查看index 是否在 以點擊裡面
                if texts not in self.listcheck.currentclick:
                    # 不在就 index 變成已點擊
                    texts.setstate()
            # 查看迭代器 是否空白
            if select:
                # 設定最後一次點擊
                self.listcheck.firstclick = select[-1]
            # 查看所有已點擊的 是否有多餘的
            for text in set(self.listcheck.currentclick) ^ set(select):
                # 多餘的點擊取消
                text.setstate()


# 可拖曳窗口 等待gui
class Select(QFrame):
    def __init__(self, parent: AllQWidget):
        super(Select, self).__init__(parent)
        # 初始化矩形座標
        self.rect: list[int, int, int, int] = [0, 0, 0, 0]
        # 設定等待GIF
        self.load = gif(self, '加載')
        # 設置 GIF 大小
        self.load.resize(20, 20)
        # 設置滑鼠穿透
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        # self.setStyleSheet('Select{background-color: rgb(255, 255, 255)}')

    def set_load_visible(self, visible: bool) -> None:
        if visible:
            self.load.raise_()
        self.load.setVisible(visible)

    def update_(self, rect: list[int, int, int, int]) -> None:
        self.rect = rect
        self.update()

    # 繪畫事件
    def paintEvent(self, event: QPaintEvent) -> None:
        # 初始化繪圖工具
        qp = QPainter()
        # 開始在窗口繪製
        qp.begin(self)
        # 自定義畫筆方法
        if self.rect != [0, 0, 0, 0]:
            self.drawrect(qp)
        # 結束在窗口的繪製
        qp.end()

    def drawrect(self, qp: QPainter) -> None:
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


# 內容窗口
class ScrollContents(QFrame):
    def __init__(self, listcheck: ListCheck) -> None:
        super().__init__()
        self.listcheck: ListCheck = listcheck
        # 禁止傳遞事件給父代  為了防止背景右鍵菜單傳遞
        self.setAttribute(Qt.WA_NoMousePropagation, True)

    # 滾輪事件
    def wheelEvent(self, event: QWheelEvent) -> None:
        # 因為禁止傳遞給父代  所以滾輪事件無法傳遞  所以手動傳遞滾輪事件
        self.listcheck.scrollarea.wheelEvent(event)
        self.listcheck.allqwidget.wheelEvent(event)


# 可視窗口容器
class VisualContents(QFrame):
    def __init__(self, listcheck: ListCheck) -> None:
        super().__init__()
        self.listcheck: ListCheck = listcheck

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.listcheck.select.resize(self.size())


# 滾動區
class QScrollArea(ScrollArea):
    def __init__(self, parent, listcheck: ListCheck, scrollcontents: ScrollContents, visualcontents: VisualContents):
        super().__init__(parent, scrollcontents=scrollcontents, visualcontents=visualcontents)
        self.listcheck: ListCheck = listcheck

    def textrefresh(self):
        _max = math.ceil((abs(self.scrollcontents.y()) + self.visualcontents.height()) / self.listcheck.textmax) + 1
        # print(self.listcheck.textvalue, _max)
        for index in range(self.listcheck.textvalue, _max):
            if index < self.listcheck.textall:
                self.listcheck.textlist[index].refresh()
                self.listcheck.textvalue += 1
            else:
                break

        # 設置內容容器大小
        self.listcheck.scrollcontents.resize(
            self.listcheck.scrollcontents.width(),
            self.listcheck.textall * self.listcheck.textmax
        )
        if not self.listcheck.currentclick:
            # 設定統計數量
            self.listcheck.quantity.all(self.listcheck.textall)

    # 滾動條移動回調
    def scrollcontentsby(self, dx: int, dy: int) -> None:
        # 刷新 text數據
        self.textrefresh()
        # 當橫滾動條移動後 標題需要跟著移動
        self.listcheck.title.move(self.listcheck.title.x() + dx, 0)
        # 獲取標題寬度底部位置
        bottom = self.listcheck.title.x() + self.listcheck.title.width()
        # 設定標題寬度
        self.listcheck.title.resize(
            1 + self.listcheck.title.width() + (self.listcheck.width() - bottom),
            self.listcheck.titlemax
        )


# 統計容器
class Quantity(QFrame):
    def __init__(self, parent: AllQWidget, listcheck: ListCheck) -> None:
        super().__init__(parent)
        self.listcheck: ListCheck = listcheck
        # 目前頁數
        self.page: int = 1
        # 目前最大頁數
        self.pagemax: int = 0
        # 設置總共多少 text 文字
        self.alltext: QLabel = QLabel(self)
        # 設置文字顏色
        self.alltext.setStyleSheet('color:rgb(153, 153, 171)')
        # 設定預設文字
        self.alltext.setText('0項')
        # 自動調整成符合大小
        self.alltext.adjustSize()
        # 所有頁數容器
        self.pageico: QFrame = QFrame(self)
        # 所有容器隱藏
        self.pageico.hide()
        # 頁數列表 並且新增第一頁
        self.pagelist: list[Page, ...] = [Page('1', (16, 0, 10, 18), True, self)]
        # 設置頁數文字容器
        self.pagetext = QLabel(self.pageico)
        # 設置頁數文字顏色
        self.pagetext.setStyleSheet('color:rgb(153, 153, 171)')
        # 設置頁數文字位置
        self.pagetext.move(0, 4)
        # 上一頁按鈕
        self.upico: MyIco = MyIco(
            '灰色翻頁上一頁', '藍色翻頁上一頁', state=True, coordinate=(0, 0, 10, 17),
            parent=self.pageico, click=lambda: self.setpage(self.page - 1)
        )
        # 上一頁按鈕隱藏
        self.upico.hide()
        # 下一頁按鈕
        self.onico: MyIco = MyIco(
            '灰色翻頁下一頁', '藍色翻頁下一頁', state=True, coordinate=(0, 0, 10, 17),
            parent=self.pageico, click=lambda: self.setpage(self.page + 1)
        )
        # 下一頁按鈕隱藏
        self.onico.hide()
        # 設置統計容器 上方邊框 顏色
        self.setStyleSheet('Quantity{border-style:solid; border-top-width:1px; border-color:rgba(200, 200, 200, 125)}')

    # 新增到指定頁數 並且檢查 狀態
    def addallpage(self, value: int):
        # 新增到指定頁數
        while len(self.pagelist) < value:
            self._add()
        # 設定頁數上限
        self.pagemax = value
        # 設置 頁數 位置 並且顯示
        for index, page in enumerate(self.pagelist[0:value], 1):
            # 頁數顯示
            page.show()
        # 設置 多餘的 頁數 隱藏
        for page in self.pagelist[value:]:
            # 頁數隱藏
            page.hide()
        self.checkingpage()

    # 新增一個頁數 並且檢查 狀態
    def addpage(self):
        self._add()
        self.checkingpage()

    # 新增一個頁數
    def _add(self):
        # 獲取目前頁數
        index = len(self.pagelist) + 1
        # 獲取頁數
        page = Page(str(index), (16 * index, 0, 10, 18), False, self)
        # 添加置頁數列表
        self.pagelist.append(page)
        # 設定頁數上限
        self.pagemax += 1

    # 設定 下一頁 上一頁 是否需要 顯示 隱藏 and 位置 and 設定總共頁數 and 頁數容器 大小 位置
    def checkingpage(self):
        # 如果最大頁數 == 1 and 頁數容器顯示 則頁數容器隱藏
        if self.pagemax == 1 and self.pageico.isVisible():
            # 頁數容器隱藏
            self.pageico.hide()
        # 如果最大頁數大於1 and 查看頁數容器是否不顯示
        elif self.pagemax > 1 and not self.pageico.isVisible():
            # 頁數容器顯示
            self.pageico.show()
            # 查看下一頁按鈕是否不顯示
            if not self.onico.isVisible():
                # 如果不顯示則顯示
                self.onico.show()
        # 查看目前頁數 是否等於 最大頁數
        elif self.pagemax == self.page:
            # 如果等於就把 下一頁按鈕隱藏
            self.onico.hide()
            # 設置全部頁數文字位置
            self.pagetext.move(self.pagelist[self.pagemax - 1].x() + 17, 3)
        # 查看目前頁數 是否不等於 最大頁數 and 是否下一頁按鈕沒有顯示
        elif self.pagemax != self.page and not self.onico.isVisible():
            # 如果不等於 and 下一頁按鈕沒有顯示  則把 下一頁按鈕顯示
            self.onico.show()
            # 設置全部頁數文字位置
            self.pagetext.move(self.onico.x() + 17, 3)
        # # 獲取最後一個頁數
        # page = self.pagelist[self.pagemax - 1]
        # 設定下一頁按鈕位置
        self.onico.move((self.pagemax * 16) + 16, 0)
        # 設置總共頁數文字
        self.pagetext.setText(f'共{self.pagemax}頁')
        # 自動調整文字大小
        self.pagetext.adjustSize()
        # 設置總共頁數文字 位置
        self.pagetext.move(self.onico.x() + 17, 3)
        # 設置頁數容器大小
        self.pageico.resize(self.pagetext.x() + self.pagetext.width(), 17)
        # 設置頁數容器位置
        self.pageico.move(int((self.width() - self.alltext.width() - 20 - self.pageico.width()) / 2),
                          int((self.height() - self.pageico.height()) / 2))

    # 設置成第幾頁
    def setpage(self, value: int, callback: bool = True) -> None:
        # 獲取頁數
        page = self.pagelist[value - 1]
        # 獲取舊的頁數按鈕
        _page = self.pagelist[self.page - 1]
        # 設定新頁數
        self.page = value
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
        self.listcheck.cls_click()
        # 垂直滾動條歸0
        self.listcheck.scrollarea.verticalcontents.setvalue(0)
        # 橫向滾動條歸0
        self.listcheck.scrollarea.hrizontalcontents.setvalue(0)
        # 刷新滾動窗口
        self.listcheck.scrollarea.refresh()
        # 查看目前頁數 是否等於 最大頁數
        if len(self.pagelist) == self.page:
            # 如果等於就把 下一頁按鈕隱藏
            self.onico.hide()
            # 設置全部頁數文字位置
            self.pagetext.move(page.x() + 17, 3)
        # 查看目前頁數 是否不等於 最大頁數 and 是否下一頁按鈕沒有顯示
        elif self.pagemax != self.page and not self.onico.isVisible():
            # 如果不等於 and 下一頁按鈕沒有顯示  則把 下一頁按鈕顯示
            self.onico.show()
            # 設置全部頁數文字位置
            self.pagetext.move(self.onico.x() + 17, 3)
        # 設定 頁數容器 寬度
        self.pageico.resize(self.pagetext.x() + self.pagetext.width(), 17)

        # 查看目前頁數 是否是 第一頁 and 上一頁按鈕是否顯示
        if self.page == 1 and self.upico.isVisible():
            # 如果是第一頁 and 上一頁按鈕顯示 則把上一頁按鈕隱藏
            self.upico.hide()
        # 查看目前頁數 是否不是 第一頁 and 上一頁按鈕是否顯示
        elif self.page != 1 and not self.upico.isVisible():
            # 如果不是是第一頁 and 上一頁按鈕沒有顯示 則把上一頁按鈕顯示
            self.upico.show()

        # 初始化目前已顯示多少text
        self.listcheck.textvalue = 0
        # 初始化當前頁數多少text
        self.listcheck.textall = self.listcheck.textsave.len()
        # 查看是否有頁數回調 and 是否能夠回調
        if self.listcheck.page_callback and callback:
            # 調用回調函數
            self.listcheck.page_callback(value)

        self.listcheck.scrollarea.refresh()

    # 設置所有總共多少項
    def all(self, value: int) -> None:
        # 設置文字
        self.alltext.setText(f'{value}項')
        # 文字自動調整大小
        self.alltext.adjustSize()
        # 文字調整位置
        self.alltext.move(self.width() - self.alltext.width() - 20,
                          int(int(self.height() - self.alltext.height()) / 2))

    # 設置已選中多少項
    def setvalue(self, value: int) -> None:
        # 設置文字
        self.alltext.setText(f'已選中{value}項')
        # 文字自動調整大小
        self.alltext.adjustSize()
        # 文字調整位置
        self.alltext.move(self.width() - self.alltext.width() - 20,
                          int(int(self.height() - self.alltext.height()) / 2))

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        # 文字調整位置
        self.alltext.move(self.width() - self.alltext.width() - 20,
                          int((self.height() - self.alltext.height()) / 2))
        self.pageico.move(int((self.width() - self.alltext.width() - 20 - self.pageico.width()) / 2),
                          int((self.height() - self.pageico.height()) / 2))


class Page(QLabel):
    def __init__(self, text: str, geometry: tuple[int, ...], state: bool, quantity: Quantity) -> None:
        super().__init__(quantity.pageico)
        # 獲取統計容器
        self.quantity: Quantity = quantity
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
        self.quantity.setpage(int(self.text()))

