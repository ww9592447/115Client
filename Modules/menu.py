from PyQt5.Qt import QWidget, QIcon, QAction, QHBoxLayout, Qt, QGraphicsDropShadowEffect, \
    QColor, QPixmap, QSize, QListWidget, QListWidgetItem, QApplication, QPainter, \
    QPoint, QCursor, QAbstractItemView, QStyledItemDelegate, QModelIndex, QPen, QStyleOptionViewItem


# 獲取螢幕大小
def available_view_size() -> type[int, int]:
    ss = QApplication.screenAt(QCursor.pos()).availableGeometry()
    w, h = ss.width() - 100, ss.height() - 100
    return w, h


class MenuItemDelegate(QStyledItemDelegate):

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        if not index.model().data(index, Qt.UserRole) is None:
            return super().paint(painter, option, index)

        # draw seperator
        painter.save()

        c = 0
        pen = QPen(QColor(c, c, c, 25), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        rect = option.rect
        painter.drawLine(0, rect.y() + 4, rect.width() + 12, rect.y() + 4)

        painter.restore()


class MenuActionListWidget(QListWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.setViewportMargins(0, 6, 0, 6)
        # 設置防止刪除文字
        self.setTextElideMode(Qt.ElideNone)
        # 設置圖標大小
        self.setIconSize(QSize(14, 14))
        # 設置 菜單 畫圖
        self.setItemDelegate(MenuItemDelegate())
        # 設置禁止選中
        self.setSelectionMode(QAbstractItemView.NoSelection)
        # 設置qss
        self.setStyleSheet(
            'MenuActionListWidget{font: 14px "Segoe UI", "Microsoft YaHei", "PingFang SC"}'
        )

    def addItem(self, item) -> None:
        """ add menu item at the end """
        super().addItem(item)
        self.adjustSize()

    def adjustSize(self) -> None:
        size = QSize()
        for i in range(self.count()):
            item = self.item(i)
            if item.isHidden():
                continue
            s = item.sizeHint()
            size.setWidth(max(s.width(), size.width()))
            size.setHeight(size.height() + s.height())

        w, h = available_view_size()

        self.viewport().adjustSize()

        m = self.viewportMargins()
        size += QSize(m.left() + m.right() + 2, m.top() + m.bottom())
        size.setHeight(min(h, size.height() + 3))
        size.setWidth(max(min(w, size.width()), self.minimumWidth()))
        self.setFixedSize(size)


class Menu(QWidget):
    menu_qss = """QMenu {
        background-color: rgb(232, 232, 232);
        font: 14px 'Segoe UI', 'Microsoft YaHei';
        padding: 4px 0px 4px 0px;
        border: 1px solid rgb(200, 200, 200);
    }
    QMenu::separator {
        height: 1px;
        background: rgba(0, 0, 0, 104);
        margin-right: 13px;
        margin-top: 4px;
        margin-bottom: 4px;
        margin-left: 10px;
    }
    MenuActionListWidget {
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 9px;
        background-color: rgb(249, 249, 249);
        outline: none;
        font: 14px 'Segoe UI', 'Microsoft YaHei';
    }
    MenuActionListWidget::item {
        padding-left: 10px;
        padding-right: 10px;
        border-radius: 5px;
        border: none;
        margin-left: 6px;
        margin-right: 6px;
    }
    MenuActionListWidget::item:disabled {
        padding-left: 10px;
        padding-right: 10px;
        border-radius: 5px;
        border: none;
    }
    MenuActionListWidget::item:hover {
        background-color: rgba(0, 0, 0, 9);
    }
    """

    def __init__(self) -> None:
        super().__init__(None)
        # 設置所有動作列表
        self.actions: list[QAction, ...] = []
        # 子菜單大小
        self.item_height = 28
        # 設置布局
        self.box_layout = QHBoxLayout(self)
        # 設置菜單窗口
        self.view = MenuActionListWidget(self)
        # 添加菜單窗口到布局
        self.box_layout.addWidget(self.view, 1, Qt.AlignCenter)
        # 設置布局內容邊距
        self.box_layout.setContentsMargins(12, 8, 12, 20)
        # 設置陰影窗口
        self.shadowEffect = QGraphicsDropShadowEffect(self.view)
        self.shadowEffect.setBlurRadius(30)
        self.shadowEffect.setOffset(0, 8)
        self.shadowEffect.setColor(QColor(0, 0, 0, 30))
        # 設置菜單窗口套用陰影窗口效果
        self.view.setGraphicsEffect(self.shadowEffect)
        # 設置連接槽函數
        self.view.itemClicked.connect(self._item_clicked)

        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint |
                            Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(self.menu_qss)

    def addAction(self, action: QAction) -> QListWidgetItem:
        self.actions.append(action)
        item = QListWidgetItem(self._create_item_icon(action), action.text())
        self._adjust_item_text(item, action)

        item.setData(Qt.UserRole, action)
        action.setProperty('item', item)

        self.view.addItem(item)
        self.adjustSize()
        return item

    # 顯示菜單
    def exec(self, pos: QPoint) -> None:
        if self._is_item_all_hidden():
            return

        rect = QApplication.screenAt(QCursor.pos()).availableGeometry()
        w, h = self.width() + 5, self.sizeHint().height()
        x = min(pos.x() - self.layout().contentsMargins().left(), rect.right() - w)
        y = min(pos.y() - 4, rect.bottom() - h)

        self.move(QPoint(x, y))

        self.show()

    def adjustSize(self) -> None:
        m = self.layout().contentsMargins()
        w = self.view.width() + m.left() + m.right()
        h = self.view.height() + m.top() + m.bottom()
        self.setFixedSize(w, h)

    # 添加分隔線
    def add_separator(self):
        """ add seperator to menu """
        m = self.view.viewportMargins()
        w = self.view.width()-m.left()-m.right()

        # add separator to list widget
        item = QListWidgetItem(self.view)
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(QSize(w, 9))
        self.view.addItem(item)
        item.setData(Qt.DecorationRole, "seperator")
        self.adjustSize()

    def set_item_hidden(self, item: QListWidgetItem, hide: bool) -> None:
        item.setHidden(hide)
        self.view.adjustSize()
        self.adjustSize()

    @staticmethod
    def set_item_enabled(item: QListWidgetItem, enabled: bool) -> None:
        if enabled:
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        else:
            item.setFlags(Qt.NoItemFlags)

    # 菜單單擊槽
    def _item_clicked(self, item: QListWidgetItem) -> None:

        if item.flags() == Qt.NoItemFlags:
            return

        action = item.data(Qt.UserRole)

        # 獲取 動作
        action = item.data(Qt.UserRole)
        self.view.clearSelection()
        self.close()
        action.trigger()

    def _create_item_icon(self, action: QAction) -> QIcon:
        has_icon = self._has_item_icon()

        icon = QIcon(action.icon())

        if has_icon and action.icon().isNull():
            pixmap = QPixmap(self.view.iconSize())
            pixmap.fill(Qt.transparent)
            icon = QIcon(pixmap)
        elif not has_icon:
            icon = QIcon()

        return icon

    def _adjust_item_text(self, item: QListWidgetItem, action: QAction) -> None:
        sw = 0

        if not self._has_item_icon():
            item.setText(action.text())
            w = 40 + self.view.fontMetrics().width(action.text()) + sw
        else:
            item.setText(" " + action.text())
            w = 60 + self.view.fontMetrics().width(item.text()) + sw

        item.setSizeHint(QSize(w, self.item_height))

    def _has_item_icon(self) -> bool:
        return any(not i.icon().isNull() for i in self.actions)

    def _is_item_all_hidden(self) -> bool:
        hidden = []

        for index in range(self.view.count()):
            if self.view.item(index).data(Qt.UserRole) is None:
                continue
            hidden.append(not self.view.item(index).isHidden())
        return not any(hidden)
