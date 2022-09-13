from module import QWidget, QLabel, QFont, Qt, backdrop, picture, MyIco, startfile,\
                   QFrame, popen, exists, create_task, QPalette, ScrollArea, QColor


class Qtest(QFrame):
    def __init__(self, path, name, ico, size, send, sidebar_1, network, cid=None, parent=None):
        super().__init__(parent)
        # 選擇首頁窗口
        self.sidebar_1 = sidebar_1
        # 前進cid
        self.network = network
        # 如果是上傳則紀錄目錄cid
        self.cid = cid
        # 檔案路徑
        self.path = path
        # 邊框
        self.frame = QFrame(self)
        self.frame.setStyleSheet('border-color:rgba(200, 200, 200, 125)')

        # 副檔名圖案
        self.file_ico = QLabel(self)
        self.file_ico.setGeometry(15, 15, 30, 30)
        self.file_ico.setPixmap(picture(f'_{ico}'))

        self.file_name = QLabel(name, self)
        self.file_name.setFont(QFont("細明體", 9))
        self.file_name.move(55, 16)
        pe = QPalette()
        pe.setColor(QPalette.WindowText, QColor(50, 50, 50, 150))
        self.file_size = QLabel(self)
        self.file_size.setFont(QFont("細明體", 9))
        self.file_size.move(55, 37)
        self.file_size.setText(size)
        self.file_size.setPalette(pe)

        self.ico = QWidget(self)
        _ico = QLabel(self.ico)
        _ico.move(0, 0 if send == '秒傳完成' else 2)
        _ico.setPixmap(picture(send))
        text = QLabel(self.ico)
        text.setFont(QFont("細明體", 9))
        text.move(20, 2)
        text.setText(send)
        text.setPalette(pe)

        MyIco('黑色開啟文件', '藍色開啟文件', coordinate=(97, 0, 13, 15), state=True, click=self.open_file, parent=self.ico)
        MyIco('黑色開啟資料夾', '藍色開啟資料夾', coordinate=(148, 1, 14, 13), state=True, click=self.open_folder, parent=self.ico)
        MyIco('黑色清除記錄', '藍色清除記錄', coordinate=(198, 0, 15, 16), state=True, parent=self.ico)
        self.setStyleSheet('Qtest{border-style:solid; border-bottom-width:1px; border-color:rgba(200, 200, 200, 125)'
                           '; background-color:rgb(255, 255, 255)}')

    def open_folder(self):
        if self.cid:
            self.sidebar_1()
            create_task(self.network(cid=self.cid, pages=True))
        elif exists(self.path):
            popen(f'explorer.exe /select, {self.path}')

    def open_file(self):
        if exists(self.path):
            startfile(self.path)

    def resizeEvent(self, e):
        self.ico.move(self.width() - 293, 20)
        self.file_name.resize(self.width() - 350, 11)
        self.frame.setGeometry(0, self.height() - 1, self.width(), 1)


class EndList(QFrame):
    def __init__(self, sidebar_1, network, parent=None):
        super().__init__(parent)
        # 設置滾動區
        self.scrollarea = ScrollArea(self)
        # 獲取滾動內容窗口
        self.scrollcontents = self.scrollarea.scrollcontents
        # 關閉橫滾動條
        self.scrollarea.sethrizontal(False)
        # 設置背景空白
        self.setStyleSheet(
            'EndList{background-color:rgb(255, 255, 255);border-style:solid;'
            'border-left-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )


        # 所有all_qtest
        self.all_qtest = []
        # 選擇首頁窗口
        self.sidebar_1 = sidebar_1
        # 前進cid
        self.network = network

    # 添加
    def add(self, path, name, ico, size, send, cid=None):
        quantity = len(self.all_qtest)
        progressbar = Qtest(path, name, ico, size, send, self.sidebar_1, self.network, cid=cid, parent=self.scrollcontents)
        progressbar.setGeometry(0, quantity * 56, self.width() - 2, 56)
        progressbar.show()
        self.scrollcontents.setGeometry(0, 0, self.width() - 2, (quantity + 1) * 56)
        self.all_qtest.append(progressbar)

    def resizeEvent(self, e):
        self.scrollarea.resize(self.size())
        self.scrollcontents.setGeometry(0, 0, self.width() - 2, self.scrollcontents.height())
        for progressBar in self.all_qtest:
            progressBar.setGeometry(0, progressBar.y(), self.width() - 2, 56)
