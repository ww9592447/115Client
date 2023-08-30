from typing import Self

from PyQt5.Qt import QWidget, Qt, QLabel, QFont, QContextMenuEvent, QMouseEvent, QFontMetrics

from Modules.type import NTextData, NlistData, NMyTextData, MyTextSlots, NTextSlots
from Modules.image import AllImage
from Modules.widgets import MyLabel, MyFrame


class TextSave:
    # 所有 text資料 [page, list[TextData]
    text: dict[int, list[NTextData, ...]]

    def __init__(self):
        # 初始化 text資料
        self.text = {1: []}

    # 清空資料
    def cls(self) -> None:
        # 初始化 所有 text 資料
        for text in self.text.values():
            text.clear()

    # 初始化資料
    def initialization(self) -> None:
        # 初始化 所有 text 資料
        self.text.clear()
        # 設置新數值
        self.text[1] = []


class TextSaveList:

    text_save: TextSave
    # 頁數上限
    max: int
    # qlist資料
    nlist_data: NlistData

    def __init__(self, nlist_data: NlistData) -> None:
        self.max: int = nlist_data['quantity_limit']
        # 設置所有text資料
        self.save: dict[str | None, TextSave] = {}
        self.nlist_data: NlistData = nlist_data
        # 設置目前text資料
        self.text_save: TextSave = TextSave()
        self.save[None] = self.text_save

    def new_text_contents(self, name: str) -> None:
        self.text_save: TextSave = TextSave()
        self.save[name] = self.text_save
        self.nlist_data['scroll_contents'].resize(
            self.nlist_data['scroll_contents'].width(), 0
        )

    def switch_text_contents(self, name: str) -> None:
        self.text_save = self.save[name]

    def cls(self) -> None:
        self.text_save.cls()

    # 更新text資料
    def refresh_text_save(self, data: list[NTextData, ...]) -> None:
        self.text_save.text[self.nlist_data['page']] = data

    # 設置最大頁數
    def set_max_page(self, index: int) -> None:
        for value in range(len(self.text_save.text) + 1, index + 1):
            # 設置最大頁數
            self.text_save.text[value] = []

    # 獲取 目前多少頁
    def page_size(self) -> int:
        return len(self.text_save.text)

    def get_text(self, index: int) -> NTextData:
        return self.text_save.text[self.nlist_data['page']][index]


class MyText(MyLabel):
    def __init__(self, parent: QWidget, font: QFont) -> None:
        super().__init__(parent)
        # 保存 自身 數據
        self.data: NMyTextData = NMyTextData(text='', color=None, mouse=None)
        # 設定標題字體大小
        self.setFont(font)

    def set_slots(self, my_text_slots: MyTextSlots):
        # 查看是否要解除左鍵單擊信號
        if my_text_slots['disconnect_left_click']:
            # 獲取所有解除信號
            for click in my_text_slots['disconnect_left_click']:
                # 全部解除 左鍵點擊信號
                self.left_click.disconnect(click)
        # 查看是否要連接左鍵單擊信號
        if my_text_slots['connect_left_click']:
            # 獲取所有連接信號
            for slot in my_text_slots['connect_left_click']:
                # 連接 新的 左鍵點擊信號
                self.left_click.connect(slot)

    def refresh(self, data: NMyTextData) -> None:
        # 查看是否要設定滑鼠移動到上方顏色
        if self.data['color'] != data['color'] and data['color']:
            # 設置text 預設顏色 滑動到上方顏色
            self.setStyleSheet(
                f'MyText{{color: rgb{data["color"][0]}}}'
                f'MyText:hover{{color: rgb{data["color"][1]}}}'
            )
        # 查看使否要取消顏色
        elif self.data['color'] and data['color'] is None:
            self.setStyleSheet('')
        # 查看是否設定成可點擊
        if self.data['mouse'] != data['mouse']:
            if data['mouse']:
                # 滑鼠設定成可點擊圖標
                self.setCursor(Qt.PointingHandCursor)
            else:
                # 滑鼠還原
                self.setCursor(Qt.ArrowCursor)
        self.setText(data['text'])
        self.adjustSize()
        # 更新數據
        self.data.update(**data)

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            if self.data['mouse']:
                self.left_click.emit(self.parentWidget())
        # 右鍵
        elif event.buttons() == Qt.RightButton:
            if self.data['mouse']:
                self.right_click.emit(self.parentWidget())
        event.ignore()


