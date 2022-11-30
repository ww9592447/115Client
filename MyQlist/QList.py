from .package import QFrame, QWidget, QApplication, sys, pyqtSignal, Qt, QPoint, QPainter, QPen, QColor,\
    gif, QCursor, QMenu, QLabel, MyIco

from asyncio import sleep, set_event_loop
from qasync import QEventLoop
from .MScroolBar import ScrollArea
from .QTitle import QTitle
from .QText import QText


class Page(QLabel):
    def __init__(self, text, geometry, status, parent):
        super().__init__(parent)
        self.setText(text)
        self.setGeometry(*geometry)
        self.setAlignment(Qt.AlignCenter)
        if not status:
            self.setCursor(Qt.PointingHandCursor)
        self.setProperty('status', status)
        self.setStyleSheet('Page{color:rgb(153, 153, 171);}'
                           'Page:hover{color:rgb(6,168,255);}'
                           'Page[status="true"]{color:rgb(6,168,255);}')
        self.show()

    # 單擊
    def mousePressEvent(self, event):
        index = self.parent().parent().pagelist.index(self)
        self.parent().parent().setpage(index)


# 統計容器
class Quantity(QFrame):
    def __init__(self, parent, listcheck):
        super().__init__(parent)
        self.listcheck = listcheck
        # 紀錄頁數
        self.page = 0
        # 設置文字容器
        self.alltext = QLabel(self)
        # 設置文字顏色
        self.alltext.setStyleSheet('color:rgb(153, 153, 171)')
        # 設定預設文字
        self.alltext.setText('0項')
        # 自動調整成符合大小
        self.alltext.adjustSize()
        # 所有頁數容器
        self.pageico = QFrame(self)
        # 所有容器隱藏
        self.pageico.hide()
        # 頁數列表 並且新增第一頁
        self.pagelist = [Page('1', (16, 0, 10, 18), True, self.pageico)]
        # 設置第一頁不可用
        self.pagelist[0].setEnabled(False)
        # 設置頁數文字容器
        self.pagetext = QLabel(self.pageico)
        # 設置頁數文字顏色
        self.pagetext.setStyleSheet('color:rgb(153, 153, 171)')
        # 設置頁數文字位置
        self.pagetext.move(0, 4)
        # 上一頁按鈕
        self.upico = MyIco('灰色翻頁上一頁', '藍色翻頁上一頁', state=True, coordinate=(0, 0, 10, 17), parent=self.pageico,
                           click=lambda: self.setpage(self.listcheck.page - 1))

        # 上一頁按鈕隱藏
        self.upico.hide()
        # 下一頁按鈕
        self.onico = MyIco('灰色翻頁下一頁', '藍色翻頁下一頁', state=True, coordinate=(0, 0, 10, 17), parent=self.pageico,
                           click=lambda: self.setpage(self.listcheck.page + 1))
        # 下一頁按鈕隱藏
        self.onico.hide()
        # 設置統計容器 上方邊框 顏色
        self.setStyleSheet('Quantity{border-style:solid; border-top-width:1px; border-color:rgba(200, 200, 200, 125)}')

    # 提前設置頁數
    def advance(self, value):
        # 新增到指定頁數
        while len(self.pagelist) < value:
            self.add()

    def add(self):
        # 查看頁數容器是否不顯示
        if not self.pageico.isVisible():
            # 如果不顯示則顯示
            self.pageico.show()
        # 查看下一頁按鈕是否不顯示
        if not self.onico.isVisible():
            # 如果不顯示則顯示
            self.onico.show()

        index = len(self.pagelist)
        # 所有text容器
        self.listcheck.alllist.append([])
        # 所有右鍵
        self.listcheck.menu.append({})
        # 所有內容窗口容器
        self.listcheck.scrollcontents.append(ScrollContents(self.listcheck))
        index += 1
        self.pagetext.setText(f'共{index}頁')
        self.pagetext.adjustSize()
        page = Page(str(index), (16 * index, 0, 10, 18), False, self.pageico)
        self.pagelist.append(page)
        self.onico.move(page.x() + 16, 0)
        self.pagetext.move(self.onico.x() + 17, 3)
        self.pageico.resize(self.pagetext.x() + self.pagetext.width(), 17)
        self.pageico.move(int((self.width() - self.alltext.width() - 20 - self.pageico.width()) / 2),
                          int((self.height() - self.pageico.height()) / 2))

    # 設置成第幾頁
    def setpage(self, value, callback=True):
        page = self.pagelist[value]
        # 獲取舊的頁數按鈕
        _page = self.pagelist[self.listcheck.page]
        # 設定舊的頁數按鈕成可以互動的狀態
        _page.setProperty('status', False)
        # 設定新的頁數按鈕成不能互動的狀態
        page.setProperty('status', True)
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

        self.listcheck.cls_click()
        self.listcheck.scrollarea.verticalcontents.setvalue(0)
        self.listcheck.scrollarea.hrizontalcontents.setvalue(0)
        width = self.listcheck.scrollcontents[self.listcheck.page].width()
        self.listcheck.page = value
        self.page = value
        scrollcontents = self.listcheck.scrollcontents[self.listcheck.page]
        self.listcheck.scrollarea.setwidget(scrollcontents)
        scrollcontents.resize(width, len(self.listcheck.alllist[self.listcheck.page]) * self.listcheck.textmax)
        self.listcheck.scrollarea.refresh()
        for texts in scrollcontents.children():
            texts.refresh()

        self.all(len(self.listcheck.alllist[self.listcheck.page]))

        # 查看目前頁數 是否等於 最大頁數
        if len(self.pagelist) == self.listcheck.page + 1:
            # 如果等於就把 下一頁按鈕隱藏
            self.onico.hide()
            # 設置全部頁數文字位置
            self.pagetext.move(page.x() + 17, 3)
        # 查看目前頁數 是否不等於 最大頁數 and 是否下一頁按鈕沒有顯示
        elif len(self.pagelist) != self.listcheck.page + 1 and not self.onico.isVisible():
            # 如果不等於 and 下一頁按鈕沒有顯示  則把 下一頁按鈕顯示
            self.onico.show()
            # 設置全部頁數文字位置
            self.pagetext.move(self.onico.x() + 17, 3)
        self.pageico.resize(self.pagetext.x() + self.pagetext.width(), 17)
        # 查看目前頁數 是否是 第一頁 and 上一頁按鈕是否顯示
        if self.listcheck.page == 0 and self.upico.isVisible():
            # 如果是第一頁 and 上一頁按鈕顯示 則把上一頁按鈕隱藏
            self.upico.hide()
        # 查看目前頁數 是否不是 第一頁 and 上一頁按鈕是否顯示
        elif self.listcheck.page != 0 and not self.upico.isVisible():
            # 如果不是是第一頁 and 上一頁按鈕沒有顯示 則把上一頁按鈕顯示
            self.upico.show()
        # 查看是否有頁數回調 and 是否能夠回調
        if self.listcheck.page_callback and callback:
            # 調用回調函數
            self.listcheck.page_callback(value)

    # 設置所有總共多少項
    def all(self, value):
        # 設置文字
        self.alltext.setText(f'{value}項')
        # 文字自動調整大小
        self.alltext.adjustSize()
        # 文字調整位置
        self.alltext.move(self.width() - self.alltext.width() - 20,
                          int(int(self.height() - self.alltext.height()) / 2))

    # 設置已選中多少項
    def setvalue(self, value):
        # 設置文字
        self.alltext.setText(f'已選中{value}項')
        # 文字自動調整大小
        self.alltext.adjustSize()
        # 文字調整位置
        self.alltext.move(self.width() - self.alltext.width() - 20,
                          int(int(self.height() - self.alltext.height()) / 2))

    def resizeEvent(self, event):
        # 文字調整位置
        self.alltext.move(self.width() - self.alltext.width() - 20,
                          int((self.height() - self.alltext.height()) / 2))
        self.pageico.move(int((self.width() - self.alltext.width() - 20 - self.pageico.width()) / 2),
                          int((self.height() - self.pageico.height()) / 2))


