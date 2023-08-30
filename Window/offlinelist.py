from typing import Callable, Coroutine
from asyncio import create_task

from PyQt5.Qt import QWidget, QFrame, QResizeEvent, QProgressBar, QFont, QLabel

from Modules.image import AllImage, Image, GifLabel, GifImage
from MyQlist.MScroolBar import ScrollArea
from Modules.widgets import MyIco, MyPushButton
from Modules.get_data import pybyte
from API.offline import Offline


class QText(QFrame):
    def __init__(self, data: dict[str, any], task_close, _open, parent: QWidget) -> None:
        super().__init__(parent)
        self.data: dict[str, any] = data
        self.name_ico: QLabel = QLabel(self)
        self.name_ico.setGeometry(15, 15, 30, 30)
        self.name_ico.setPixmap(AllImage.get_image(Image.MAX_FOLDER))
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
            MyIco(self.ico, Image.BLACK_CLOSE, Image.BLUE_CLOSE, coordinate=(190, y(10), 9, 10), state=True,
                  click=lambda: create_task(task_close(data['info_hash'])))
        # 查看是否 下載完畢
        elif data['status'] == 2:
            # 設置顯示狀態
            progresstext = QLabel(self.ico)
            progresstext.setFont(QFont("細明體", 12))
            progresstext.setGeometry(0, y(16), 152, 16)
            progresstext.setStyleSheet('color:rgba(50, 50, 50, 150)')
            progresstext.setText('下載完成')
            MyIco(
                self.ico, Image.BLACK_CLOSE, Image.BLUE_CLOSE, coordinate=(160, y(10), 9, 10), state=True,
                click=lambda: create_task(task_close(data['info_hash']))
            )

            MyIco(
                self.ico, Image.BLACK_OPEN_FOLDER, Image.BLUE_OPEN_FOLDER, coordinate=(190, y(13), 14, 13), state=True,
                click=lambda: create_task(_open(data['file_id']))
            )
        # 查看是否是 違規內容
        elif data['status'] == -1:
            progresstext = QLabel(self.ico)
            progresstext.setFont(QFont("細明體", 12))
            progresstext.setGeometry(0, y(16), 152, 16)
            progresstext.setStyleSheet('color:rgba(50, 50, 50, 150)')
            progresstext.setText('下載含有違規內容')
            MyIco(
                self.ico,Image.BLACK_CLOSE, Image.BLUE_CLOSE, coordinate=(190, y(10), 9, 10), state=True,
                click=lambda: create_task(task_close(data['info_hash']))
            )
        # 邊框
        self.setStyleSheet('QText{border-style:solid;border-bottom-width:1;border-color: rgba(200, 200, 200, 125);'
                           'background-color: rgb(255, 255, 255)}')

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.ico.setGeometry(self.width() - 240, 0, 360, 55)


class OfflineList(QFrame):
    def __init__(
            self,
            offline: Offline,
            sidebar_1: Callable[[], None],
            network: Callable[[str], Coroutine],
            parent: QWidget
    ) -> None:
        super().__init__(parent)
        # 目錄操作
        self.offline: Offline = offline
        # 切換目錄
        self.sidebar_1: Callable[[], None] = sidebar_1
        # 網路
        self.network: Callable[[str], Coroutine] = network
        # 所有Qtest
        self.all_text: list[QText, ...] = []
        # 設置滾動區
        self.scroll_area: ScrollArea = ScrollArea(self)
        # 獲取滾動內容窗口
        self.scroll_contents: QFrame = self.scroll_area.scroll_contents
        # 關閉橫滾動條
        self.scroll_area.set_horizontal(False)
        # 根據名稱設置背景空白
        self.setStyleSheet(
            'OfflineList{background-color:rgb(255, 255, 255);border-style:solid;'
            'border-left-width:1px; border-color:rgba(200, 200, 200, 125)}'
            'ScrollArea{border-style:solid;border-top-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )
        self.load: GifLabel = AllImage.get_gif(self, GifImage.MIN_LOAD)
        self.load.resize(32, 32)

        MyPushButton(self, '刷新', (10, 8, 111, 41), font_size=16, qss=2, click=lambda: create_task(self.refresh()))
        MyPushButton(self, '清空', (130, 8, 111, 41), font_size=16, qss=2, click=lambda: create_task(self.task_cls()))

    def add(self, data: dict[str, any]) -> None:
        quantity = len(self.all_text)
        text = QText(data, self.task_close, self.open, parent=self.scroll_contents)
        text.setGeometry(0, quantity * 56, self.width(), 56)
        text.show()
        self.scroll_contents.setGeometry(0, 0, self.width(), (quantity + 1) * 56)
        self.all_text.append(text)

    # 切換至首頁 並到指定cid
    async def open(self, cid: str) -> None:
        # 切換首頁
        self.sidebar_1()
        # 進入指定目錄
        create_task(self.network(cid))

    def delete(self) -> None:
        self.scroll_contents.setParent(None)
        self.scroll_contents.deleteLater()
        self.scroll_contents = QWidget()
        self.scroll_contents.setGeometry(0, 0, self.width(), 0)
        self.scroll_area.set_widget(self.scroll_contents)
        self.scroll_contents.show()
        self.all_text = []

    # 刪除指定離線任務
    async def task_close(self, value: str) -> None:
        if self.all_text:
            self.delete()
        self.load.show()
        await self.offline.offline_delete(value)
        await self.refresh()

    # 清除所有任務
    async def task_cls(self) -> None:
        self.load.show()
        await self.offline.offline_clear()
        await self.refresh()

    async def refresh(self) -> None:
        self.load.show()
        if self.all_text:
            self.delete()
        tasks = await self.offline.offline_schedule()
        if tasks['tasks'] is not None:
            for task in tasks['tasks']:
                self.add(task)
        self.load.hide()

    def raise_(self) -> None:
        QWidget.raise_(self)
        create_task(self.refresh())

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.scroll_contents.setGeometry(0, 0, self.width(), self.scroll_contents.height())
        for text in self.all_text:
            text.setGeometry(0, text.y(), self.width(), 56)
        self.load.move(int(self.width() / 2), int(self.height() / 2))
        self.scroll_area.setGeometry(0, 55, self.width(), self.height() - 55)

