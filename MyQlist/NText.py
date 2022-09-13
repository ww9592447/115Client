from .package import picture, MyQLabel, QFont, QLabel, QCursor, QMenu, Qt


class MyLText(MyQLabel):
    def __init__(self, parent, size=15):
        super().__init__(parent)
        # 獲取字體設置
        font = QFont()
        # 設置字體大小
        font.setPointSize(size)
        # 設定標題字體大小
        self.setFont(font)


class Text(MyQLabel):
    def __init__(self, text=None, listcheck=None, data=None, ico=None, my_mode=None, text_mode=None):
        super().__init__(None)
        self.setStyleSheet(
            'Text{background-color: white}'
            'Text:hover{background-color: rgb(249, 250, 251)}'
            'Text[status="true"]{background-color: rgb(234, 246, 253)}'
        )
        self.listcheck = listcheck
        # 設定選中狀態qss屬性
        self.setProperty('status', False)
        # 設定按鍵發射
        self.slot = self
        # 點擊狀態
        self.status = False
        # text圖標
        self.textico = None
        # 右鍵
        self.contextMenu = None
        # 記錄額外資料
        self.data = data
        # 設定 text
        self.text_ = MyLText(self)
        # 設定 text 文字
        self.text_.setText(text)
        # 判斷是否需要設定圖標
        if ico:
            # 獲取相應圖標
            _ico = picture(ico)
            # 設定圖標
            self.textico = QLabel(self)
            # 設定圖標圖片
            self.textico.setPixmap(_ico)
            # 設置圖標大小
            self.textico.resize(_ico.size())
            # 設置圖標位置
            self.textico.move(
                10, int((self.listcheck.textmax - self.textico.height()) / 2)
            )
        # 獲取 text x位置
        x = (self.textico.x() + self.textico.width()) if self.textico else 0
        # 獲取 text y位置
        y = int((self.listcheck.textmax - self.text_.fontMetrics().height()) / 2)
        # 設定 text 位置
        self.text_.move(x + 10, y)
        # 設定 text 大小
        self.text_.resize(
            self.text_.fontMetrics().horizontalAdvance(text),
            self.text_.fontMetrics().height())

        if my_mode:
            # 查看 自身 是否需要設定單擊信號
            if 'leftclick' in my_mode:
                for mode in my_mode['leftclick']:
                    # 連接自身左鍵點擊信號
                    self.leftclick.connect(mode)
            # 查看 自身 是否需要設定雙擊信號
            if 'doubleclick' in my_mode:
                for mode in my_mode['doubleclick']:
                    # 連接自身左鍵雙擊信號
                    self.doubleclick.connect(mode)
            if 'cursor' in my_mode:
                self.setCursor(Qt.PointingHandCursor)
        if text_mode:
            # 查看 自身 是否需要設定單擊信號
            if 'leftclick' in text_mode:
                for mode in text_mode['leftclick']:
                    self.text_.leftclick.connect(mode)
            # 查看 text 是否需要設定標題 顏色
            if 'color' in text_mode:
                # 設定QSS 預設顏色 移動到上方顏色
                self.text_.setStyleSheet(
                    f'MyLText{{color: rgb{text_mode["color"][0]}}}'
                    f'MyLText:hover{{color: rgb{text_mode["color"][1]}}}'
                )
            if 'cursor' in my_mode:
                self.text_.setCursor(Qt.PointingHandCursor)

    # 右鍵菜單事件
    def menuclick(self, text, slot, mode=True):
        # 在右鍵位置顯示
        def display():
            if self.listcheck.menu_callback:
                self.listcheck.menu_callback(lambda: self.contextMenu.popup(QCursor.pos()))
            else:
                self.contextMenu.popup(QCursor.pos())
            # for _, values in self.listcheck.menu.items():
            # 	for _, _values in values.items():
            # 		if _values.isVisible():
            # 			self.contextMenu.popup(QCursor.pos())
            # 			return

        # 如果沒有QMenu信號事件 創建QMenu信號事件
        if self.contextMenu is None:
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(display)
            self.contextMenu = QMenu(self)

        cp = self.contextMenu.addAction(text)
        cp.triggered.connect(slot)
        cp.setVisible(mode)
        if self not in self.listcheck.menu:
            self.listcheck.menu[self.listcheck.page][self] = {text: cp}
        else:
            self.listcheck.menu[self.listcheck.page][self].update({text: cp})

    # 更改大小事件
    def resizeEvent(self, e):
        pass


