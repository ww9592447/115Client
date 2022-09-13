from .package import picture, ClickQLabel, QLabel, Qt, QFrame, QFont, QCursor, MyQLabel, pyqtSignal, NewString


# 標題第一個複選紐容器
class ClickQLabelContainer(QFrame):
    def __init__(self, parent, ico, listcheck):
        super().__init__(parent)
        self.listcheck = listcheck
        # 設定未選中ico
        self.unselected = picture('複選空白')
        # 設定選中ico
        self.checked = picture('複選打勾')
        # 複選紐狀態
        self.status = False
        # 獲取圖片
        self.ico = ico
        # 設置複選按鈕
        self.checkbutton = ClickQLabel(self)
        # 複選紐連接全選 OR 未選 信號
        self.checkbutton.leftclick.connect(self._setallstatus)
        # 設置複選按鈕跟圖片大小一樣
        self.checkbutton.resize(ico.size())
        # 設置背景顏色QSS
        self.setStyleSheet('ClickQLabelContainer[backdrop="true"]{background-color: rgb(246, 248, 251)}')

    # 滑鼠單擊
    def mousePressEvent(self, event):
        # 獲取第一個標題名稱
        name = self.listcheck.alltitle[0]
        # 根據名稱獲取標題
        title = name.data[0]
        # 查看標題是否有函數需要調用
        if name.data[2]:
            if self.parent().sorttitle != title:
                self.parent().sorttitle.sortico.hide()
                self.parent().sorttitle = title
            title.sort = not title.sort
            title.setsort(title.sort)
            name.data[2](title.sort)

    # 設定所有Texts成 選中 或者是 未選中 狀態
    def _setallstatus(self):
        alllist = self.listcheck.alllist[self.listcheck.page]
        # 查看是否全部已選中
        if len(self.listcheck.currentclick) == len(alllist):
            # self.setstatus(False)
            for texts in self.listcheck.currentclick.copy():
                texts.setstatus()
        else:
            # self.setstatus(True)
            for texts in alllist:
                if texts not in self.listcheck.currentclick:
                    texts.setstatus()

    # 設定複選紐圖片
    def setstatus(self, status):
        # 設置複選紐圖片
        self.checkbutton.setimage(status)
        # 設置本身狀態
        self.status = status

    def resizeEvent(self, event):
        # 調整複選按鈕 位置
        self.checkbutton.move(5, int((self.listcheck.titlemax - self.ico.height()) / 2))

    # 設定背景顏色 並刷新
    def setbackdrop(self, value):
        # 設定背景QSS backdrop值
        self.setProperty('backdrop', value)
        # 刷新QSS
        self.setStyle(self.style())

    # 鼠標移出label
    def leaveEvent(self, event):
        if self.listcheck.alltitle[0].data[2]:
            if self.mapFromGlobal(QCursor.pos()).x() >= self.width():
                return
            if self.listcheck.alltitle:
                self.setbackdrop(False)
                self.listcheck.alltitle[0].data[0].setbackdrop(False)

    # 鼠標移入label
    def enterEvent(self, event):
        if self.listcheck.alltitle[0].data[2]:
            if self.listcheck.alltitle:
                self.setbackdrop(True)
                self.listcheck.alltitle[0].data[0].setbackdrop(True)


# 移動條
class MyQFrame(QFrame):
    def __init__(self, parent, listcheck, text, least):
        super().__init__(parent)
        # 設定 self.listcheck
        self.listcheck = listcheck
        # 設定 最小控件大小
        self.least = least
        # 自身標題
        self.text = text
        # 設定左右移動直線滑鼠箭頭
        self.setCursor(QCursor(Qt.SizeHorCursor))

    # 滑鼠點擊移動
    def mouseMoveEvent(self, event):
        # 獲取自身標題是在第幾個
        index = self.listcheck.alltitle.index(self.text)
        # 獲取自身標題
        title = self.listcheck.alltitle[index].data[0]
        # 判斷標題移動後的座標 是否小於 最低移動限制
        if title.width() + event.x() >= self.least:
            scrollcontents = self.listcheck.scrollcontents[self.listcheck.page]
            # 獲取移動條移動後的距離
            width = scrollcontents.width() + event.x()
            # 設置標題移動後的scrollcontents寬度
            scrollcontents.resize(width, scrollcontents.height())
            # 設定 自身標題 寬度
            title.resize(title.width() + event.x(), title.height())
            # 設定 自身移動條 位置
            self.move(title.x() + title.width() - 3, 0)
            alllist = self.listcheck.alllist[self.listcheck.page]
            if index + 2 <= len(self.listcheck.alltitle):
                # 獲取後續標題
                for data in self.listcheck.alltitle[index + 1:]:
                    # 從文字裡獲取資料
                    _title, _line, _ = data.data
                    # 後續標題移動位子
                    _title.move(_title.x() + event.x(), _title.y())
                    # 後續移動條移動位置
                    _line.move(_title.x() + _title.width() - 3, _line.y())
                    # 發送後續標題位置信號
                    for texts in alllist:
                        texts.alltext[data].setdata('move', _title.x(), _title.width())

            # 發送移動後 自身X 自身寬度 位置
            for texts in alllist:
                texts.alltext[self.text].setdata('resize', title.x(), title.width())


