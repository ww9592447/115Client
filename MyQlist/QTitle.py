from .module import picture, ClickQLabel, QMouseEvent, QResizeEvent, QLabel,\
    QPixmap, Qt, QFrame, QFont, QCursor
if False:
    from QList import ListCheck, AllQWidget


class QTitle(QFrame):
    def __init__(self, parent: 'AllQWidget', listcheck: 'ListCheck'):
        super().__init__(parent)
        self.listcheck: ListCheck = listcheck
        # 獲取複選紐
        ico: QPixmap = picture('複選空白')
        # 設置標題第一個複選紐
        self.clickqlabel = ClickQLabelContainer(self, ico, listcheck)
        # 設置複選按鈕大小
        self.clickqlabel.setGeometry(0, 0, ico.width() + 10, self.listcheck.titlemax)
        # 禁止傳遞事件給父代  為了防止背景右鍵菜單傳遞
        self.setAttribute(Qt.WA_NoMousePropagation, True)
        # 標題移動到內容窗口相同位置
        self.move(1, 0)
        # 設置標題下方邊框
        self.setStyleSheet('QTitle{border-style:solid; border-bottom-width:1px;'
                           'border-color:rgba(200, 200, 200, 125)}')

    # text文字, width預設寬度, least最小寬度
    def add(self, name, width=50, least=50):
        # 如果預設寬度小於 最小寬度 則把預設寬度調整成 最小寬度
        if width < least:
            width = least
        # 設置標題
        title = Title(self, self.listcheck, name)
        # 查看標題是不是第一個
        if len(self.listcheck.titlelist) == 0:
            # 設置第一格標題位置
            title.setGeometry(self.clickqlabel.width(), 0, width, self.listcheck.titlemax)
        else:
            # 獲取上一個標題
            _title, _ = self.listcheck.titlelist[-1]
            # 從上一個標題獲取資料設定標題大小位置
            title.setGeometry(_title.x() + _title.width(), 0, width, self.listcheck.titlemax)

        # 設定可觸碰移動條
        line = MovingBar(self, self.listcheck, name, least)
        # 設定移動條大小位置
        line.setGeometry(
            title.x() + title.width() - (int(self.listcheck.titllinesize / 2) + 1),
            0, self.listcheck.titllinesize, title.height()
        )
        # 設置內容窗口寬度大小
        self.listcheck.scrollcontents.resize(title.x() + title.width(), self.listcheck.scrollcontents.height())
        # 顯示標題
        title.show()
        # 標題往下層移動 防止擋住可觸碰移動條
        title.lower()
        # 可動移動條顯示
        line.show()
        # 插入標題  name 顯示文字 title 文字容器 line 可觸碰移動條 None 點擊事件
        self.listcheck.titlelist.append(name, (title, line))

        for text in self.listcheck.textlist:
            # 新增 新的 子text
            text.settext(title)
            # 讓所有的 text 保持跟 內容窗口相同寬度
            text.resize(self.listcheck.scrollcontents.width(), text.height())
            # 獲取 自身標題符合的 子text
            _text = text.textlist[title.text]
            # 調整 子text 寬度
            _text.resize(title.x() + title.width() - _text.x(), _text.height())

    # 設置標題 顯示 or 隱藏
    def set_title_visible(self, name: str, visible: bool) -> None:
        # 獲取要設定的 標題 移動條
        title, line = self.listcheck.titlelist.get(name)
        # 設定標題 顯示 or 隱藏
        title.setVisible(visible)
        # 設定移動條 顯示 or 隱藏
        line.setVisible(visible)
        # 獲取內容窗口
        scrollcontents = self.listcheck.scrollcontents
        # 設置內容窗口寬度大小
        scrollcontents.resize(
            scrollcontents.width() + (title.width() if visible else - title.width()), scrollcontents.height()
        )
        # 循環text
        for text in self.listcheck.textlist:
            # 獲取子text
            mytext = text.textlist[title.text]
            # 子text 顯示 or 隱藏
            mytext.setVisible(visible)
            # text 調整大小
            text.resize(scrollcontents.width(), text.height())
        # 設定標題list 顯示 or 隱藏
        self.listcheck.titlelist.setvisible(title.text, visible)
        # 獲取 子text 第一個x座標
        x = self.clickqlabel.width()
        for index, titlelist in enumerate(self.listcheck.titlelist):
            _title, _line = titlelist
            if _title.x() != x:
                _title.move(x, _title.y())
                _line.move(_title.x() + _title.width() - (int(self.listcheck.titllinesize / 2) + 1), _title.y())
                for text in self.listcheck.textlist:
                    mytext = text.textlist[_title.text]
                    if index == 0 and not mytext.parent_.icoimage.isHidden():
                        mytext.move(mytext.parent_.text_x, mytext.y())
                    else:
                        mytext.move(x, mytext.y())
            x = _title.x() + _title.width()


