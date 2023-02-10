from .module import gif, MyIco, QPoint, QFrame, QLabel, QWidget, QCursor, QMenu, QObject,\
    Qt, MyTextSave, NTextSave, QAction, math, Optional, Callable, QMouseEvent, QResizeEvent, QWheelEvent
from .MScroolBar import ScrollArea
from .NText import QText, Text


class NList(QFrame):
    def __init__(self, parent: QObject = None) -> None:
        QFrame.__init__(self, parent)
        # 設置 text 最大大小
        self.textmax: int = 39
        # 一頁上限多少個text
        self.pagemax: int = 1000
        # 底部統計 窗口 最大大小
        self.quantitymax: int = 34
        # 目前已顯示多少text
        self.textvalue: int = 0
        # 當前頁數多少text
        self.textall: int = 0
        # 設置 text 右鍵菜單
        self.contextmenu: QMenu = QMenu(self)
        # 所有 text 右鍵菜單
        self.menu: dict[str, QAction] = {}
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
        # 設置 可見窗口
        self.visualcontents = VisualContents(self)
        # 設置滾動區
        self.scrollarea: QScrollArea = QScrollArea(self.allqwidget, self, self.scrollcontents, self.visualcontents)
        # 所有text
        self.textlist: list[Text, ...] = []
        # # 儲存頁數資料
        self.textsave: List = List(self, self.pagemax)
        # 儲存所有介面的頁數資料
        self.savecontents: dict[Optional[str], List] = {None: self.textsave}
        # 設置text
        self.text = QText(self)
        # 初始化頁數
        self.addallpage(1)
        # 設置空白背景
        self.setStyleSheet('NList{background-color: rgb(255, 255, 255)}')

        # self.set_load_visible(True)
        #
        # self.textadd(ico='資料夾', text={'text': 'asaaaaaaaaaaad', 'leftclick': None, 'color': ((100, 100, 100), (100, 100, 200))})
        # self.textadd(ico='資料夾', text={'text': 'zzzzzzzzz', 'leftclick': None, 'color': None})
        # self.textadd(ico='資料夾', text={'text': 'accccccccad', 'leftclick': None, 'color': None})

        # z = QPushButton(self.scrollcontents)
        # z.resize(50, 50)
        # self.text_menu_click_connect('zzz', lambda: print('asdqweqwe'))
        #
        # self.backdrop_menu_click_connect('new', lambda: self.new('zzz'))
        # self.backdrop_menu_click_connect('qq', lambda: self.qq())
        # self.backdrop_menu_click_connect('switch', lambda: self.switch(None))

        self.resize(500, 500)


        # self.addallpage(5)
        #
        # self.page_callback = self.zz

    def zz(self, index):
        if self.textsave.len() == 0:
            self.textadd(ico='資料夾', text={'text': 'uuuuuuuuu', 'leftclick': None, 'color': None})
            self.textadd(ico='資料夾', text={'text': 'ooooooooz', 'leftclick': None, 'color': ((100, 200, 100), (100, 100, 200))})
            self.textadd(ico='資料夾',
                         text={'text': 'appppppcad', 'leftclick': None, 'color': None})

    def qq(self):
        self.textadd(ico='資料夾', text={'text': 'uuuuuuuuu', 'leftclick': None, 'color': None})
        self.textadd(ico='資料夾', text={'text': 'ooooooooz', 'leftclick': None, 'color': None})
        self.textadd(ico='資料夾', text={'text': 'appppppcad', 'leftclick': None, 'color': ((100, 100, 100), (100, 100, 200))})

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
        # 設置新的頁數資料
        self.textsave = self.savecontents[name]
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
            text: MyTextSave,
            data: any = None,
            ico: Optional[str] = None,
            leftclick: Optional[list[Callable, ...]] = None,
            doubleclick: Optional[list[Callable, ...]] = None
    ) -> None:

        textsave: NTextSave = {
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
    def textadds(self, text: list[NTextSave, ...]) -> None:
        for save in text:
            self.textsave.append(save)
            self.textall += 1
        self.scrollarea.textrefresh()

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

    # 設置 加載GIF 顯示 or 隱藏
    def set_load_visible(self, visible: bool) -> None:
        if visible:
            self.visualcontents.load.raise_()
        self.visualcontents.load.setVisible(visible)

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
        self.scrollarea.resize(self.width(), self.allqwidget.height() - self.quantitymax)
        self.scrollcontents.resize(self.width() - 2, self.scrollcontents.height())
        self.quantity.setGeometry(
            0, self.allqwidget.height() - self.quantitymax,
            self.allqwidget.width(), self.quantitymax
        )
        for text in self.textlist:
            text.resize(self.width() - 2, text.height())


class List:
    def __init__(self, nlist: NList, _max: int) -> None:
        self.nlist: NList = nlist
        # 所有 text 資料
        self._text: dict[int, list[NTextSave, ...]] = {1: []}
        # 一頁顯示多少個
        self._max: int = _max

    # 初始化資料
    def cls(self):
        # 初始化 所有 text 資料
        self._text.clear()
        # 設置新數值
        self._text[1] = []

    # 設置最大頁數
    def addallpage(self, index: int) -> None:
        for value in range(len(self._text) + 1, index + 1):
            # 設置最大頁數
            self._text[value] = []

    # 新增新text資料
    def append(self, value: NTextSave) -> None:
        # 新增 text 資料
        self._text[self.nlist.quantity.page].append(value)

    # dict[key]
    def __getitem__(self, index: int) -> NTextSave:
        return self._text[self.nlist.quantity.page][index]

    def len(self) -> int:
        return len(self._text[self.nlist.quantity.page])

    # 獲取目前頁數
    def __len__(self) -> int:
        return len(self._text)


# 可視窗口容器
class VisualContents(QFrame):
    def __init__(self, nlist: NList) -> None:
        super().__init__()
        self.nlis: NList = nlist
        # 設定等待GIF
        self.load = gif(self, '加載')
        # 設置 GIF 大小
        self.load.resize(20, 20)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.load.move(
            int((self.width() - self.load.width()) / 2),
            int((self.height() - self.load.height()) / 2)
        )


# 內容窗口
class ScrollContents(QFrame):
    def __init__(self, nlist: NList) -> None:
        super().__init__()
        self.nlist: NList = nlist
        # 禁止傳遞事件給父代  為了防止背景右鍵菜單傳遞
        self.setAttribute(Qt.WA_NoMousePropagation, True)

    # 滾輪事件
    def wheelEvent(self, event: QWheelEvent) -> None:
        # 因為禁止傳遞給父代  所以滾輪事件無法傳遞  所以手動傳遞滾輪事件
        self.nlist.scrollarea.wheelEvent(event)
        self.nlist.allqwidget.wheelEvent(event)


class AllQWidget(QWidget):
    def __init__(self, parent: NList):
        super().__init__(parent)
        self.nlist: NList = parent
        # 內容窗口初始座標
        self.titlesize = QPoint(1, 1)
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
            if self.nlist.backdrop_menu_callback:
                self.nlist.backdrop_menu_callback(lambda: self.contextmenu.popup(QCursor.pos()))
            else:
                self.contextmenu.popup(QCursor.pos())


# 滾動區
class QScrollArea(ScrollArea):
    def __init__(self, parent: QObject, nlist: NList, scrollcontents: ScrollContents, visualcontents: VisualContents):
        super().__init__(parent, scrollcontents=scrollcontents, visualcontents=visualcontents)
        self.nlist: NList = nlist

    def textrefresh(self):
        _max = math.ceil((abs(self.scrollcontents.y()) + self.visualcontents.height()) / self.nlist.textmax) + 1
        for index in range(self.nlist.textvalue, _max):
            if index < self.nlist.textall:
                self.nlist.textlist[index].refresh()
                self.nlist.textvalue += 1
            else:
                break
        # 設置內容容器大小
        self.nlist.scrollcontents.resize(
            self.nlist.scrollcontents.width(),
            self.nlist.textall * self.nlist.textmax
        )

    # 滾動條移動回調
    def scrollcontentsby(self, dx: int, dy: int) -> None:
        # 刷新 text數據
        self.textrefresh()


# 統計容器
class Quantity(QFrame):
    def __init__(self, parent: AllQWidget, nlist: NList):
        super().__init__(parent)
        self.nlist: NList = nlist
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
        # 垂直滾動條歸0
        self.nlist.scrollarea.verticalcontents.setvalue(0)
        # 橫向滾動條歸0
        self.nlist.scrollarea.hrizontalcontents.setvalue(0)
        # 刷新滾動窗口
        self.nlist.scrollarea.refresh()
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
        self.nlist.textvalue = 0
        # 初始化當前頁數多少text
        self.nlist.textall = self.nlist.textsave.len()
        # 查看是否有頁數回調 and 是否能夠回調
        if self.nlist.page_callback and callback:
            # 調用回調函數
            self.nlist.page_callback(value)

        self.nlist.scrollarea.refresh()

    # 設置所有總共多少項
    def all(self, value: int) -> None:
        # 設置文字
        self.alltext.setText(f'{value}項')
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