# 內容窗口
class ScrollContents(QFrame):
    def __init__(self, listcheck):
        super().__init__()
        self.listcheck = listcheck
        # 禁止傳遞事件給父代  為了防止背景右鍵菜單傳遞
        self.setAttribute(Qt.WA_NoMousePropagation, True)

    # 滾輪事件
    def wheelEvent(self, event):
        # 因為禁止傳遞給父代  所以滾輪事件無法傳遞  所以手動傳遞滾輪事件
        self.listcheck.scrollarea.wheelEvent(event)
        self.listcheck.allqwidget.wheelEvent(event)
        # event.ignore()

    def resizeEvent(self, event):
        if event.oldSize().width() != event.size().width():
            # 讓所有的 texts 保持跟 內容窗口相同寬度
            for texts in self.listcheck.alllist[self.listcheck.page]:
                texts.resize(self.width(), texts.height())


# 滾動區
class QScrollArea(ScrollArea):
    def __init__(self, parent, listcheck, scrollcontents, visualcontents):
        super().__init__(parent, scrollcontents=scrollcontents, visualcontents=visualcontents)
        self.listcheck = listcheck

    def scrollContentsBy(self, dx, dy):
        self.listcheck.title.move(self.listcheck.title.x() + dx, 0)
        bottom = self.listcheck.title.x() + self.listcheck.title.width()
        self.listcheck.title.resize(
            1 + self.listcheck.title.width() + (self.listcheck.width() - bottom),
            self.listcheck.titlemax
        )