# 標題
class Title(QFrame):
    # text文字, width預設寬度, least最小寬度
    def __init__(self, parent, listcheck, text, titleinterval, titlemax):
        super().__init__(parent)
        self.listcheck = listcheck
        # 設定標題文字
        self.titleText = QLabel(self)
        # 獲取QT 字體設置
        font = QFont()
        # 設置字體大小
        font.setPointSize(9)
        # 設定標題字體大小
        self.titleText.setFont(font)
        # 紀錄標題文字
        self.text = text
        # 設定文字
        self.titleText.setText(text)
        # 自動適應大小
        self.titleText.adjustSize()
        # 設置標題文字位置
        self.titleText.move(titleinterval, int((titlemax - self.titleText.height()) / 2))
        # 目前排序ico
        self.sort = None
        # 設定是否顯示背景屬性
        self.setProperty('backdrop', False)
        # 設置右側邊框, 背景顏色
        self.setStyleSheet('Title{border-style:solid; border-right-width:1px;'
                           'border-right-color:rgba(200, 200, 200, 125)}'
                           'Title[backdrop="true"]{background-color: rgb(246, 248, 251)}')
        # 排序圖片
        self.sortico = QLabel(self)
        # 排序圖片隱藏
        self.sortico.hide()

    def setsort(self, value):
        index = self.listcheck.alltitle.index(self.text)
        if self.listcheck.alltitle[index].data[2]:
            if not self.sortico.isVisible():
                self.sortico.show()
            self.sort = value
            self.sortico.setPixmap(picture(value))

    def mousePressEvent(self, event):
        index = self.listcheck.alltitle.index(self.text)
        if self.listcheck.alltitle[index].data[2]:
            if self.parent().sorttitle != self:
                self.parent().sorttitle.sortico.hide()
                self.parent().sorttitle = self
            self.sort = not self.sort
            self.setsort(self.sort)
            self.listcheck.alltitle[index].data[2](self.sort)

    # 設置背景顏色 並刷新
    def setbackdrop(self, value):
        self.setProperty('backdrop', value)
        self.setStyle(self.style())

    # 鼠標移出label
    def leaveEvent(self, event):
        index = self.listcheck.alltitle.index(self.text)
        if self.listcheck.alltitle[index].data[2]:
            if index == 0 and self.mapFromGlobal(QCursor.pos()).x() < 0:
                return
            self.setbackdrop(False)
            self.parent().clickqlabel.setbackdrop(False)

    # 鼠標移入label
    def enterEvent(self, event):
        index = self.listcheck.alltitle.index(self.text)
        if self.listcheck.alltitle[index].data[2]:
            self.setbackdrop(True)
            if index == 0:
                self.parent().clickqlabel.setbackdrop(True)

    def resizeEvent(self, event):
        self.sortico.setGeometry(self.width() - 20, 0, 10, self.listcheck.titlemax)


