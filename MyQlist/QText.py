from typing import Callable

from PyQt5.Qt import QFrame, pyqtSignal, QWidget, QCursor, QMenu, Qt, QApplication, QLabel, QFont, QObject,\
    QMouseEvent, QContextMenuEvent

from Modules.type import QlistData, TextData, MyTextData, MyTextSlots, TextSlots, MyDict
from Modules.image import AllImage
from Modules.widgets import ClickLabel, MyLabel, MyFrame


# 複選紐
class TextClickLabel(ClickLabel):
    def __init__(
            self,
            parent: QWidget,
            vbox_left_select: Callable[['Text'], None],
            vbox_right_select: Callable[['Text'], None]
    ) -> None:
        super().__init__(parent)
        # 設置複選紐左鍵點擊回調
        self.vbox_left_select: Callable[['Text'], None] = vbox_left_select
        # 設置複選紐右鍵點擊回調
        self.vbox_right_select: Callable[['Text'], None] = vbox_right_select

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            self.vbox_left_select(self.parentWidget())
        # 右鍵
        elif event.buttons() == Qt.RightButton:
            self.vbox_right_select(self.parentWidget())


# 可觸碰移動條
class MovingBar(QWidget):
    # 移動條移動信號
    mouse_move = pyqtSignal(str, QMouseEvent)

    def __init__(self, parent: QWidget, name: str, least: int) -> None:
        super().__init__(parent)
        # 設置 自身標題
        self.name: str = name
        # 設置 標題最小寬度
        self.least: int = least
        # 設置 左右移動直線滑鼠箭頭
        self.setCursor(QCursor(Qt.SizeHorCursor))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.mouse_move.emit(self.name, event)


class Title(QFrame):
    def __init__(self, parent: QWidget, moving_bar: MovingBar, qlist_data: QlistData, name: str) -> None:
        super().__init__(parent)
        # 設置 標題文字UI
        self.title_text = QLabel(self)
        # 設置移動條
        self.moving_bar = moving_bar
        # 設置標題文字UI
        self.title_text: QLabel = QLabel(self)
        # 紀錄標題文字
        self.name: str = name
        # 獲取QT 字體設置
        font = QFont()
        # 設置字體大小
        font.setPointSize(9)
        # 設定標題字體大小
        self.title_text.setFont(font)
        # 設定文字
        self.title_text.setText(name)
        # 自動適應大小
        self.title_text.adjustSize()
        # 設置標題文字UI位置
        self.title_text.move(
            qlist_data['title_interval'],
            int((qlist_data['title_max'] - self.title_text.height()) / 2)
        )
        # 設定是否顯示背景屬性
        self.setProperty('backdrop', False)
        # 設置右側邊框, 背景顏色
        self.setStyleSheet('Title{border-style:solid; border-right-width:1px;'
                           'border-right-color:rgba(200, 200, 200, 125)}'
                           'Title[backdrop="true"]{background-color: rgb(246, 248, 251)}')


class TextDataList:
    def __init__(self, text_data_list: list[TextData, ...]):
        # 設定text資料
        self.text_data_list: list[TextData, ...] = text_data_list
        # 設定以讀取text數量
        self.read: int = 0

    def size(self) -> int:
        return len(self.text_data_list)

    def __getitem__(self, index: int) -> TextData:
        return self.text_data_list[index]


class TextSave:
    def __init__(self) -> None:
        # 設置text資料
        self.text: dict[int, TextDataList] = {1: TextDataList([])}
        # 設置標題
        self.title: MyDict[Title] = MyDict()

    # 清空資料
    def cls(self) -> None:
        for text in self.text.values():
            text.text_data_list.clear()
            text.read = 0

    # 更新標題
    def renew_title(self, title: MyDict[Title]) -> None:
        # 更新標題
        self.title: MyDict[Title] = title


