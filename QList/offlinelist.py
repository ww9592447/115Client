from module import MyQLabel, QLabel, QWidget, picture, Callable, QObject,\
    QFont, pybyte, QProgressBar, MyIco, ScrollArea, QResizeEvent,\
    create_task, QFrame, gif, Awaitable
from API.directory import Directory


class Qtext(QFrame):
    def __init__(self, data: dict[str, any], task_close, _open, parent=None):
        super().__init__(parent)
        self.data: dict[str, any] = data
        self.name_ico: QLabel = QLabel(self)
        self.name_ico.setGeometry(15, 15, 30, 30)
        self.name_ico.setPixmap(picture(f'_資料夾'))
        # 檔案名稱
        self.file_name: QLabel = QLabel(data['name'], self)
        self.file_name.setFont(QFont("細明體", 9))
        self.file_name.move(55, 16)

        self.file_size: QLabel = QLabel(pybyte(int(data['size'])), self)
        self.file_size.setFont(QFont("細明體", 9))
        self.file_size.move(55, 37)
        self.file_size.setFixedWidth(100)
        self.file_size.setStyleSheet('color:rgba(50, 50, 50, 150)')
        # 設置傳輸進度容器
        self.ico: QFrame = QFrame(self)
        # 設置傳輸進度容器qss
        self.ico.setStyleSheet('background-color:rgb(255, 255, 255)')
        # 獲取y座標回調
        y = lambda height: int((56 - height) / 2)
        # 查看是否還在 下載中
        if data['status'] == 1:
            # 設置進度條
            progressbar = QProgressBar(self.ico)
            progressbar.setStyleSheet(
                'QProgressBar{border: 0px; background:rgb(200, 100, 200) ;'
                'background-color: rgb(229, 230, 234);color:rgb(60, 104, 137)}'
                'QProgressBar::chunk {background-color: rgb(6, 168, 255)}'
            )
            progressbar.setMaximum(100)
            progressbar.setGeometry(0, y(14), 152, 14)
            progressbar.setTextVisible(False)
            progressbar.setValue(int(data['percentDone']))
            MyIco('黑色關閉下載', '藍色關閉下載', coordinate=(190, y(10), 9, 10), state=True,
                  click=lambda: create_task(task_close(data['info_hash'])), parent=self.ico)
        # 查看是否 下載完畢
        elif data['status'] == 2:
            # 設置顯示狀態
            progresstext = QLabel(self.ico)
            progresstext.setFont(QFont("細明體", 12))
            progresstext.setGeometry(0, y(16), 152, 16)
            progresstext.setStyleSheet('color:rgba(50, 50, 50, 150)')
            progresstext.setText('下載完成')
            MyIco('黑色關閉下載', '藍色關閉下載', coordinate=(160, y(10), 9, 10), state=True,
                  click=lambda: create_task(task_close(data['info_hash'])), parent=self.ico)
            MyIco('黑色開啟資料夾', '藍色開啟資料夾', coordinate=(190, y(13), 14, 13), state=True,
                  click=lambda: create_task(_open(data['file_id'])), parent=self.ico)
        # 查看是否是 違規內容
        elif data['status'] == -1:
            progresstext = QLabel(self.ico)
            progresstext.setFont(QFont("細明體", 12))
            progresstext.setGeometry(0, y(16), 152, 16)
            progresstext.setStyleSheet('color:rgba(50, 50, 50, 150)')
            progresstext.setText('下載含有違規內容')
            MyIco('黑色關閉下載', '藍色關閉下載', coordinate=(190, y(10), 9, 10), state=True,
                  click=lambda: create_task(task_close(data['info_hash'])), parent=self.ico)
        # 邊框
        self.setObjectName('_frame')
        self.setStyleSheet('#_frame{border-style:solid;border-bottom-width:1;border-color: rgba(200, 200, 200, 125);'
                           'background-color: rgb(255, 255, 255)}')

    def resizeEvent(self, event):
        self.ico.setGeometry(self.width() - 240, 0, 360, 55)


class Offlinelist(QFrame):
    def __init__(
            self,
            directory: Directory,
            sidebar_1: Callable[[], None],
            network: Callable[[str], Awaitable[None]],
            parent: QObject
    ) -> None:
        super().__init__(parent)
        # 目錄操作
        self.directory: Directory = directory
        # 切換目錄
        self.sidebar_1: Callable[[], None] = sidebar_1
        # 網路
        self.network: Callable[[str], Awaitable[None]] = network
        # 所有Qtest
        self.allqtext: list[Qtext, ...] = []
        # 設置滾動區
        self.scrollarea: ScrollArea = ScrollArea(self)
        # 獲取滾動內容窗口
        self.scrollcontents: QFrame = self.scrollarea.scrollcontents
        # 關閉橫滾動條
        self.scrollarea.sethrizontal(False)
        # 根據名稱設置背景空白
        self.setStyleSheet(
            'Offlinelist{background-color:rgb(255, 255, 255);border-style:solid;'
            'border-left-width:1px; border-color:rgba(200, 200, 200, 125)}'
            'ScrollArea{border-style:solid;border-top-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )
        self.gui: QLabel = gif(self, '加載')

        MyQLabel('刷新', (10, 8, 111, 41), fontsize=16, clicked=lambda: create_task(self.refresh()), parent=self)
        MyQLabel('清空', (130, 8, 111, 41), fontsize=16, clicked=lambda: create_task(self.task_cls()), parent=self)

    def add(self, data: dict[str, any]) -> None:
        quantity = len(self.allqtext)
        qtext = Qtext(data, self.task_close, self.open, parent=self.scrollcontents)
        qtext.setGeometry(0, quantity * 56, self.width(), 56)
        qtext.show()
        self.scrollcontents.setGeometry(0, 0, self.width(), (quantity + 1) * 56)
        self.allqtext.append(qtext)

    # 切換至首頁 並到指定cid
    async def open(self, cid: str) -> None:
        # 切換首頁
        self.sidebar_1()
        # 進入指定目錄
        create_task(self.network(cid))

    def delete(self) -> None:
        self.scrollcontents.setParent(None)
        self.scrollcontents.deleteLater()
        self.scrollcontents = QFrame()
        self.scrollcontents.setGeometry(0, 0, self.width(), 0)
        self.scrollarea.setwidget(self.scrollcontents)
        self.scrollcontents.show()
        self.allqtext = []

    # 刪除指定離線任務
    async def task_close(self, value: str) -> None:
        if self.allqtext:
            self.delete()
        self.gui.show()
        await self.directory.offline_delete(value)
        await self.refresh()

    # 清除所有任務
    async def task_cls(self) -> None:
        self.gui.show()
        await self.directory.offline_clear()
        await self.refresh()

    async def refresh(self) -> None:
        self.gui.show()
        if self.allqtext:
            self.delete()
        tasks = await self.directory.offline_schedule()
        if tasks['tasks'] is not None:
            for task in tasks['tasks']:
                self.add(task)
        self.gui.hide()

    def raise_(self) -> None:
        QWidget.raise_(self)
        create_task(self.refresh())

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.scrollcontents.setGeometry(0, 0, self.width(), self.scrollcontents.height())
        for qtext in self.allqtext:
            qtext.setGeometry(0, qtext.y(), self.width(), 56)
        self.gui.move(int(self.width() / 2), int(self.height() / 2))
        self.scrollarea.setGeometry(0, 55, self.width(), self.height() - 55)