class QTitle(QFrame):
    def __init__(self, parent, listcheck):
        super().__init__(parent)
        # 本體
        self.listcheck = listcheck
        # 禁止傳遞事件給父代  為了防止背景右鍵菜單傳遞
        self.setAttribute(Qt.WA_NoMousePropagation, True)
        # 正在排序中標題
        self.sorttitle = None
        # 標題移動到內容窗口相同位置
        self.move(1, 0)
        ico = picture('複選空白')
        # 設置複選按鈕
        self.clickqlabel = ClickQLabelContainer(self, ico, listcheck)
        # 設置複選按鈕大小
        self.clickqlabel.setGeometry(0, 0, ico.width() + 10, self.listcheck.titlemax)
        # 設置標題下方邊框
        self.setStyleSheet('QTitle{border-style:solid; border-bottom-width:1px;'
                           'border-color:rgba(200, 200, 200, 125)}')

    def setsort(self, name, value, slot):
        if name in self.listcheck.alltitle:
            index = self.listcheck.alltitle.index(name)
            self.listcheck.alltitle[index].data[2] = slot
            if self.sorttitle is None:
                self.sorttitle = self.listcheck.alltitle[index].data[0]
                self.listcheck.alltitle[index].data[0].setsort(value)

    # 刪除 標題
    def delete(self, name):
        # 查看 name 是否存在標題內
        if name in self.listcheck.alltitle:
            # 獲取 name 在標題的 index 位置
            index = self.listcheck.alltitle.index(name)
            # 刪除 index 的 標題 可觸碰移動條
            for data in self.listcheck.alltitle.pop(index).data:
                if data is None:
                    continue
                # 設定父類成無
                data.setParent(None)
                # 調用刪除函數
                data.deleteLater()
            # 查看 index 後面是否還有 標題
            if len(self.listcheck.alltitle) > index:
                for data in self.listcheck.alltitle[index:]:
                    # 獲取標題
                    title = data.data[0]
                    # 獲取可觸碰移動條
                    line = data.data[1]
                    # 獲取 標題是第幾個 index
                    _index = self.listcheck.alltitle.index(data)
                    # 查看 index 是否是第一個
                    if _index == 0:
                        title.move(self.clickqlabel.width(), 0)
                    else:
                        # 獲取上一個標題
                        _title = self.listcheck.alltitle[_index - 1].data[0]
                        # 重新設定標題位置
                        title.move(_title.x() + _title.width(), 0)
                    # 重新設定可觸碰移動條位置
                    line.move(title.x() + title.width() - (int(self.listcheck.titllinesize / 2) + 1), 0)
            # 獲取最後一個標題
            title = self.listcheck.alltitle[-1].data[0]
            # 調整標題容器大小
            self.resize(title.x() + title.width() + (int(self.listcheck.titllinesize / 2) + 1), self.height())
            # 根據最後一個標題設置內容窗口大小
            scrollcontents = self.listcheck.scrollcontents[self.listcheck.page]
            scrollcontents.resize(title.x() + title.width(), scrollcontents.height())
            for texts in self.listcheck.alllist[self.listcheck.page]:
                texts.refresh()

    # 插入標題
    def insert(self, index, name, width=50, least=50):
        # 查看插入的位置 是否要插入還新增
        if len(self.listcheck.alltitle) > index:
            # 獲取插入位置的標題
            _title = self.listcheck.alltitle[index].data[0]
            # 新增標題
            title = Title(self, self.listcheck, name, self.listcheck.titleinterval, self.listcheck.titlemax)
            # 標題調整位置大小
            title.setGeometry(_title.x(), 0, width, self.listcheck.titlemax)
            # 新增可觸碰移動條
            line = MyQFrame(self, self.listcheck, name, least)
            # 設定移動條大小位置
            line.setGeometry(
                title.x() + title.width() - (int(self.listcheck.titllinesize / 2) + 1),
                0, self.listcheck.titllinesize, title.height()
            )
            # 標題顯示
            title.show()
            # 可觸碰移動條顯示
            line.show()
            # # 插入標題
            self.listcheck.alltitle.insert(index, NewString(name, [title, line, None]))
            for data in self.listcheck.alltitle[index + 1:]:
                _title = data.data[0]
                _line = data.data[1]
                _title.setGeometry(title.x() + title.width(), 0, _title.width(), self.listcheck.titlemax)
                # 設定移動條大小位置
                _line.setGeometry(
                    _title.x() + _title.width() - (int(self.listcheck.titllinesize / 2) + 1),
                    0, self.listcheck.titllinesize, _title.height()
                )
                title = _title
            scrollcontents = self.listcheck.scrollcontents[self.listcheck.page]
            # 設置內容窗口寬度大小
            scrollcontents.resize(title.x() + title.width(), scrollcontents.height())

            for texts in self.listcheck.alllist[self.listcheck.page]:
                texts.refresh()

        elif len(self.listcheck.alltitle) == index:
            self.add(name, width=width, least=least)

    # text文字, width預設寬度, least最小寬度
    def add(self, name, width=50, least=50):
        # 如果預設寬度小於 最小寬度 則把預設寬度調整成 最小寬度
        if width < least:
            width = least
        # 設置標題
        title = Title(self, self.listcheck, name, self.listcheck.titleinterval, self.listcheck.titlemax)
        # 查看標題是不是第一個
        if len(self.listcheck.alltitle) == 0:
            # 設置第一格標題位置
            title.setGeometry(self.clickqlabel.width(), 0, width, self.listcheck.titlemax)
        else:
            # 獲取上一個標題
            _title = self.listcheck.alltitle[-1].data[0]
            # 從上一個標題獲取資料設定標題大小位置
            title.setGeometry(_title.x() + _title.width(), 0, width, self.listcheck.titlemax)

        # 設定可觸碰移動條
        line = MyQFrame(self, self.listcheck, name, least)
        # 設定移動條大小位置
        line.setGeometry(
            title.x() + title.width() - (int(self.listcheck.titllinesize / 2) + 1),
            0, self.listcheck.titllinesize, title.height()
        )
        # line.setStyleSheet('background-color: rgb(100, 200, 200)')
        scrollcontents = self.listcheck.scrollcontents[self.listcheck.page]
        # 設置內容窗口寬度大小
        scrollcontents.resize(title.x() + title.width(), scrollcontents.height())
        # 顯示標題
        title.show()
        # 標題往下層移動 防止擋住可觸碰移動條
        title.lower()
        # 可動移動條顯示
        line.show()
        # 插入標題  name 顯示文字 title 文字容器 line 可觸碰移動條 None 點擊事件
        self.listcheck.alltitle.append(NewString(name, [title, line, None]))

        for texts in self.listcheck.alllist[self.listcheck.page]:
            texts.refresh()
