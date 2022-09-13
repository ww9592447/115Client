from .package import gif, MyIco, QPoint, QFrame, QLabel, QWidget, QCursor, QMenu, Qt
from MScroolBar import ScrollArea
from .NText import QText
from asyncio import sleep


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

        self.listcheck.scrollarea.verticalcontents.setvalue(0)
        self.listcheck.scrollarea.hrizontalcontents.setvalue(0)
        width = self.listcheck.scrollcontents[self.listcheck.page].width()
        self.listcheck.page = value
        self.page = value
        scrollcontents = self.listcheck.scrollcontents[self.listcheck.page]
        self.listcheck.scrollarea.setwidget(scrollcontents)
        scrollcontents.resize(width, len(self.listcheck.alllist[self.listcheck.page]) * self.listcheck.textmax)
        self.listcheck.scrollarea.refresh()
        # for texts in scrollcontents.children():
        #     texts.refresh()
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


class AllQWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        # 內容窗口初始座標
        self.titlesize = QPoint(1, 1)
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

    def resizeEvent(self, event):
        if event.oldSize().width() != event.size().width():
            # 讓所有的 texts 保持跟 內容窗口相同寬度
            for texts in self.listcheck.alllist[self.listcheck.page]:
                texts.resize(self.width(), texts.height())


class NList(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        # 設置空白背景
        self.setStyleSheet('NList{background-color: rgb(255, 255, 255)}')
        # 設置文字 窗口 最大大小
        self.textmax = 39
        # 一頁上限多少個text
        self.pagemax = 1000
        # 底部統計 窗口 最大大小
        self.quantitymax = 34
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
        # 目前第幾頁
        self.page = 0
        # 所有容器
        self.allqwidget = AllQWidget(self)
        # 所有text容器
        self.alllist = [[]]
        # 所有內容窗口容器
        self.scrollcontents = [ScrollContents(self)]
        # 初始化內容容器大小
        self.scrollcontents[0].resize(0, 0)
        # 設置統計容器
        self.quantity = Quantity(self.allqwidget, self)
        # 設置滾動區
        self.scrollarea = ScrollArea(self.allqwidget, scrollcontents=self.scrollcontents[0])
        # 設置文字
        self.text = QText(self)
        # 設定等待GIF
        self.load = gif(self.allqwidget, '加載')
        # 設置 GIF 大小
        self.load.resize(20, 20)

        # text_mode = {'leftclick': [lambda: print('fffff')]}
        # my_mode = {'leftclick': [lambda: print('fffff')], 'cursor': True}
        #
        # # text_mode = {'leftclick': [slot], 'color': ((0, 0, 0), (6, 168, 255))}} if ico == '資料夾' else None
        #
        # self.text.add('asssssssssssssssssd', ico='資料夾', my_mode=my_mode, text_mode=text_mode)

    def page_advance(self, value):
        self.quantity.advance(value)

    # text 添加
    def text_add(self, text, index=None, data=None, ico=None, my_mode=None, text_mode=None):
        self.text.add(text, index=index, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode)

    # 插入
    def text_insert(self, index, text, data=None, ico=None, my_mode=None, text_mode=None):
        self.text.insert(index, text, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode)

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

    # 更換新的窗口
    def new_contents(self):
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
        scrollcontents.resize(self.width() - 2, 0)

    # 儲存目前資料
    def save_contents(self, name):
        self.save[name] = {
            'quantity': self.quantity,'alllist': self.alllist,
            'scrollcontents': self.scrollcontents,'menu': self.menu
        }

    # 更換 成舊資料
    def replace_contents(self, new):
        self.scrollarea.verticalcontents.setvalue(0)
        self.scrollarea.hrizontalcontents.setvalue(0)
        if self.quantity:
            self.quantity.hide()
        self.quantity = self.save[new]['quantity']
        self.quantity.show()
        self.quantity.setGeometry(0, self.allqwidget.height() - self.quantitymax, self.allqwidget.width(),
                                  self.quantitymax)
        self.page = self.quantity.page
        self.alllist = self.save[new]['alllist']
        self.scrollcontents = self.save[new]['scrollcontents']
        scrollcontents = self.scrollcontents[self.page]
        self.scrollarea.setwidget(scrollcontents)
        scrollcontents.resize(self.width() - 2, scrollcontents.height())
        self.scrollarea.refresh()
        self.quantity.show()

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

    # 返回指定data or 已點擊texts data
    def extra(self, index):
        return self.alllist[self.page][index].data

    # 加載GIF隱藏
    def load_hide(self):
        self.load.hide()

    # 加載GIF顯示
    def load_show(self):
        self.load.raise_()
        self.load.show()

    def resizeEvent(self, event):
        self.allqwidget.resize(
            self.width(),
            self.height() - self.allqwidget.y()
        )
        self.scrollarea.resize(self.allqwidget.width(), self.allqwidget.height() - self.quantitymax)
        self.scrollcontents[self.page].resize(self.width() - 2, self.scrollcontents[self.page].height())
        self.quantity.setGeometry(
            0, self.allqwidget.height() - self.quantitymax,
            self.allqwidget.width(), self.quantitymax
        )
        self.load.move(
            int((self.allqwidget.width() - self.load.width() - self.quantitymax) / 2),
            int((self.allqwidget.height() - self.load.height() - self.quantitymax) / 2)
        )


if __name__ == '__main__':
    import sys
    from PyQt5.Qt import QApplication
    app = QApplication(sys.argv)
    w = NList()
    w.show()
    sys.exit(app.exec_())