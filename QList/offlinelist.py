from module import MyQLabel, QLabel, QWidget, picture,\
    QFont, pybyte, QProgressBar, MyIco, ScrollArea,\
    create_task, QFrame, gif


class Qtext(QFrame):
    def __init__(self, data, end, _open, parent=None):
        super().__init__(parent)
        self.data = data
        self.name_ico = QLabel(self)
        self.name_ico.setGeometry(15, 15, 30, 30)
        self.name_ico.setPixmap(picture(f'_資料夾'))
        # 檔案名稱
        self.file_name = QLabel(data['name'], self)
        self.file_name.setFont(QFont("細明體", 9))
        self.file_name.move(55, 16)

        self.file_size = QLabel(pybyte(int(data['size'])), self)
        self.file_size.setFont(QFont("細明體", 9))
        self.file_size.move(55, 37)
        self.file_size.setFixedWidth(100)
        self.file_size.setStyleSheet('color:rgba(50, 50, 50, 150)')
        # 磁力hash
        self.ico = QFrame(self)

        y = lambda height: int((56 - height) / 2)
        if data['status'] == 1:
            # 設置進度條
            self.progressBar = QProgressBar(self.ico)
            self.progressBar.setMaximum(100)
            self.progressBar.setGeometry(0, y(14), 152, 14)
            self.progressBar.setTextVisible(False)
            self.progressBar.setValue(int(data['percentDone']))
            MyIco('黑色關閉下載', '藍色關閉下載', coordinate=(190, y(10), 9, 10), state=True,
                  click=lambda: create_task(end(data['info_hash'])), parent=self.ico)
        elif data['status'] == 2:
            # 設置顯示狀態
            self.progressText = QLabel(self.ico)
            self.progressText.setFont(QFont("細明體", 12))
            self.progressText.setGeometry(0, y(16), 152, 16)
            self.progressText.setStyleSheet('color:rgba(50, 50, 50, 150)')
            self.progressText.setText('下載完成')
            MyIco('黑色關閉下載', '藍色關閉下載', coordinate=(160, y(10), 9, 10), state=True,
                  click=lambda: create_task(end(data['info_hash'])), parent=self.ico)
            MyIco('黑色開啟資料夾', '藍色開啟資料夾', coordinate=(190, y(13), 14, 13), state=True,
                  click=lambda: create_task(_open(data['file_id'])), parent=self.ico)
        elif data['status'] == -1:
            self.progressText = QLabel(self.ico)
            self.progressText.setFont(QFont("細明體", 12))
            self.progressText.setGeometry(0, y(16), 152, 16)
            self.progressText.setStyleSheet('color:rgba(50, 50, 50, 150)')
            self.progressText.setText('下載含有違規內容')
            MyIco('黑色關閉下載', '藍色關閉下載', coordinate=(190, y(10), 9, 10), state=True,
                  click=lambda: create_task(end(data['info_hash'])), parent=self.ico)
        # 邊框
        self.setObjectName('_frame')
        self.setStyleSheet('#_frame{border-style:solid;border-bottom-width:1;border-color: rgba(200, 200, 200, 125);'
                           'background-color: rgb(255, 255, 255)}')

    def resizeEvent(self, e):
        self.ico.setGeometry(self.width() - 240, 0, 360, 56)


class Offlinelist(QFrame):
    def __init__(self, directory, sidebar_1, network, parent=None):
        super().__init__(parent)
        # 目錄操作
        self.directory = directory
        # 切換目錄
        self.sidebar_1 = sidebar_1
        # 進入cid
        self.network = network
        # 所有Qtest
        self.allqtext = []
        # 設置滾動區
        self.scrollarea = ScrollArea(self)
        # 獲取滾動內容窗口
        self.scrollcontents = self.scrollarea.scrollcontents
        # 關閉橫滾動條
        self.scrollarea.sethrizontal(False)
        # 根據名稱設置背景空白
        self.setStyleSheet(
            'Offlinelist{background-color:rgb(255, 255, 255);border-style:solid;'
            'border-left-width:1px; border-color:rgba(200, 200, 200, 125)}'
            'ScrollArea{border-style:solid;border-top-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )
        self.gui = gif(self, '加載')
        
        MyQLabel('刷新', (10, 8, 111, 41), fontsize=16, clicked=lambda: create_task(self._refresh()), parent=self)
        MyQLabel('清空', (130, 8, 111, 41), fontsize=16, clicked=lambda: create_task(self.cls()), parent=self)
    
    def add(self, data):
        quantity = len(self.allqtext)
        qtext = Qtext(data, self.end, self.open, parent=self.scrollcontents)
        qtext.setGeometry(0, quantity * 56, self.width(), 56)
        qtext.show()
        self.scrollcontents.setGeometry(0, 0, self.width(),  (quantity + 1) * 56)
        self.allqtext.append(qtext)
    
    async def open(self, cid):
        # 切換首頁
        self.sidebar_1()
        # 進入指定目錄
        create_task(self.network(cid, pages=True))

    def delete(self):
        self.scrollcontents = QFrame(self)
        self.scrollcontents.setGeometry(0, 0, self.width(), 0)
        self.scrollcontents.show()
        self.scrollarea.setwidget(self.scrollcontents)
        self.allqtext = []

    async def end(self, _hash):
        if self.allqtext:
            self.delete()
        self.gui.show()
        await self.directory.offline_delete(_hash)
        await self._refresh()

    async def cls(self):
        self.gui.show()
        await self.directory.offline_clearurl()
        self.gui.hide()

    async def _refresh(self):
        self.gui.show()
        if self.allqtext:
            self.delete()
        tasks = await self.directory.offline_schedule()
        if tasks['tasks'] is not None:
            for task in tasks['tasks']:
                self.add(task)
        self.gui.hide()

    def raise_(self):
        QWidget.raise_(self)
        create_task(self._refresh())

    def resizeEvent(self, e):
        self.scrollcontents.setGeometry(0, 0, self.width(), self.scrollcontents.height())
        for qtext in self.allqtext:
            qtext.setGeometry(0, qtext.y(), self.width(), 56)
        self.gui.move(int(self.width() / 2), int(self.height() / 2))
        self.scrollarea.setGeometry(0, 55, self.width(), self.height() - 55)