class TextSaveList:
    def __init__(self, qlist_data: QlistData) -> None:
        # 設置所有標題
        self.title_all: MyDict[Title] = MyDict()
        # 設置目前標題
        self.title: MyDict[Title] = MyDict()
        # 設置所有text資料
        self.save: dict[str | None, TextSave] = {}
        # 設置頁數上限
        self.max: int = qlist_data['quantity_limit']
        # 設置所有qlist資料
        self.qlist_data: QlistData = qlist_data
        # 設置目前text資料
        self.text_save = TextSave()
        # 儲存目前text資料
        self.save[None] = self.text_save

    def new_text_contents(self, name: str) -> None:
        self.text_save: TextSave = TextSave()
        self.save[name] = self.text_save
        self.text_save.renew_title(self.title)
        self.qlist_data['scroll_contents'].resize(
            self.qlist_data['scroll_contents'].width(), 0
        )

    def switch_text_contents(self, name: str) -> None:
        self.text_save: TextSave = self.save[name]
        self.title = self.text_save.title

    # 更新text資料
    def refresh_text_save(self, data: list[TextData, ...]) -> None:
        self.text_save.text[self.qlist_data['page']] = TextDataList(data)

    # 獲取text以刷新數量
    def get_read(self) -> int:
        return self.text_save.text[self.qlist_data['page']].read

    # 設定text刷新數量
    def set_read(self, value: int) -> None:
        self.text_save.text[self.qlist_data['page']].read = value

    def cls(self) -> None:
        self.text_save.cls()

    def title_append(self, name: str, title: Title) -> None:
        self.title_all[name] = title
        self.title[name] = title

    def set_title_visible(self, name: str, visible: bool):
        if name in self.title_all:
            if visible:
                if name not in self.title:
                    self.title[name] = self.title_all[name]
                    self.title.sort(self.title_all)
            else:
                if name in self.title:
                    self.title.remove(name)

    def title_index(self, title: str) -> int:
        return self.title.index(title)

    def title_all_index(self, title: str) -> int:
        return self.title_all.index(title)

    def title_size(self) -> int:
        return len(self.title)

    # 設置最大頁數
    def set_max_page(self, index: int) -> None:
        for value in range(len(self.text_save.text) + 1, index + 1):
            # 設置最大頁數
            self.text_save.text[value] = TextDataList([])

    # 獲取 指定or目前 頁數 text數量
    def get_text_size(self, index: int = None) -> int:
        if index:
            if index in self.text_save.text:
                return self.text_save.text[index].size()
            else:
                return 0
        else:
            if self.qlist_data['page'] in self.text_save.text:
                return self.text_save.text[self.qlist_data['page']].size()
            else:
                return 0

    # 獲取 目前多少頁
    def page_size(self) -> int:
        return len(self.text_save.text)

    # 獲取 目前頁數text資料
    def get_text(self, index: int) -> TextData:
        return self.text_save.text[self.qlist_data['page']][index]

    # 獲取 目前標題index的標題
    def get_index_title(self, index: int) -> Title:
        return self.title[index]

    # 獲取 所有標題index的標題
    def get_index_title_all(self, index: int) -> Title:
        return self.title_all[index]

    # 獲取 目前標題name的標題
    def get_name_title(self, name: str) -> Title:
        return self.title[name]

    # 獲取 所有標題name的標題
    def get_name_title_all(self, name: str) -> Title:
        return self.title_all[name]