# 可拖曳窗口 等待gui
class Select(QFrame):
    def __init__(self, parent):
        super(Select, self).__init__(parent)
        self.listcheck = parent
        # 設置滑鼠穿透
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        # 初始化矩形座標
        self.rect = [0, 0, 0, 0]
        # self.setStyleSheet('Select{background-color: rgb(255, 255, 255)}')
        # 設定等待GIF
        self.load = gif(self, '加載')
        # 設置 GIF 大小
        self.load.resize(20, 20)

    def sethide(self):
        # 設置滑鼠穿透
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet('')

    def setshow(self):
        # 關閉滑鼠穿透
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet('Select{background-color: rgb(255, 255, 255)}')

    # 加載GIF隱藏
    def loadhide(self):
        self.load.hide()

    # 加載GIF顯示
    def loadshow(self):
        self.load.raise_()
        self.load.show()

    def update_(self, rect):
        self.rect = rect
        self.update()

    def paintEvent(self, event):
        # 初始化繪圖工具
        qp = QPainter()
        # 開始在窗口繪製
        qp.begin(self)
        # 自定義畫筆方法
        if self.rect != [0, 0, 0, 0]:
            self.drawrect(qp)
        # 結束在窗口的繪製
        qp.end()

    def drawrect(self, qp):
        # 獲得 畫筆 顏色 大小
        pen = QPen(QColor(6, 168, 255, 255), 1)
        # 設定 畫筆 顏色 大小
        qp.setPen(pen)
        # 畫出矩形
        qp.drawRect(*self.rect)
        # 為矩形內容上色
        qp.fillRect(*self.rect, QColor(6, 168, 255, 128))

    def resizeEvent(self, event):
        self.load.move(
            int((self.width() - self.load.width()) / 2),
            int((self.height() - self.load.height()) / 2)
        )


class AllQWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        # 內容窗口初始座標
        self.titlesize = QPoint(1, self.parent().titlemax + 1)
        # 初始化矩形座標
        self.rect = [0, 0, 0, 0]
        # 保存第一次點擊Y座標
        self._y = 0
        # 保存內容窗口移動Y座標
        self.by = 0
        # 右鍵菜單
        self.contextMenu = None

    # 背景右鍵菜單事件
    def menuclick(self, text, slot, mode=True):
        # 在右鍵位置顯示
        def display():
            # 是否有背景右鍵回調
            if self.parent().backdrop_menu_callback:
                self.parent().backdrop_menu_callback(lambda: self.contextMenu.popup(QCursor.pos()))
            else:
                # 查看是否右鍵是否隱藏  如果全部隱藏 則不顯示右鍵
                for _, values in self.parent().backdrop_menu.items():
                    for _, _values in values.items():
                        if _values.isVisible():
                            self.contextMenu.popup(QCursor.pos())
                            return

        # 如果沒有QMenu信號事件 創建QMenu信號事件
        if self.contextMenu is None:
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(display)
            self.contextMenu = QMenu(self)

        cp = self.contextMenu.addAction(text)
        cp.triggered.connect(slot)
        cp.setVisible(mode)

        if self not in self.parent().backdrop_menu:
            self.parent().backdrop_menu[self] = {text: cp}
        else:
            self.parent().backdrop_menu[self].update({text: cp})

    # 滑鼠單擊
    def mousePressEvent(self, event):
        # 清空所有已點擊
        self.parent().cls_click()
        # 獲取窗口相對座標
        pos = event.pos() - self.titlesize
        # 查看相對座標 是否 不是負數 and 左鍵點擊
        if pos.x() > 0 < pos.y() and event.buttons() == Qt.LeftButton:
            # 獲取當前頁數內容窗口
            scrollcontents = self.parent().scrollcontents[self.parent().page]
            # 設定第一次點擊 內容窗口y相對座標
            self._y = pos.y() - scrollcontents.y()
            # 設定內容窗口移動Y座標
            self.by = scrollcontents.y()
            # 設定矩形座標
            self.rect[0] = pos.x()
            # 設定矩形座標
            self.rect[1] = pos.y()

    # 滑鼠鬆開
    def mouseReleaseEvent(self, event):
        # 還原矩形座標
        self.rect = [0, 0, 0, 0]
        # 刷新矩形
        self.parent().select.update_(self.rect)

    # 滾輪
    def wheelEvent(self, event):
        if self.rect != [0, 0, 0, 0]:
            # 獲取當前頁數內容窗口
            scrollcontents = self.parent().scrollcontents[self.parent().page]
            # 獲取內容窗口移動多少
            y = abs(self.by - scrollcontents.y())
            # 設置新內容窗口y座標
            self.by = scrollcontents.y()
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
    def mouseMoveEvent(self, event):
        if self.rect[0:2] != [0, 0]:
            # 獲取窗口相對座標
            pos = event.pos() - self.titlesize
            # 設定矩形要多大
            self.rect[2] = pos.x() - self.rect[0]
            self.rect[3] = pos.y() - self.rect[1]
            # 設定刷新矩形相關資料
            self.setupdate(pos)

    # 設定刷新矩形相關資料
    def setupdate(self, pos):
        # 獲取當前頁數內容窗口
        scrollcontents = self.parent().scrollcontents[self.parent().page]
        # 刷新矩形
        self.parent().select.update_(self.rect)
        # 獲取第一次點擊內容窗口y座標, 目前內容窗口y相對座標
        y = [self._y, pos.y() - scrollcontents .y()]
        # 排序相對座標
        y.sort()
        # 查看最小相對y座標是否大於 內容窗口大小  小於0
        if scrollcontents.height() >= y[0] >= 0:
            # 獲取 最低相對座標 在哪個texys上面
            _min = int(y[0] / self.parent().textmax)
            # 獲取目前頁數所有texts
            alllist = self.parent().alllist[self.parent().page]
            # 獲取 最高相對座標 在哪個texts上面
            if (_max := len(alllist)) > int(y[1] / self.parent().textmax):
                _max = int(y[1] / self.parent().textmax) + 1
            # 獲取最低到最高的迭代器
            select = alllist[_min: _max]
            # 開始循環迭代器
            for texts in select:
                # 查看index 是否在 以點擊裡面
                if texts not in self.parent().currentclick:
                    # 不在就 index 變成已點擊
                    texts.setstatus()
            # 查看迭代器 是否空白
            if select:
                # 設定最後一次點擊
                self.parent().firstclick = texts
            # 查看所有已點擊的 是否有多餘的
            for texts in set(self.parent().currentclick) ^ set(select):
                # 多餘的點擊取消
                texts.setstatus()


# 可視窗口容器
class VisualContents(QFrame):
    def __init__(self, listcheck):
        super().__init__()
        self.listcheck = listcheck

    def resizeEvent(self, event):
        self.listcheck.select.resize(self.size())