# 標題第一個複選紐容器
class ClickQLabelContainer(QFrame):
    def __init__(self, parent: QTitle, ico: QPixmap, listcheck: 'ListCheck'):
        super().__init__(parent)
        self.listcheck: ListCheck = listcheck
        # 設定未選中ico
        self.unselected: QPixmap = picture('複選空白')
        # 設定選中ico
        self.checked: QPixmap = picture('複選打勾')
        # 複選紐狀態
        self.state: bool = False
        # 獲取複選紐圖片
        self.ico: QPixmap = ico
        # 設置複選按鈕
        self.checkbutton: ClickQLabel = ClickQLabel(self)
        # 複選紐連接全選 OR 未選 信號
        self.checkbutton.leftclick.connect(self._setallstate)
        # 設置複選按鈕跟圖片大小一樣
        self.checkbutton.resize(ico.size())
        # 設置背景顏色QSS
        self.setStyleSheet('ClickQLabelContainer[backdrop="true"]{background-color: rgb(246, 248, 251)}')

    # # 滑鼠單擊事件
    # def mousePressEvent(self, event: QMouseEvent) -> None:
    #     # 獲取第一個標題名稱
    #     name = self.listcheck.alltitle[0]
    #     # 根據名稱獲取標題
    #     title = name.data[0]
    #     # 查看標題是否有函數需要調用
    #     if name.data[2]:
    #         if self.parent().sorttitle != title:
    #             self.parent().sorttitle.sortico.hide()
    #             self.parent().sorttitle = title
    #         title.sort = not title.sort
    #         title.setsort(title.sort)
    #         name.data[2](title.sort)

    # 設定所有Texts成 選中 或者是 未選中 狀態
    def _setallstate(self) -> None:
        # 查看是否全部已選中
        if len(self.listcheck.currentclick) == self.listcheck.textall:
            for text in self.listcheck.currentclick.copy():
                text.setstate()
        else:
            for text in self.listcheck.textlist[0:self.listcheck.textall]:
                if text not in self.listcheck.currentclick:
                    text.setstate()

    # 設定複選紐圖片
    def setstate(self, state: bool) -> None:
        # 設置複選紐圖片
        self.checkbutton.setimage(state)
        # 設置本身狀態
        self.state = state

    # 設定背景顏色 並刷新
    def setbackdrop(self, state: bool) -> None:
        # 設定背景QSS backdrop值
        self.setProperty('backdrop', state)
        # 刷新QSS
        self.setStyle(self.style())

    # # 鼠標移出事件
    # def leaveEvent(self, event: QEvent) -> None:
    #     if self.listcheck.alltitle[0].data[2]:
    #         if self.mapFromGlobal(QCursor.pos()).x() >= self.width():
    #             return
    #         if self.listcheck.alltitle:
    #             self.setbackdrop(False)
    #             self.listcheck.alltitle[0].data[0].setbackdrop(False)

    # # 鼠標移入label
    # def enterEvent(self, event):
    #     if self.listcheck.alltitle[0].data[2]:
    #         if self.listcheck.alltitle:
    #             self.setbackdrop(True)
    #             self.listcheck.alltitle[0].data[0].setbackdrop(True)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        # 調整複選按鈕 位置
        self.checkbutton.move(5, int((self.listcheck.titlemax - self.ico.height()) / 2))