class MyText(MyLabel):
    def __init__(self, parent: QWidget, qlist_data: QlistData,) -> None:
        super().__init__(parent)
        # 設置自身資料
        self.data: MyTextData = MyTextData(text='', color=None, mouse=None, text_size=[])
        # 原本寬度
        self.text_width: int = 0
        # 文字最大大小
        self.text_height_max: int = 0
        # 設置間隔符號
        self.spacer_symbol: str = qlist_data['spacer_symbol']
        # 設置間隔符號總大小
        self.spacer_symbol_size: int = qlist_data['spacer_symbol_size']
        # 設置間隔空白數量
        self.spacer_space: int = qlist_data['spacer_space']
        # 設置間隔空白總大小
        self.spacer_space_size: int = qlist_data['spacer_space_size']
        # 設置要發送的窗口
        self.slot: QWidget = self.parentWidget()

    def set_slots(self, my_text_slots: MyTextSlots) -> None:
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

    def refresh(self, data: MyTextData) -> None:
        # 設定最大文字寬度大小
        self.text_height_max = self.fontMetrics().horizontalAdvance(data['text'])
        if data['text'] and not data['text_size']:
            # 初始化文字大小
            size = 0
            # 獲取全部文字順序大小
            for char in data['text']:
                # 獲取文字大小
                size = size + self.fontMetrics().horizontalAdvance(char)
                # 添加文字大小 位置
                data['text_size'].append(size)
            # 文字大小翻轉 從大到小
            data['text_size'].reverse()
        # 設置可調整的最大寬度
        self.setMaximumWidth(self.text_height_max)
        # 查看是否要設定滑鼠移動到上方顏色
        if self.data['color'] != data['color'] and data['color'] and isinstance(data['color'][0], tuple):
            # 設置text 預設顏色 滑動到上方顏色
            self.setStyleSheet(
                f'MyText{{color: rgb{data["color"][0]}}}'
                f'MyText:hover{{color: rgb{data["color"][1]}}}'
            )
        elif self.data['color'] != data['color'] and data['color'] and isinstance(data['color'][0], int):
            # 設置text 預設顏色
            self.setStyleSheet(f'MyText{{color: rgb{data["color"]}}}')
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
        # 更新數據
        self.data.update(**data)

    def resize_(self, w: int, h: int) -> None:
        text = self.data['text']
        if text:
            # 紀錄原本寬度
            self.text_width = w
            # 查看文字大小 + 間隔空白大小 是否大於 寬度 如果大於設定新文字
            if self.text_height_max + self.spacer_space_size > self.text_width:
                index = len(self.data['text_size'])
                # 獲取文字大小
                for size in self.data['text_size']:
                    # 查看目前文字大小 + 間隔符號大小 + 間隔空白大小 是否小於寬度 如果小於就重新設定文字
                    if size + self.spacer_symbol_size + self.spacer_space_size < self.text_width:
                        # 設定文字
                        text = self.data['text'][0:index] + self.spacer_symbol
                        # 獲取文字大小
                        w = size + self.spacer_symbol_size
                        break
                    index -= 1
        # 如果文字不同就設置新文字
        if self.text() != text:
            # 設定文字
            self.setText(text)
        # 調整大小
        self.resize(w, h)

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
            qlist_data: QlistData,
            text_save_list: TextSaveList,
            index: int,
            text_left_select: Callable[['Text'], None],
            text_right_select: Callable[['Text'], None],
            vbox_left_select: Callable[['Text'], None],
            vbox_right_select: Callable[['Text'], None]
    ) -> None:
        super().__init__(parent)
        # 設置自身資料
        self.text_data: TextData = TextData(
            data=None, ico=None, my_text={}, mouse=False
        )
        # 設置第一個子text x 座標
        self.child_text_x: int = 0
        # 設置紀錄是否已選中
        self.state: bool = False
        # 設置記錄所有子text
        self.child_text: dict[str, MyText] = {}
        # 設置所有text資料
        self.text_save_list: TextSaveList = text_save_list
        # 設置自身編號
        self.index: int = index
        # 設置所有qlist資料
        self.qlist_data: QlistData = qlist_data
        #  設置text左鍵點擊回調
        self.text_left_select: Callable[['Text'], None] = text_left_select
        # 設置text右鍵點擊回調
        self.text_right_select: Callable[['Text'], None] = text_right_select
        # 設置自身ico圖案UI
        self.ico_image: QLabel = QLabel(self)
        # 設置自身ico圖案UI隱藏
        self.ico_image.hide()
        # 設置複選紐
        self.check_button: TextClickLabel = TextClickLabel(self, vbox_left_select, vbox_right_select)
        # 把複選鈕置中
        self.check_button.move(5, int((qlist_data['text_height_max'] - self.check_button.height()) / 2))
        # 設置右鍵菜單
        self.context_menu: QMenu = QMenu(self)
        # 設定選中狀態qss屬性
        self.setProperty('state', False)
        # 設置 qss
        self.setStyleSheet(
            'Text{background-color: white}'
            'Text:hover{background-color: rgba(249, 250, 251, 200)}'
            'Text[state="true"]{background-color: rgba(234, 246, 253, 200)}'
        )

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if len(self.qlist_data['menu']):
            if self.qlist_data['menu_callable']:
                if self.qlist_data['menu_callable']():
                    self.qlist_data['context_menu'].exec(event.globalPos())
            else:
                self.qlist_data['context_menu'].exec(event.globalPos())

    def set_child_text(self, title: Title) -> None:
        if title.name in self.child_text:
            my_text = self.child_text[title.name]
        else:
            # 獲取空白text
            my_text = MyText(self, self.qlist_data)
            # 設置字體大小
            my_text.setFont(self.qlist_data['font'])
            # 新增空白text
            self.child_text[title.name] = my_text

        if not self.text_save_list.title_index(title.name) and not self.ico_image.isHidden():
            # 設置子Text x位置
            self.child_text_x = self.ico_image.x() + self.ico_image.width() + 10
            # 設定子Text 座標
            my_text.move(self.child_text_x, self.qlist_data['my_text_y'])
            # 設定子Text 大小
            my_text.resize_(
                title.x() + title.width() - self.child_text_x,
                my_text.fontMetrics().height()
            )
        else:
            # 設定子Text 座標
            my_text.move(title.x(), self.qlist_data['my_text_y'])
            # 設定子Text 大小
            my_text.resize_(title.width(), my_text.fontMetrics().height())

    def set_slots(self, text_slots: TextSlots) -> None:
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

        for title in self.text_save_list.title_all:
            if title.name in text_slots['my_text']:
                my_text = self.child_text[title.name]
                my_text.set_slots(text_slots['my_text'][title.name])

    def refresh(self) -> None:
        # 獲取自身資料
        text_save: TextData = self.text_save_list.get_text(self.index)

        if text_save['ico'] and text_save['ico'] != self.text_data['ico']:
            # 獲取相應圖標
            ico = AllImage.get_image(text_save['ico'])
            # 設定圖標圖片
            self.ico_image.setPixmap(ico)
            # 設置圖標大小
            self.ico_image.resize(ico.size())
            # 設置圖標位置
            self.ico_image.move(
                self.check_button.x() + self.check_button.width() + 10,
                int((self.qlist_data['text_height_max'] - self.ico_image.height()) / 2)
            )
            # 圖標顯示
            self.ico_image.show()
        elif text_save['ico'] is None and self.ico_image.isVisible():
            self.ico_image.hide()

        for title in self.text_save_list.title:
            my_text = self.child_text[title.name]
            if title.name in text_save['my_text']:
                data: MyTextData = text_save['my_text'][title.name]
            else:
                data: MyTextData = MyTextData(
                    text='', color=None, mouse=False, text_size=[]
                )
            my_text.refresh(data)

            self.set_child_text(title)
        # 更新自身資料
        self.text_data: TextData = text_save

    # 滑鼠單擊事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            self.text_left_select(self)
            if self.text_data['mouse']:
                self.left_click.emit(self)
        # 右鍵
        elif event.buttons() == Qt.RightButton:
            self.text_right_select(self)
            if self.text_data['mouse']:
                self.right_click.emit(self)

    # 雙擊
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if self.text_data['mouse']:
            self.double_click.emit(self)