# 所有點擊
class Currentclick(list):
    def __init__(self, listcheck):
        super().__init__()
        self.listcheck = listcheck

    def append(self, __object):
        super().append(__object)
        value = len(self)
        self.listcheck.quantity.setvalue(value)
        if value == len(self.listcheck.scrollcontents[self.listcheck.page].children()):
            self.listcheck.title.clickqlabel.setstatus(True)

    def remove(self, __value):
        super().remove(__value)
        if len(self) == 0:
            self.listcheck.quantity.all(len(self.listcheck.scrollcontents[self.listcheck.page].children()))
        else:
            self.listcheck.quantity.setvalue(len(self))
        if self.listcheck.title.clickqlabel.status:
            self.listcheck.title.clickqlabel.setstatus(False)


class ListCheck(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        # 設置空白背景
        self.setStyleSheet('ListCheck{background-color: rgb(255, 255, 255)}')
        # 設置文字 窗口 最大大小
        self.textmax = 39
        # 設置標題 窗口 最大大小
        self.titlemax = 31
        # 一頁上限多少個text
        self.pagemax = 1000
        # 底部統計 窗口 最大大小
        self.quantitymax = 34
        # 設置標題移動條可觸碰大小
        self.titllinesize = 7
        # 文字離 複選紐 間隔多遠
        self.checkbuttoninterval = 5
        # 設置標題離左邊框多遠
        self.titleinterval = 3
        # texts最後一次點擊
        self.firstclick = None
        # 保存紀錄 方便可以隨時更換之前的列表
        self.save = {}
        # 全局點擊信號
        # 如果設定全局點擊信號 如果有新建的texts 會讀取這個列表進行初始化
        self.click_connect = []
        # 所有右鍵菜單
        self.menu = [{}]
        # 所有背景菜單
        self.backdrop_menu = {}
        # 右鍵回調
        self.menu_callback = None
        # 背景右鍵回調
        self.backdrop_menu_callback = None
        # 換頁回調
        self.page_callback = None
        # 所有標題
        self.alltitle = []
        # 目前所有複選紐點擊
        self.currentclick = Currentclick(self)
        # 複選紐 手動調整可觸碰大小
        self.touchable = None
        # 目前排序
        self.stop = None
        # 目前第幾頁
        self.page = 0
        # 所有容器
        self.allqwidget = AllQWidget(self)
        # 所有text容器
        self.alllist = [[]]
        # 所有內容窗口容器
        self.scrollcontents = [ScrollContents(self)]
        # 設置統計容器
        self.quantity = Quantity(self.allqwidget, self)
        # 設置滾動區
        self.scrollarea = QScrollArea(self.allqwidget, self, self.scrollcontents[0], VisualContents(self))
        # 移動滾動區到標題之下
        self.scrollarea.move(0, self.titlemax)
        # 可拖曳窗口 等待gui
        self.select = Select(self.allqwidget)
        # 移動位置跟內容窗口等同位置
        self.select.move(1, self.titlemax + 1)
        # 設置標題
        self.title = QTitle(self.allqwidget, self)
        # 設置文字
        self.text = QText(self)

        # self.page_advance(6)
        #
        # self.title_add('標題')
        # self.text_add({'標題': 'bbbbbbbbbbb'})
        # self.text_add({'標題': 'uuuuuuuuuuuuuuuuuu'}, index=4)
        # self.text_add({'標題': 'bbbbbbbbbbb'})
        # self.text_add({'標題': 'bbbbbbbbbbb'})
        # self.text_add({'標題': '1bbbbbbbbbb'})
        #
        # self.text_add({'標題': 'bbbbbbbbbbb'})
        # self.text_add({'標題': '2bbbbbbbbbb'})
        # self.text_add({'標題': 'bbbbbbbbbbb'})
        # self.text_add({'標題': 'bbbbbbbbbbb'})
        # self.text_add({'標題': '3bbbbbbbbbb'})
        # self.text_add({'標題': '4bbbbbbbbbb'})
        # self.text_add({'標題': 'bbbbbbbbbbb'})
        # self.text_add({'標題': '1111111111'})
        # self.text_insert(0, {'標題': '0000000000'})

    # 提前設置頁數
    def page_advance(self, value):
        self.quantity.advance(value)

    # 更換新的窗口
    def new_contents(self):
        self.cls_click()
        if self.quantity:
            self.quantity.hide()
        self.quantity = Quantity(self.allqwidget, self)
        self.quantity.show()
        self.quantity.setGeometry(0, self.allqwidget.height() - self.quantitymax, self.allqwidget.width(),
                                  self.quantitymax)
        # 所有text容器
        self.alllist = [[]]
        self.page = 0
        scrollcontents = ScrollContents(self)
        # 所有內容窗口容器
        self.scrollcontents = [scrollcontents]
        self.scrollarea.setwidget(scrollcontents)
        name = self.alltitle[-1]
        title = name.data[0]
        scrollcontents.resize(title.x() + title.width(), 0)

    # 儲存目前資料
    def save_contents(self, name):
        alltitle = {}
        for _name in self.alltitle:
            title = _name.data[0]
            line = _name.data[1]
            alltitle[_name] = {'width': title.width(), 'least': line.least, 'slot': _name.data[2]}
        self.save[name] = {
            'quantity': self.quantity, 'alltitle': alltitle,
            'alllist': self.alllist, 'scrollcontents': self.scrollcontents,
            'menu': self.menu
        }

    # 更換 成舊資料
    def replace_contents(self, new):
        self.cls_click()
        self.scrollarea.verticalcontents.setvalue(0)
        self.scrollarea.hrizontalcontents.setvalue(0)
        if self.quantity:
            self.quantity.hide()
        width = self.scrollcontents[self.page].width()
        self.quantity = self.save[new]['quantity']
        self.quantity.show()
        self.quantity.setGeometry(0, self.allqwidget.height() - self.quantitymax, self.allqwidget.width(),
                                  self.quantitymax)
        self.page = self.quantity.page
        self.alllist = self.save[new]['alllist']
        self.scrollcontents = self.save[new]['scrollcontents']
        scrollcontents = self.scrollcontents[self.page]
        self.scrollarea.setwidget(scrollcontents)
        scrollcontents.resize(width, scrollcontents.height())
        self.scrollarea.refresh()
        title = self.save[new]['alltitle']

        for name in set(title.keys()) ^ set(self.alltitle):
            if name in title:
                index = list(title).index(name)
                self.title.insert(index, name, title[name]['width'], title[name]['least'])
            else:
                self.title.delete(name)
        for texts in self.alllist[self.page]:
            texts.refresh()
        self.quantity.show()

    # 刪除舊容器
    def delete_old_contents(self, name):
        quantity = self.save[name]['quantity']
        if self.quantity == quantity:
            for scrollcontents in self.scrollcontents:
                scrollcontents.setParent(None)
                scrollcontents.deleteLater()
            self.quantity = None
            self.scrollarea.scrollcontents = None
            self.alllist = None
            self.scrollcontents = None

        quantity.setParent(None)
        quantity.deleteLater()
        del self.save[name]

    # 刪除目前容器
    def delete_contents(self):
        self.quantity.setParent(None)
        self.quantity.deleteLater()
        for scrollcontents in self.scrollcontents:
            scrollcontents.setParent(None)
            scrollcontents.deleteLater()
        self.quantity = None
        self.scrollarea.scrollcontents = None
        self.alllist = None
        self.scrollcontents = None

    # text 添加
    def text_add(self, text, index=None, data=None, ico=None, my_mode=None, text_mode=None):
        self.text.add(text, index=index, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode)

    # 插入
    def text_insert(self, index, text, data=None, ico=None, my_mode=None, text_mode=None):
        self.text.insert(index, text, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode)

    # 標籤添加
    def title_add(self, text, width=50, least=50):
        self.title.add(text, width, least)

    # 標籤添加
    def title_insert(self, index, text, width=50, least=50):
        self.title.insert(index, text, width, least)

    # 批量添加文字
    async def text_adds(self, texts, index=None, datas=None, icos=None, my_modes=None, text_modes=None):
        if datas:
            if len(datas) != len(texts):
                raise Exception("data數量不對")
        if icos == list:
            if len(icos) != len(texts):
                raise Exception("ico數量不對")

        for text, _index in zip(texts, range(1, len(texts) + 1)):
            data = datas if datas is None else datas[_index - 1]
            ico = icos if icos is None else icos[_index - 1]
            my_mode = my_modes if my_modes is None else my_modes[_index - 1]
            text_mode = text_modes if text_modes is None else text_modes[_index - 1]
            self.text_add(text, index=index, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode)
            if _index % 200 == 0:
                await sleep(0.1)

    def content_show(self):
        self.select.setshow()
        self.scrollarea.setvertical(False)

    def content_hide(self):
        self.select.sethide()
        self.scrollarea.setvertical(True)

    # 返回指定data or 已點擊texts data
    def extra(self, index=None):
        if index is not None:
            return self.alllist[self.page][index].data
        if (index := self.now_all()) == 0:
            return None
        data = []
        for texts in index:
            data.append(texts.data)
        if len(data) == 1:
            return data[0]
        else:
            return data

    # 目前所有點擊
    def now_all(self):
        return self.currentclick

    # 加載GIF隱藏
    def load_hide(self):
        self.select.loadhide()

    # 加載GIF顯示
    def load_show(self):
        self.select.loadshow()

    # 清空所有點擊
    def cls_click(self):
        for texts in self.currentclick.copy():
            texts.setstatus()

    # 設定 vbox 可觸碰大小
    def settouchable(self, resize):
        self.touchable = resize

    # 背景右鍵 菜單
    def backdrop_menu_click_connect(self, text, slot, mode=True):
        self.allqwidget.menuclick(text, slot, mode)

    # 連結texts槽 左鍵單擊
    def texts_left_click_connect(self, slot):
        self.click_connect.append(('texts', 'leftclick', slot))
        for texts in sum(self.alllist, []):
            texts.leftclick.connect(slot)

    # 連結texts槽 右鍵單擊
    def texts_right_click_connect(self, slot):
        self.click_connect.append(('texts', 'rightclick', slot))
        for texts in sum(self.alllist, []):
            texts.rightclick.connect(slot)

    # 連結texts槽 雙擊
    def texts_double_click_connect(self, slot):
        self.click_connect.append(('texts', 'doubleclick', slot))
        for texts in sum(self.alllist, []):
            texts.doubleclick.connect(slot)

    # 連結右鍵 菜單
    def texts_menu_click_connect(self, text, slot, mode=True):
        self.click_connect.append(('menu', 'menuclick', text, slot))
        for texts in sum(self.alllist, []):
            texts.menuclick(text, slot, mode)

    # 顯示右鍵菜單
    def menu_show(self, text, index=None):
        if not index:
            for key in self.menu[self.listcheck.page].keys():
                self.menu[key][text].setVisible(True)
        else:
            self.menu[self.listcheck.page][self.alllist[self.page][index]][text].setVisible(True)

    # 隱藏右鍵菜單
    def menu_hide(self, text, index=None):
        if not index:
            for key in self.menu[self.listcheck.page].keys():
                self.menu[self.listcheck.page][key][text].setVisible(False)
        else:
            self.menu[self.listcheck.page][self.alllist[self.page][index]][text].setVisible(False)

    # 顯示背景右鍵菜單
    def backdrop_menu_show(self, text):
        _backdrop = list(self.backdrop_menu.keys())[0]
        self.backdrop_menu[_backdrop][text].setVisible(True)

    # 隱藏背景右鍵菜單
    def backdrop_menu_hide(self, text):
        _backdrop = list(self.backdrop_menu.keys())[0]
        self.backdrop_menu[_backdrop][text].setVisible(False)

    # 刪除標題
    def delete_title(self, name):
        self.title.delete(name)

    def resizeEvent(self, event):
        self.allqwidget.resize(
            self.width(),
            self.height() - self.allqwidget.y()
        )
        bottom = self.title.x() + self.title.width()
        self.title.resize(1 + self.title.width() + (self.width() - bottom), self.titlemax)
        self.scrollarea.resize(self.allqwidget.width(), self.allqwidget.height() - self.titlemax - self.quantitymax)
        self.quantity.setGeometry(
            0, self.allqwidget.height() - self.quantitymax,
            self.allqwidget.width(), self.quantitymax
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    set_event_loop(loop)
    ex = ListCheck()
    ex.show()
    with loop:
        loop.run_forever()