# 標題
class Title(QFrame):
    # text文字, width預設寬度, least最小寬度
    def __init__(self, parent: QTitle, listcheck: 'ListCheck', text: str) -> None:
        super().__init__(parent)
        self.listcheck: ListCheck = listcheck
        # 設定標題文字
        self.titleText: QLabel = QLabel(self)
        # 紀錄標題文字
        self.text: str = text
        # 獲取QT 字體設置
        font = QFont()
        # 設置字體大小
        font.setPointSize(9)
        # 設定標題字體大小
        self.titleText.setFont(font)
        # 設定文字
        self.titleText.setText(text)
        # 自動適應大小
        self.titleText.adjustSize()
        # 設置標題文字位置
        self.titleText.move(self.listcheck.titleinterval, int((self.listcheck.titlemax - self.titleText.height()) / 2))
        # # 目前排序ico
        # self.sort: str = ''
        # # 排序圖片
        # self.sortico: QLabel = QLabel(self)
        # # 排序圖片隱藏
        # self.sortico.hide()
        # 設定是否顯示背景屬性
        self.setProperty('backdrop', False)
        # 設置右側邊框, 背景顏色
        self.setStyleSheet('Title{border-style:solid; border-right-width:1px;'
                           'border-right-color:rgba(200, 200, 200, 125)}'
                           'Title[backdrop="true"]{background-color: rgb(246, 248, 251)}')

    # def setsort(self, value):
    #     index = self.listcheck.alltitle.index(self.text)
    #     if self.listcheck.alltitle[index].data[2]:
    #         if not self.sortico.isVisible():
    #             self.sortico.show()
    #         self.sort = value
    #         self.sortico.setPixmap(picture(value))

    # # 滑鼠單擊事件
    # def mousePressEvent(self, event: QMouseEvent) -> None:
    #     index = self.listcheck.alltitle.index(self.text)
    #     if self.listcheck.alltitle[index].data[2]:
    #         if self.parent().sorttitle != self:
    #             self.parent().sorttitle.sortico.hide()
    #             self.parent().sorttitle = self
    #         self.sort = not self.sort
    #         self.setsort(self.sort)
    #         self.listcheck.alltitle[index].data[2](self.sort)

    # # 設置背景顏色 並刷新
    # def setbackdrop(self, value):
    #     self.setProperty('backdrop', value)
    #     self.setStyle(self.style())
    #
    # # 鼠標移出label
    # def leaveEvent(self, event):
    #     index = self.listcheck.alltitle.index(self.text)
    #     if self.listcheck.alltitle[index].data[2]:
    #         if index == 0 and self.mapFromGlobal(QCursor.pos()).x() < 0:
    #             return
    #         self.setbackdrop(False)
    #         self.parent().clickqlabel.setbackdrop(False)
    #
    # # 鼠標移入label
    # def enterEvent(self, event):
    #     index = self.listcheck.alltitle.index(self.text)
    #     if self.listcheck.alltitle[index].data[2]:
    #         self.setbackdrop(True)
    #         if index == 0:
    #             self.parent().clickqlabel.setbackdrop(True)

    # def resizeEvent(self, event):
        # self.sortico.setGeometry(self.width() - 20, 0, 10, self.listcheck.titlemax)


# 移動條
class MovingBar(QFrame):
    def __init__(self, parent: QTitle, listcheck: 'ListCheck', text: str, least: int):
        super().__init__(parent)
        # 設定 self.listcheck
        self.listcheck: ListCheck = listcheck
        # 自身標題
        self.text: str = text
        # 設定 最小控件大小
        self.least: int = least
        # 設定左右移動直線滑鼠箭頭
        self.setCursor(QCursor(Qt.SizeHorCursor))

    # 滑鼠點擊移動
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # 獲取自身標題是在第幾個
        index = self.listcheck.titlelist.index(self.text)
        # 獲取自身標題
        title, _ = self.listcheck.titlelist.get(self.text)
        # 判斷標題移動後的座標 是否小於 最低移動限制
        if title.width() + event.x() >= self.least:
            # 獲取內容窗口
            scrollcontents = self.listcheck.scrollcontents
            # 設置標題移動後的scrollcontents寬度
            scrollcontents.resize(scrollcontents.width() + event.x(), scrollcontents.height())
            # 設定 自身標題 寬度
            title.resize(title.width() + event.x(), title.height())
            # 設定 自身移動條 位置
            self.move(title.x() + title.width() - 3, 0)
            # 移動後面的 標題 移動條
            if index + 2 <= len(self.listcheck.titlelist):
                # 獲取後續標題, 移動條
                for _title, _line in self.listcheck.titlelist[index + 1:]:
                    # 後續標題移動位子
                    _title.move(_title.x() + event.x(), _title.y())
                    # 後續移動條移動位置
                    _line.move(_title.x() + _title.width() - 3, _line.y())
                    # 發送後續標題位置信號
                    for text in self.listcheck.textlist:
                        _text = text.textlist[_title.text]
                        _text.move(_title.x(), _text.y())
            # 發送移動後 自身X 自身寬度 位置
            for text in self.listcheck.textlist:
                # 讓所有的 text 保持跟 內容窗口相同寬度
                text.resize(self.listcheck.scrollcontents.width(), text.height())
                # 獲取 自身標題符合的 子text
                _text = text.textlist[title.text]
                # 調整 子text 寬度
                _text.resize(title.x() + title.width() - _text.x(), _text.height())
