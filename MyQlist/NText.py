from .module import MyTextSave, QApplication, Optional, Callable, QFontMetrics, picture, MyQLabel, MyQFrame, QFont, QLabel, QCursor, Qt
if False:
    from NList import NList


class Text(MyQFrame):
    def __init__(self, nlist: 'NList', index: int) -> None:
        super().__init__(nlist.scrollcontents)
        self.nlist: NList = nlist
        # 自身編號
        self.index = index
        # 點擊狀態
        self.state: bool = False
        # 設定按鍵發射
        self.slot: MyQFrame = self
        # text圖標
        self.icoimage: QLabel = QLabel(self)
        # text圖標 隱藏
        self.icoimage.hide()
        # 獲取字體設置
        font: QFont = QFont()
        # 設置字體大小
        font.setPointSize(15)
        # 設置子text
        self.text: MyText = MyText(self)
        # 設置 子text y座標 位置
        self.text.move(0, int((self.nlist.textmax - QFontMetrics(font).height()) / 2))
        # 紀錄text圖標文字
        self._ico: str = ''
        # 紀錄 背景左鍵 點擊信號
        self._leftclick: list[Callable, ...] = []
        # 紀錄 背景左鍵 雙擊信號
        self._doubleclick: list[Callable, ...] = []
        # 記錄額外資料
        self.data: any = None
        # 設置右鍵策略
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # 設置右鍵連接事件
        self.customContextMenuRequested.connect(self.display)
        # 設定選中狀態qss屬性
        self.setProperty('state', False)
        # 設置 qss
        self.setStyleSheet(
            'Text{background-color: white}'
            'Text:hover{background-color: rgb(249, 250, 251)}'
            'Text[state="true"]{background-color: rgb(234, 246, 253)}'
        )

    # 右鍵事件
    def display(self):
        if self.nlist.menu:
            if self.nlist.menu_callback:
                self.nlist.menu_callback(lambda: self.listcheck.contextmenu.popup(QCursor.pos()))
            else:
                self.nlist.contextmenu.popup(QCursor.pos())

    # 重新設定子texts資料
    def refresh(self):
        save = self.nlist.textsave[self.index]
        self.data = save['data']
        if save['ico'] and self._ico != save['ico']:
            # 獲取相應圖標
            ico = picture(save['ico'])
            # 保存目前的圖標文字
            self._ico = save['ico']
            # 設定圖標圖片
            self.icoimage.setPixmap(ico)
            # 設置圖標大小
            self.icoimage.resize(ico.size())
            # 設置圖標位置
            self.icoimage.move(
                10, int((self.nlist.textmax - self.icoimage.height()) / 2)
            )
            # 圖標顯示
            self.icoimage.show()

            self.text.move(self.icoimage.x() + self.icoimage.width() + 10, self.text.y())

        elif save['ico'] is None and self.icoimage.isVisible():
            self._ico = None
            self.icoimage.hide()
            self.text.move(0, self.text.y())

        # 查看目前是否有左鍵點擊信號 如果有 則全部解除
        if self._leftclick:
            # 全部解除 左鍵點擊信號
            self.leftclick.disconnect()
            # 全部刪除 左鍵點擊信號
            self._leftclick.clear()
        # 查看目前是否有左鍵雙擊信號 如果有 則全部解除
        if self._doubleclick:
            # 全部解除 左鍵雙擊信號
            self.doubleclick.disconnect()
            # 全部刪除 左鍵雙擊信號
            self._doubleclick.clear()

        if save['leftclick']:
            # 連接 新的 左鍵點擊信號
            for slot in save['leftclick']:
                self.leftclick.connect(slot)
                self._leftclick.append(slot)
        if save['doubleclick']:
            # 連接 新的 左鍵雙擊信號
            for slot in save['doubleclick']:
                self.doubleclick.connect(slot)
                self._doubleclick.append(slot)

        self.text.refresh(save['text'])
        self.text.adjustSize()