class Text(MyFrame):
    def __init__(
            self,
            parent: QWidget,
            nlist_data: NlistData,
            index: int,
            text_save_list: TextSaveList,
            font: QFont,
    ) -> None:

        super().__init__(parent)
        # 設置自身資料
        self.text_data: NTextData = NTextData(
            data=None, ico=None, mouse=False, text=NMyTextData(mouse=None, color=None, text='')
        )
        # 設置自身編號
        self.index: int = index
        # 設置所有qlist資料
        self.nlist_data: NlistData = nlist_data
        # 設置所有text資料
        self.text_save_list = text_save_list
        # 設定發射窗口
        self.slot: Text = self
        # 設置自身ico圖案UI
        self.ico_image: QLabel = QLabel(self)
        # 設置自身ico圖案UI隱藏
        self.ico_image.hide()
        # 設置子text y座標 位置
        self._y: int = int((nlist_data['text_height_max'] - QFontMetrics(font).height()) / 2)
        # 設置子text
        self.text: MyText = MyText(self, font)
        # 設置 子text y座標 位置
        self.text.move(0, self._y)
        # 設定選中狀態qss屬性
        self.setProperty('state', False)
        # 設置 qss
        self.setStyleSheet(
            'Text{background-color: white}'
            'Text:hover{background-color: rgb(249, 250, 251)}'
            'Text[state="true"]{background-color: rgb(234, 246, 253)}'
        )

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if len(self.nlist_data['menu']):
            if self.nlist_data['menu_callable']:
                if self.nlist_data['menu_callable']():
                    self.nlist_data['context_menu'].exec(event.globalPos())
            else:
                self.nlist_data['context_menu'].exec(event.globalPos())

    def radio(self) -> None:
        if self.nlist_data['first_click'] is not None:
            self.nlist_data['first_click'].set_state(False)
        self.nlist_data['first_click'] = self
        self.set_state(not self.property('state'))

    def set_state(self, state: bool) -> None:
        # 設置本身狀態
        self.state = state
        # 設定背景顏色
        self.setProperty('state', state)
        # 刷新QSS
        self.setStyle(self.style())

    def set_slots(self, text_slots: NTextSlots) -> None:
        # 查看是否要解除左鍵單擊信號
        if text_slots['disconnect_left_click']:
            # 獲取所有解除信號
            for click in text_slots['disconnect_left_click']:
                # 全部解除 左鍵點擊信號
                self.left_click.disconnect(click)
        # 查看是否要解除左鍵雙擊信號
        if text_slots['disconnect_double_click']:
            # 獲取所有解除信號
            for click in text_slots['disconnect_double_click']:
                # 全部解除 左鍵點擊信號
                self.double_click.disconnect(click)
        # 查看是否要連接左鍵單擊信號
        if text_slots['connect_left_click']:
            # 獲取所有連接信號
            for slot in text_slots['connect_left_click']:
                # 連接 新的 左鍵點擊信號
                self.left_click.connect(slot)
        # 查看是否要連接左鍵雙擊信號
        if text_slots['connect_double_click']:
            # 獲取所有連接信號
            for slot in text_slots['connect_double_click']:
                # 連接 新的 左鍵點擊信號
                self.double_click.connect(slot)
        self.text.set_slots(text_slots['text'])

    def refresh(self) -> None:
        # 獲取自身資料
        text_save: NTextData = self.text_save_list.get_text(self.index)

        if text_save['ico'] and text_save['ico'] != self.text_data['ico']:
            # 獲取相應圖標
            image = AllImage.get_image(text_save['ico'])
            # 設定圖標圖片
            self.ico_image.setPixmap(image)
            # 設置圖標大小
            self.ico_image.resize(image.size())
            # 設置圖標位置
            self.ico_image.move(
                10, int((self.nlist_data['text_height_max'] - self.ico_image.height()) / 2)
            )
            # 圖標顯示
            self.ico_image.show()
            self.text.move(self.ico_image.x() + self.ico_image.width() + 10, self._y)

        elif text_save['ico'] is None and self.ico_image.isVisible():

            self.ico_image.hide()
            self.text.move(10, self._y)

        self.text.refresh(text_save['text'])

        # 更新自身資料
        self.text_data: NTextData = text_save

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            self.radio()
            if self.text_data['mouse']:
                self.left_click.emit(self)
        # 右鍵
        elif event.buttons() == Qt.RightButton:
            self.radio()
            if self.text_data['mouse']:
                self.right_click.emit(self)

    # 雙擊
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if self.text_data['mouse']:
            self.double_click.emit(self)


class QText:
    # 所有text
    text_list: list[Text, ...] = []

    def __init__(self, nlist_data: NlistData) -> None:
        self.nlist_data: NlistData = nlist_data
        self.text_save_list: TextSaveList = TextSaveList(nlist_data)
        self.text_name: str | None = None
        # 獲取字體設置
        font: QFont = QFont()
        # 設置字體大小
        font.setPointSize(15)

        for index in range(nlist_data['quantity_limit']):
            text = Text(
                nlist_data['scroll_contents'], nlist_data,
                index, self.text_save_list, font)
            # 設置位置
            text.setGeometry(
                0, len(self.text_list) * nlist_data['text_height_max'],
                nlist_data['scroll_contents'].width(), nlist_data['text_height_max']
            )
            # text顯示
            text.show()
            self.text_list.append(text)

    def new_text_contents(self, name: str) -> None:
        self.text_save_list.new_text_contents(name)
        self.text_save_list.switch_text_contents(name)
        self.text_name: str | None = name

    def switch_text_contents(self, name: str) -> None:
        self.text_save_list.switch_text_contents(name)
        self.text_name: str | None = name

    def add_text(self, text: list[NTextData, ...]) -> None:
        self.text_save_list.refresh_text_save(text)

    # 獲取 指定or目前 頁數 text數量
    def get_text_size(self, index: int = None) -> int:
        if index:
            if index in self.text_save_list.text_save.text:
                return len(self.text_save_list.text_save.text[index])
            else:
                return 0
        else:
            if self.nlist_data['page'] in self.text_save_list.text_save.text:
                return len(self.text_save_list.text_save.text[self.nlist_data['page']])
            else:
                return 0

    def set_text_slots(self, text_slots: list[NTextSlots]) -> None:
        for index, slots in enumerate(text_slots):
            self.text_list[index].set_slots(slots)