class QText:
    def __init__(self, listcheck):
        self.listcheck = listcheck

    # 添加一個列表 *args 文字列表 data 額外資料 ico 圖標 mode 文字點擊事件 顏色 設定
    def add(self, text, index=None, data=None, ico=None, my_mode=None, text_mode=None):
        if index:
            category = 1
        else:
            category = 0
        self._create(text, index=index, category=category, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode)

    # 插入一個列表
    def insert(self, index, text, data=None, ico=None, my_mode=None, text_mode=None):
        self._create(text, category=2, index=index, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode)

    def _create(self, text, category, index=None, data=None, ico=None, my_mode=None, text_mode=None):
        # 新增texts
        texts = Text(
            text, listcheck=self.listcheck, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode
        )
        # 查看是否需要新增
        if category == 0:
            page = 0
            for page in range(len(self.listcheck.alllist)):
                if len(self.listcheck.alllist[page]) + 1 <= self.listcheck.pagemax:
                    break

            if len(self.listcheck.alllist[page]) + 1 > self.listcheck.pagemax:
                self.listcheck.quantity.add()
                page += 1
            texts.setParent(self.listcheck.scrollcontents[page])
            # 設置位置
            texts.setGeometry(
                0, len(self.listcheck.alllist[page]) * self.listcheck.textmax,
                self.listcheck.scrollcontents[page].width(), self.listcheck.textmax
            )
            # 添加新label
            self.listcheck.alllist[page].append(texts)
            index = page
        # 查看是否需要從 page頁 開始新增
        elif category == 1:
            page = len(self.listcheck.alllist) - 1
            for page in range(index, len(self.listcheck.alllist)):
                if len(self.listcheck.alllist[page]) < self.listcheck.pagemax:
                    break
            if len(self.listcheck.alllist[page]) > self.listcheck.pagemax:
                self.listcheck.quantity.add()
                page += 1
            texts.setParent(self.listcheck.scrollcontents[page])
            # 設置位置
            texts.setGeometry(
                0, len(self.listcheck.alllist[page]) * self.listcheck.textmax,
                self.listcheck.scrollcontents[page].width(), self.listcheck.textmax
            )
            # 添加新label
            self.listcheck.alllist[page].append(texts)
    
        # 查看是否需要插入
        elif category == 2:
            insert_index = index // self.listcheck.pagemax
            _insert_index = index % self.listcheck.pagemax
            if insert_index + 1 > len(self.listcheck.alllist):
                self._create(texts, index=insert_index, category=1, data=data, ico=ico, my_mode=my_mode,
                             text_mode=text_mode)
                return
    
            while 1:
                texts.setParent(self.listcheck.scrollcontents[insert_index])
                alllist = self.listcheck.alllist[insert_index]
                alllist.insert(_insert_index, texts)
                for _texts, _index in zip(alllist, range(len(alllist))):
                    _texts.setGeometry(
                        0, _index * self.listcheck.textmax,
                        self.listcheck.scrollcontents[insert_index].width(), self.listcheck.textmax
                    )
                if len(self.listcheck.alllist[insert_index]) > self.listcheck.pagemax:
                    texts = self.listcheck.alllist[insert_index].pop()
                    _insert_index = 0
                    insert_index += 1
                    if insert_index > len(self.listcheck.alllist) - 1:
                        self.listcheck.quantity.add()
                else:
                    break
        # texts顯示
        texts.show()
    
        # 初始化點擊事件
        for slot in self.listcheck.click_connect:
            if slot[0] == 'texts':
                getattr(texts, slot[1]).connect(slot[2])
            elif slot[0] == 'menu':
                getattr(texts, slot[1])(slot[2], slot[3])
        if self.listcheck.page != index:
            return
        self.listcheck.quantity.all(len(self.listcheck.alllist[self.listcheck.page]))
        # 設置內容容器大小
        self.listcheck.scrollcontents[self.listcheck.page].resize(
            self.listcheck.scrollcontents[self.listcheck.page].width(),
            len(self.listcheck.alllist[self.listcheck.page]) * self.listcheck.textmax
        )