class QTitle(QFrame):
    def __init__(self, parent: QWidget, title_max: int) -> None:
        super().__init__(parent)
        # 設置標題複選紐
        self.click_label = ClickLabel(parent)
        # 設置標題複選紐位置
        self.click_label.move(5, int((title_max - self.click_label.image[True].height()) / 2))
        # 禁止傳遞事件給父代  為了防止背景右鍵菜單傳遞
        self.setAttribute(Qt.WA_NoMousePropagation, True)
        # 標題移動到內容窗口相同位置
        self.move(1, 0)
        # 設置標題下方邊框
        self.setStyleSheet('QTitle{border-style:solid; border-bottom-width:1px;'
                           'border-color:rgba(200, 200, 200, 125)}')


class QText(QObject):
    # 更改點擊數量信號
    change_quantity = pyqtSignal(int)

    def __init__(self, all_widget: QWidget, qlist_data: QlistData) -> None:
        super().__init__()
        # 設置所有qlist資料
        self.qlist_data: QlistData = qlist_data
        # 設置目前text資料
        self.text_save_list: TextSaveList = TextSaveList(qlist_data)
        # 設置所有已點選text
        self.current_click: list[Text, ...] = []
        # 設置所有text
        self.text_list: list[Text, ...] = []
        # 設置標題容器
        self.title = QTitle(
            all_widget, qlist_data['title_max']
        )
        # 設置目前text資料名稱
        self.text_name: str | None = None
        # 設置複選紐 點擊 信號
        self.title.click_label.left_click.connect(self.set_all_state)
        for index in range(qlist_data['quantity_limit']):
            text = Text(
                qlist_data['scroll_contents'],
                qlist_data,
                self.text_save_list,
                index,
                self.text_left_select,
                self.text_right_select,
                self.vbox_left_select,
                self.vbox_right_select,
            )
            # 設置位置
            text.setGeometry(
                0, len(self.text_list) * qlist_data['text_height_max'],
                qlist_data['scroll_contents'].width(), qlist_data['text_height_max']
            )
            # text顯示
            text.show()
            self.text_list.append(text)

    def new_text_contents(self, name: str) -> None:
        self.text_save_list.set_read(0)
        self.text_save_list.new_text_contents(name)
        self.text_save_list.switch_text_contents(name)
        self.text_name: str | None = name

    def switch_text_contents(self, name: str) -> None:
        self.text_save_list.set_read(0)
        self.text_save_list.switch_text_contents(name)
        self.text_name: str | None = name

    def add_text(self, text: list[TextData, ...]) -> None:
        self.text_save_list.refresh_text_save(text)

    def set_text_slots(self, text_slots: list[TextSlots]) -> None:
        for index, slots in enumerate(text_slots):
            self.text_list[index].set_slots(slots)

    def initialization_text(self) -> None:
        self.qlist_data['scroll_contents'].resize(
            self.qlist_data['scroll_contents'].width(),
            0
        )

    def title_add(self, name: str, width: int = 50, least: int = 50) -> None:
        # 如果預設寬度小於 最小寬度 則把預設寬度調整成 最小寬度
        if width < least:
            width = least
        # 設定可觸碰移動條
        moving_bar: MovingBar = MovingBar(self.title, name, least)
        moving_bar.mouse_move.connect(self.moving_bar_mouse_move)
        # 設置標題
        title: Title = Title(self.title, moving_bar, self.qlist_data, name)
        # 查看標題是不是第一個
        if self.text_save_list.title_size() == 0:
            # 設置第一格標題位置
            title.setGeometry(23, 0, width, self.qlist_data['title_max'])
        else:
            # 獲取最後一個標題
            _title: Title = self.text_save_list.get_index_title(-1)
            # 從上一個標題獲取資料設定標題大小位置
            title.setGeometry(_title.x() + _title.width(), 0, width, self.qlist_data['title_max'])
        # 設定移動條大小位置
        moving_bar.setGeometry(
            title.x() + title.width() - (int(self.qlist_data['title_moving_bar_size'] / 2) + 1),
            0, self.qlist_data['title_moving_bar_size'], title.height()
        )
        # 設置內容窗口寬度大小
        self.qlist_data['scroll_contents'].resize(
            title.x() + title.width(),
            self.qlist_data['scroll_contents'].height()
        )
        # 顯示標題
        title.show()
        # 標題往下層移動 防止擋住可觸碰移動條
        title.lower()
        # 可動移動條顯示
        moving_bar.show()
        # 插入標題  name 顯示文字 title 文字容器 line 可觸碰移動條 None 點擊事件
        self.text_save_list.title_append(name, title)
        for text in self.text_list:
            # 新增 新的 子text
            text.set_child_text(title)
            # 讓所有的 text 保持跟 內容窗口相同寬度
            text.resize(self.qlist_data['scroll_contents'].width(), text.height())
            # 獲取 自身標題符合的 子text
            my_text: MyText = text.child_text[title.name]
            # 調整 子text 寬度
            my_text.resize(title.x() + title.width() - my_text.x(), my_text.height())

    def set_title_visible(self, title: Title, visible: bool) -> None:
        # 獲取標題移動條
        moving_bar = title.moving_bar
        # 設定標題 顯示 or 隱藏
        title.setVisible(visible)
        # 設定移動條 顯示 or 隱藏
        moving_bar.setVisible(visible)
        # 獲取內容窗口
        scroll_contents = self.qlist_data['scroll_contents']
        # 設置內容窗口寬度大小
        scroll_contents.resize(
            scroll_contents.width() + (title.width() if visible else - title.width()), scroll_contents.height()
        )
        # 循環text
        for text in self.text_list:
            # 獲取子text
            my_text: MyText = text.child_text[title.name]
            # 子text 顯示 or 隱藏
            my_text.setVisible(visible)
            # text 調整大小
            text.resize(scroll_contents.width(), text.height())
        # 設定標題list 顯示 or 隱藏
        self.text_save_list.set_title_visible(title.name, visible)
        # 獲取 子text 第一個x座標
        x: int = 23
        _title: Title
        for index, _title in enumerate(self.text_save_list.title):
            _moving_bar = _title.moving_bar
            if _title.x() != x:
                _title.move(x, _title.y())
                _moving_bar.move(
                    _title.x() + _title.width() - (int(self.qlist_data['title_moving_bar_size'] / 2) + 1),
                    _title.y()
                )
                for text in self.text_list:
                    my_text: MyText = text.child_text[_title.name]
                    if index == 0 and not text.ico_image.isHidden():
                        my_text.move(text.child_text_x, my_text.y())
                    else:
                        my_text.move(x, my_text.y())
            x = _title.x() + _title.width()
        if visible:
            self.text_save_list.title.append(title.name, title) if title.name not in self.text_save_list.title else None
        else:
            self.text_save_list.title.remove(title) if title.name in self.text_save_list.title else None

    def set_text_state(self, text: Text) -> None:
        # 獲取點擊後的複選紐狀態
        state: bool = not text.property('state')
        # 設定複選紐 成相應 狀態
        text.check_button.set_image(state)
        # 根據狀態 來進行 當前點擊列表 新增 刪除
        if state:
            self.current_click.append(text)
        else:
            self.current_click.remove(text)
        # 設置本身狀態
        text.state = state
        # 設定背景顏色
        text.setProperty('state', state)
        # 刷新QSS
        text.setStyle(text.style())

    def radio(self, text: Text) -> None:
        self.qlist_data['first_click'] = text
        # 獲得已點擊複製
        current_click = self.current_click.copy()
        if text in current_click:
            current_click.remove(text)
        else:
            self.set_text_state(text)
        for text in current_click:
            self.set_text_state(text)

    def shift(self, text: Text) -> None:
        # 獲取目前點擊的text 是在第幾個
        index = self.text_list.index(text)
        # 查看最後一次點擊 之前是否點擊過
        if self.qlist_data['first_click']:
            _index = self.text_list.index(self.qlist_data['first_click'])
            # 獲取目前點擊的 - 最後點擊 之間的數量
            multiple_selection = index - _index
            # 查看數量是否大於0
            if multiple_selection > 0:
                currently = self.text_list[_index:index + 1]
            # 查看數量是否小於0
            elif multiple_selection < 0:
                currently = self.text_list[index:_index + 1]
            # 如果等於0進入點擊
            else:
                # 進入單獨點擊
                self.radio(text)
                return
            # 獲取目前所有以點擊的複製
            current_click = self.current_click.copy()
            # 循環舊的所有text 複製
            for text in current_click:
                # 查看 index 是否在新典籍範圍之內
                if text in currently:
                    # 在點擊範圍之內 就移除新點擊範圍的 index 不需要重新設定複選紐
                    currently.remove(text)
                else:
                    # 在點擊範圍之外 設定成空複選紐
                    self.set_text_state(text)
            # 循環新的所有texts點擊
            for text in currently:
                # 設定成選中複選紐
                self.set_text_state(text)
        else:
            self.qlist_data['first_click'] = text
            self.radio(text)

    # 發出點擊數量變化信號
    def emit_change_quantity(self):
        size = self.text_save_list.get_text_size()
        # 設置 標題複選紐是否選中
        if len(self.current_click) == size and size:
            self.title.click_label.set_image(True)
        elif self.title.click_label.state and len(self.current_click) != size or size == 0:
            self.title.click_label.set_image(False)
        self.change_quantity.emit(len(self.current_click))

    def vbox_left_select(self, text: Text) -> None:
        # 點著shift事件
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            self.shift(text)
        else:
            # 設定最後一次點擊
            self.qlist_data['first_click'] = text
            self.set_text_state(text)
        self.emit_change_quantity()

    def vbox_right_select(self, text: Text) -> None:
        # 設定最後一次點擊
        self.qlist_data['first_click'] = text
        self.set_text_state(text)
        self.emit_change_quantity()

    def text_left_select(self, text: Text) -> None:
        # CTRL事件
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            self.vbox_left_select(text)
            return
        # SHIFT事件
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            self.shift(text)
        else:
            self.radio(text)
        self.emit_change_quantity()

    def text_right_select(self, text: Text) -> None:
        if text.state:
            return
        self.text_left_select(text)

    def moving_bar_mouse_move(self, name: str, event: QMouseEvent) -> None:
        title: Title = self.text_save_list.get_name_title_all(name)
        index: int = self.text_save_list.title_all_index(name)
        scroll_contents = self.qlist_data['scroll_contents']
        # 判斷標題移動後的座標 是否小於 最低移動限制
        if title.width() + event.x() >= title.moving_bar.least:
            scroll_contents.resize(scroll_contents.width() + event.x(), scroll_contents.height())
            self.title.resize(self.title.width() + event.x(), self.title.height())
            # 設定 自身標題 寬度
            title.resize(title.width() + event.x(), title.height())
            # 設定 自身移動條 位置
            title.moving_bar.move(title.x() + title.width() - 3, 0)
            # 移動後面的 標題 移動條
            if index + 2 <= self.text_save_list.title_size():
                # 獲取後續標題, 移動條
                for _title in self.text_save_list.title[index + 1:]:
                    _moving_bar = _title.moving_bar
                    # 後續標題移動位子
                    _title.move(_title.x() + event.x(), _title.y())
                    # 後續移動條移動位置
                    _moving_bar.move(_title.x() + _title.width() - 3, _moving_bar.y())
                    # 發送後續標題位置信號
                    for text in self.text_list:
                        my_text: MyText = text.child_text[_title.name]
                        my_text.move(_title.x(), my_text.y())
            # 發送移動後 自身X 自身寬度 位置
            for text in self.text_list:
                # 讓所有的 text 保持跟 內容窗口相同寬度
                text.resize(scroll_contents.width(), text.height())
                # 獲取 自身標題符合的 子text
                my_text: MyText = text.child_text[title.name]
                # 調整 子text 寬度
                my_text.resize_(title.x() + title.width() - my_text.x(), my_text.height())

    # 設定所有Text成 選中 或者是 未選中 狀態
    def set_all_state(self) -> None:
        # 查看是否全部已選中
        if len(self.current_click) == self.text_save_list.get_text_size():
            for text in self.current_click.copy():
                self.set_text_state(text)
        else:
            for text in self.text_list[0:self.text_save_list.get_text_size()]:
                if text not in self.current_click:
                    self.set_text_state(text)
        self.emit_change_quantity()