class MyText(MyQLabel):
    def __init__(self, parent: Text):
        super().__init__(parent)
        # 保存 自身 數據
        self.data: MyTextSave = {'text': '', 'leftclick': None, 'color': None}
        # 紀錄 子text 左鍵點擊信號
        self._leftclick: list[Callable, ...] = []
        # 紀錄 子text qss滑動到上方顏色
        self._color: Optional[tuple[tuple[int, int, int], tuple[int, int, int]]] = None
        # 獲取字體設置
        font: QFont = QFont()
        # 設置字體大小
        font.setPointSize(15)
        # 設定標題字體大小
        self.setFont(font)

    def refresh(self, data: MyTextSave) -> None:
        # 設置text
        self.setText(data['text'])
        # 查看目前是否有左鍵點擊信號 如果有 則全部解除
        if self._leftclick:
            # 全部解除 左鍵點擊信號
            self.leftclick.disconnect()
            # 清空 左鍵信號
            self._leftclick.clear()
            # 如果沒有點擊信號
            if not data['leftclick']:
                # 滑鼠還原
                self.setCursor(Qt.ArrowCursor)
        if data['leftclick']:
            # 連接 新的 左鍵點擊信號
            for slot in data['leftclick']:
                self.leftclick.connect(slot)
                self._leftclick.append(slot)
            # 滑鼠設定成可點擊圖標
            self.setCursor(Qt.PointingHandCursor)

        if self.data['color'] != data['color'] and data['color']:
            # 設置text 預設顏色 滑動到上方顏色
            self.setStyleSheet(
                f'MyText{{color: rgb{data["color"][0]}}}'
                f'MyText:hover{{color: rgb{data["color"][1]}}}'
            )
        elif self.data['color'] and data['color'] is None:
            self.setStyleSheet('')
        # 更新數據
        self.data.update(**data)


class QText:
    def __init__(self, nlist: 'NList') -> None:
        self.nlist: NList = nlist

        for index in range(self.nlist.pagemax):
            text = Text(self.nlist, index)
            # 設置位置
            text.setGeometry(
                0, len(self.nlist.textlist) * self.nlist.textmax,
                self.nlist.scrollcontents.width(), self.nlist.textmax
            )
            self.nlist.textlist.append(text)
            # text顯示
            text.show()

    # 複選紐左鍵點擊事件
    def _vbox_left_select(self, text: Text) -> None:
        # 點著shift事件
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            self._shift(text)
            return
        # 設定成最後一次點擊
        self.nlist.firstclick = text
        text.setstate()

    # 複選紐右擊點擊事件
    def _vbox_right_select(self, text: Text) -> None:
        # 設定成最後一次點擊
        self.nlist.firstclick = text
        text.setstate()

    # texts左鍵單擊點擊事件
    def _text_left_select(self, text: Text) -> None:
        # CTRL事件
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            self._vbox_left_select(text)
            return
        # SHIFT事件
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            self._shift(text)
        else:
            self._radio(text)

    # label右擊點擊事件
    def _text_right_select(self, text: Text) -> None:
        if text.state:
            return
        # CTRL事件
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            self._vbox_left_select(text)
            return
        # SHIFT事件
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            self._shift(text)
        else:
            self._radio(text)

    # 單獨選一個
    def _radio(self, text: Text) -> None:
        self.nlist.firstclick = text
        # 獲得已點擊複製
        currentclick = self.nlist.currentclick.copy()
        if text in currentclick:
            currentclick.remove(text)
        else:
            text.setstate()
        for _text in currentclick:
            _text.setstate()

    # shift事件
    def _shift(self, text: Text) -> None:
        # 獲取目前點擊的text 是在第幾個
        index = self.nlist.textlist.index(text)
        # 查看最後一次點擊 之前是否點擊過
        if self.nlist.firstclick is not None:
            _index = self.nlist.textlist.index(self.nlist.firstclick)
            # 獲取目前點擊的 - 最後點擊 之間的數量
            multiple_selection = index - _index
            # 查看數量是否大於0
            if multiple_selection > 0:
                currently = self.nlist.textlist[_index:index + 1]
            # 查看數量是否小於0
            elif multiple_selection < 0:
                currently = self.nlist.textlist[index:_index + 1]
            # 如果等於0進入點擊
            else:
                # 進入單獨點擊
                self._radio(text)
                return
            # 獲取目前所有以點擊的複製
            currentclick = self.nlist.currentclick.copy()
            # 循環舊的所有text 複製
            for text in currentclick:
                # 查看 index 是否在新典籍範圍之內
                if text in currently:
                    # 在點擊範圍之內 就移除新點擊範圍的 index 不需要重新設定複選紐
                    currently.remove(text)
                else:
                    # 在點擊範圍之外 設定成空複選紐
                    text.setstate()
            # 循環新的所有texts點擊
            for text in currently:
                # 設定成選中複選紐
                text.setstate()
        else:
            self.nlist.firstclick = text
            self._radio(text)

