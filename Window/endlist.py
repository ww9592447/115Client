from asyncio import create_task
from os.path import exists
from os import popen, startfile
from typing import Callable, Coroutine

from PyQt5.Qt import QWidget, QLabel, QFont, QFrame, QPalette, QColor, QResizeEvent

from MyQlist.MScroolBar import ScrollArea
from Modules.image import AllImage, Image
from Modules.widgets import MyIco


def get_text(image: Image) -> str:
    if image == Image.DOWNLOAD_COMPLETED:
        return '下載完成'
    elif image == Image.UPLOAD_COMPLETED:
        return '上傳完成'
    elif image == Image.COMPLETED:
        return '秒傳完成'


class Qtest(QFrame):
    def __init__(
            self,
            parent: QWidget,
            path: str,
            name: str,
            ico: Image,
            size: str,
            image: Image,
            sidebar_1: Callable[[], None],
            network: Callable[[str], Coroutine],
            cid: str | None = None,
    ) -> None:
        super().__init__(parent)
        # 選擇首頁窗口
        self.sidebar_1: Callable[[], None] = sidebar_1
        # 前進cid
        self.network: Callable[[str], Coroutine] = network
        # 如果是上傳則紀錄目錄cid
        self.cid: str | None = cid
        # 檔案路徑
        self.path: str = path
        # 設置副檔名圖案容器
        self.file_ico = QLabel(self)
        # 設置副檔名圖案容器大小位置
        self.file_ico.setGeometry(15, 15, 30, 30)
        ico: Image = getattr(Image, ico.name.replace('MIN', 'MAX'))
        # 設置副檔名圖案
        self.file_ico.setPixmap(AllImage.get_image(ico))

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

        # 設置圖標窗口
        self.ico = QWidget(self)
        # 設置狀態圖案窗口
        _ico = QLabel(self.ico)
        # 移動狀態圖案位置
        _ico.move(0, 0 if image == Image.COMPLETED else 2)
        # 設置狀態圖案
        _ico.setPixmap(AllImage.get_image(image))

        text = QLabel(self.ico)
        text.setFont(QFont("細明體", 9))
        text.move(20, 2)
        text.setText(get_text(image))
        text.setPalette(pe)

        MyIco(
            self.ico,
            Image.BLACK_OPEN_FILE,
            Image.BLUE_OPEN_FILE,
            coordinate=(97, 0, 13, 15),
            state=True,
            click=self.open_file
        )

        MyIco(
            self.ico,
            Image.BLACK_OPEN_FOLDER,
            Image.BLUE_OPEN_FOLDER,
            coordinate=(148, 1, 14, 13),
            state=True,
            click=self.open_folder
        )

        MyIco(
            self.ico,
            Image.BLACK_DELETE_DATA,
            Image.BLUE_DELETE_DATA,
            coordinate=(198, 0, 15, 16),
            state=True
        )

        self.setStyleSheet('Qtest{border-style:solid; border-bottom-width:1px; border-color:rgba(200, 200, 200, 125)'
                           '; background-color:rgb(255, 255, 255)}')

    def open_folder(self) -> None:
        if self.cid:
            self.sidebar_1()
            create_task(self.network(self.cid))
        elif exists(self.path):
            popen(f'explorer.exe /select, {self.path}')

    def open_file(self) -> None:
        if exists(self.path):
            startfile(self.path)

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.ico.move(self.width() - 293, 20)
        self.file_name.resize(self.width() - 350, 11)


class EndList(QFrame):
    def __init__(
            self,
            sidebar_1: Callable[[], None],
            network: Callable[[str], Coroutine],
            set_index: Callable[[int], None],
            parent: QWidget
    ) -> None:
        super().__init__(parent)
        # 設置滾動區
        self.scroll_area = ScrollArea(self)
        # 獲取滾動內容窗口
        self.scroll_contents = self.scroll_area.scroll_contents
        # 關閉橫滾動條
        self.scroll_area.set_horizontal(False)
        # 設置背景空白
        self.setStyleSheet(
            'EndList{background-color:rgb(255, 255, 255);border-style:solid;'
            'border-left-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )
        # 所有all_qtest
        self.all_test = []
        # 選擇首頁窗口
        self.sidebar_1 = sidebar_1
        # 網路
        self.network = network
        # 設定完成數量
        self.set_index = set_index

    # 添加
    def add(
        self,
        path: str,
        name: str,
        ico: Image,
        size: str,
        image: Image,
        cid: str | None = None
    ) -> None:
        text = Qtest(self.scroll_contents, path, name, ico, size, image, self.sidebar_1, self.network, cid=cid)
        text.show()
        self.all_test.insert(0, text)
        for _text, index in zip(self.all_test, range(len(self.all_test))):
            _text.setGeometry(0, index * 56, self.width() - 2, 56)
        self.scroll_contents.setGeometry(0, 0, self.width() - 2, len(self.all_test) * 56)
        self.set_index(len(self.all_test))

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.scroll_area.resize(self.size())
        self.scroll_contents.setGeometry(0, 0, self.width() - 2, self.scroll_contents.height())
        for progressBar in self.all_test:
            progressBar.setGeometry(0, progressBar.y(), self.width() - 2, 56)
