from PyQt5.Qt import QGuiApplication, QFrame, QRect, QCursor, QApplication, QPushButton, QFont, Qt, QLabel,\
    pyqtSignal, QWidget, QMessageBox, QColor, QPalette, QLineEdit, QTextEdit, QProgressBar, QFileDialog, QMetaMethod,\
    QListView, QTreeView, QDialogButtonBox, QAbstractItemView, QSize, QMenu
from PyQt5 import QtCore, QtWidgets
from MyQlist.package import MyIco, picture, backdrop, gif
from MyQlist.DList import ListDirectory, Directory
from MyQlist.DList import Directory as MDirectory
from asyncio import shield, get_running_loop, create_task, sleep, set_event_loop, get_event_loop, gather, CancelledError
import time
import srequests
from os import popen, remove, startfile, makedirs, walk
from os.path import splitext, exists, split, getsize, isdir, join, isfile, basename
from datetime import timedelta, datetime
from enum import Enum
from uuid import uuid1
from MScroolBar import ScrollArea
import hashlib
import httpx
import inspect
from pathlib import Path
import math


# 設定邊框
class Frame(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet('background-color:rgba(200, 200, 200, 125)')


def getdata(state: str, result: str = None):
    return {'state': state, 'result': result if result else ''}


def pybyte(bytes, s=False):
    if s:
        s = '/s'
    else:
        s = ''
    if bytes >= 1024:
        kb = bytes / 1024
        if kb <= 1024:
            return "%.2fKB%s" % (kb, s)
        mb = kb / 1024
        if mb <= 1024:
            return "%.2fMB%s" % (mb, s)
        else:
            gb = mb / 1024
            return "%.2fGB%s" % (gb, s)
    else:
        return "%.2fB%s" % (bytes, s)


def getpath(path, value=True):
    _path = Path(path)
    if value:
        try:
            _path = _path.resolve()
        except:
            pass
        return str(_path)
    return _path


def get_ico(category):
    if category == '':
        return '未知'
    category = category.lower().replace('.', '')
    # 單副檔名
    generally = ['資料夾', 'exe', 'apk', 'cad', 'doc', 'epub', 'ipa', 'key', 'numbers', 'pages.', 'pdf', 'ppt', 'torrent', 'vsd']
    # 音訊副檔名
    music = ['mp3', 'aac', 'ogg', 'vorbis','opus', 'wav', 'flac', 'ape', 'alac', 'wavpack']
    # 影片副檔名
    video = ['flv', 'avi', 'wmv', 'asf', 'wmvhd', 'dat', 'vob', 'mpg', 'mpeg', 'mp4', '3gp', '3g2', 'mkv', 'rm', 'rmvb', 'mov', 'qt', 'ogg', 'ogv', 'oga', 'mod']
    # 試算表副檔名
    xls = ['xlsx', 'xltx', 'xls']
    # 壓縮副檔名
    compressed = ['rar', '7z', 'zip']
    # 圖片副檔名
    img = ['bmp', 'tiff', 'tif', 'png', 'gif', 'jpeg', 'jpg', 'psd', 'sai', 'psp', 'ufo', 'ps', 'eps', 'ai', 'svg', 'wmf']
    if category in generally:
        return category
    elif category in music:
        return 'music'
    elif category in video:
        return 'video'
    elif category in xls:
        return 'xls'
    elif category in compressed:
        return 'compressed'
    elif category in img:
        return 'img'
    else:
        return '未知'


class MQtext(QFrame):
    end = pyqtSignal(QWidget)
    toggle = pyqtSignal(QWidget, bool)

    def __init__(self, state, uuid, _state, queuelist=None, transmissionlist=None, allqtext=None, lock=None, parent=None):
        super().__init__(parent)
        # 共享數據資料
        self.state = state
        # 數據鎖
        self.lock = lock
        # 任務
        self.task = None
        # 是否能夠取消任務
        self.cancel = True
        # 所有qtest 列表
        self.allqtext = allqtext
        # 紀錄id
        self.uuid = uuid
        # 排隊列表
        self.queuelist = queuelist
        # 正在傳輸中列表
        self.transmissionlist = transmissionlist
        # 檔案名稱
        self.name = _state['name']
        # 檔案圖標
        self.name_ico = QLabel(self)
        # 檔案名稱
        self.file_name = QLabel(_state['name'], self)
        # 操作按鈕容器
        self.ico = QFrame(self)
        # 設定操作按鈕容器背景空白
        self.ico.setStyleSheet('background-color:rgb(255, 255, 255)')
        # 設置傳輸速度 or 狀態文字
        self.progressText = QLabel(self.ico)
        # 設文字顏色
        self.progressText.setStyleSheet('color:rgba(50, 50, 50, 150)')
        # 操作按鈕容器置頂
        self.ico.raise_()
        y = lambda height: int((56 - height) / 2)

        self.set_pause = MyIco('黑色暫停', '藍色暫停', coordinate=(219, y(10), 8, 10),
                               click=self.getevent('pause'), state=True, parent=self.ico)
        self.set_restore = MyIco('黑色恢復下載', '藍色恢復下載', coordinate=(219, y(11), 8, 11),
                                 click=self.getevent('restore'), state=True, parent=self.ico)
        self.set_closes = MyIco('黑色關閉下載', '藍色關閉下載', coordinate=(264, y(10), 9, 10),
                                state=True, click=self.getevent('close'), parent=self.ico)
        MyIco('黑色開啟資料夾', '藍色開啟資料夾', coordinate=(308, y(13), 14, 13),
              state=True, click=self.getevent('open'), parent=self.ico)
        self.set_restore.hide()
        self.setStyleSheet('MQtext{border-style:solid; border-bottom-width:1px; border-color:rgba(200, 200, 200, 125)'
                           '; background-color:rgb(255, 255, 255)}')

    # 判斷函數是否是異步並返回相應調用方式
    def getevent(self, name):
        event = getattr(self, name)
        if inspect.iscoroutinefunction(event):
            return lambda: create_task(event())
        else:
            return event

    def setdata(self, data: dict[str, str]):
        if data['state'] == 'text':
            self.progressText.setText(data['result'])
        elif data['state'] == 'end':
            self.end.emit(self)
        elif data['state'] in ['pause', 'close']:
            pass
        else:
            # 顯示網路錯誤
            self.progressText.setText(data['state'])
            # qtext 轉成暫停
            self.set_switch(False)

    # 暫停
    async def pause(self):
        self.set_switch(False)
        if self.task and not self.task.done():
            self.progressText.setText('等待暫停中...')
            self.set_button(False)
            if 'state' in self.state[self.uuid]:
                with self.lock:
                    with set_state(self.state, self.uuid) as state:
                        state.update({'state': 'pause'})
            if self.cancel:
                self.task.cancel()
            try:
                await self.task
            except (BaseException, ):
                pass
            self.set_button(True)
        self.progressText.setText('暫停中')

    # 關閉
    async def close(self):
        self.set_switch(False)
        if self.task and not self.task.done():
            self.progressText.setText('等待關閉中...')
            self.set_button(False)
            if 'state' in self.state[self.uuid]:
                with self.lock:
                    with set_state(self.state, self.uuid) as state:
                        state.update({'state': 'close'})
            if self.cancel:
                self.task.cancel()
            try:
                await self.task
            except (BaseException, ):
                pass
        self.end.emit(self)

    # 開啟
    def open(self):
        if exists(self.path):
            popen(f'explorer.exe /select, {self.path}')

    # 設定暫停開始按鈕狀態
    def set_switch(self, _bool):
        # 開始
        if _bool:
            self.progressText.setText('')
            self.set_pause.show()
            self.set_restore.hide()
        # 暫停
        else:
            self.set_pause.hide()
            self.set_restore.show()
        self.toggle.emit(self, _bool)

    # 設定按鈕是否可用
    def set_button(self, value):
        self.set_restore.setEnabled(value)
        self.set_restore.setEnabled(value)

    # 恢復
    def restore(self):
        self.set_switch(True)
        index = -1
        _index = self.allqtext.index(self)
        for wait in self.queuelist:
            if _index < self.allqtext.index(wait):
                index = self.queuelist.index(wait)
                break
        if index == -1:
            self.queuelist.append(self)
        else:
            self.queuelist.insert(index, self)

    def resizeEvent(self, e):
        self.ico.setGeometry(self.width() - 360, 0, 360, 55)


class MQtext1(MQtext):
    def __init__(self, state, _state, uuid, queuelist=None, transmissionlist=None, allqtext=None, lock=None, parent=None):
        super().__init__(state, uuid, _state, queuelist, transmissionlist, allqtext, lock, parent)
        # 檔案大小
        self.length = _state['length']
        self.name_ico.setGeometry(15, 15, 30, 30)
        self.name_ico.setPixmap(picture(f'_{_state["ico"]}'))
        self.file_name.setFont(QFont("細明體", 9))
        self.file_name.move(55, 16)

        # 設置檔案大小
        self.file_size = QLabel(f'{pybyte(_state["size"])}/{pybyte(_state["length"])}', self)
        self.file_size.setFont(QFont("細明體", 9))
        self.file_size.move(55, 37)
        self.file_size.setFixedWidth(120)
        self.file_size.setStyleSheet('color:rgba(50, 50, 50, 150)')
        # 設置進度條
        self.progressBar = QProgressBar(self.ico)
        self.progressBar.setMaximum(100)
        self.progressBar.setGeometry(0, 14, 152, 12)
        self.progressBar.setTextVisible(False)
        if _state['size'] != 0:
            self.progressBar.setValue(int(_state['size'] / _state['length'] * 100))
        self.progressBar.setStyleSheet('QProgressBar{border: 0px; background:rgb(200, 100, 200) ;'
                                       'background-color: rgb(229, 230, 234);color:rgb(60, 104, 137)}'
                                       'QProgressBar::chunk {background-color: rgb(6, 168, 255)}'
                                       )
        self.progressText.setFont(QFont("細明體", 11))
        self.progressText.setGeometry(0, 32, 152, 14)


class MQtext2(MQtext):
    def __init__(self, state, _state, uuid, queuelist=None, transmissionlist=None, allqtext=None, lock=None, parent=None):
        super().__init__(state, uuid, _state, queuelist, transmissionlist, allqtext, lock, parent)
        self.name_ico.setGeometry(15, 15, 30, 30)
        self.name_ico.setPixmap(picture(f'_{_state["ico"]}'))
        self.file_name.setFont(QFont("細明體", 12))
        self.file_name.adjustSize()
        self.file_name.move(55, int((56 - self.file_name.height()) / 2))
        self.progressText.setFont(QFont("細明體", 12))
        self.progressText.setGeometry(0, 20, 160, 16)


class MQList(QFrame):
    def __init__(self, state, lock, wait, waitlock, text, parent=None):
        super().__init__(parent)
        # 共用數據
        self.state = state
        # 數據鎖
        self.lock = lock
        # 準備下載列表
        self.wait = wait
        # 準備下載列表鎖
        self.waitlock = waitlock
        # 顯示所有數量
        self.text = text
        # 所有Qtext
        self.allqtext: list[MQtext] = []
        # 排隊列表
        self.queuelist: list[MQtext] = []
        # 正在傳輸列表
        self.transmissionlist: list[MQtext] = []
        # 暫停列表
        self.pauselist: list[MQtext] = []
        # 全部傳輸總量
        self.allsize = 0
        # 目前傳輸大小
        self.transmissionsize = 0
        # 設置 總進度條容器
        self.progresscontents = QLabel(self)
        self.progresscontents.setObjectName('progresscontents')
        self.progresscontents.setStyleSheet(
            '#progresscontents{border-style:solid; border-bottom-width:1px;'
            'border-color:rgba(200, 200, 200, 125)}'
        )
        # 預設 隱藏 總進度條容器
        self.progresscontents.hide()
        # 設置 下載總進度 文字
        self.name = QLabel(self.progresscontents)
        # 設置文字
        self.name.setText('下載總進度')
        # 設置文字顏色
        self.name.setStyleSheet('color:rgb(60, 104, 137)')
        # 設置文字位置大小
        self.name.setGeometry(14, 12, 60, 12)
        # 設置總進度條
        self.progressbar = QProgressBar(self.progresscontents)
        # 設置總進度條QSS設置
        self.progressbar.setStyleSheet('QProgressBar{border: 0px; background:rgb(200, 100, 200) ;'
                                       'background-color: rgb(229, 230, 234);color:rgb(60, 104, 137)}'
                                       'QProgressBar::chunk {background-color: rgb(6, 168, 255)}'
                                       )
        # 設置總進度上限
        self.progressbar.setMaximum(100)
        # 設置進度條%數文字置中
        self.progressbar.setAlignment(Qt.AlignCenter)
        # 設置按鈕容器
        self.buttons = QLabel(self.progresscontents)
        # 設置全部開始按鈕
        self.stop = MyQLabel('全部開始', (0, 0, 80, 24), qss=3, fontsize=12, clicked=self.allstop, parent=self.buttons)
        # 默認全部開始按鈕關閉
        self.stop.setEnabled(False)
        # 設置全部暫停按鈕
        self.pause = MyQLabel('全部暫停', (88, 0, 80, 24), qss=3, fontsize=12, clicked=self.allpause, parent=self.buttons)
        # 設置全部取消按鈕
        MyQLabel('全部取消', (176, 0, 80, 24), qss=3, clicked=self.allclose, fontsize=12, parent=self.buttons)
        # 設置滾動區
        self.scrollarea = ScrollArea(self)
        # 獲取滾動內容窗口
        self.scrollcontents = self.scrollarea.scrollcontents
        # 關閉橫滾動條
        self.scrollarea.sethrizontal(False)
        # 設置背景空白 左邊邊框
        self.setStyleSheet(
            'MQList{background-color:rgb(255, 255, 255);border-style:solid;'
            'border-left-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )

    # 全部開始
    def allstop(self):
        for qtext in self.pauselist:
            qtext.set_restore.left_click.emit(qtext)

    # 全部暫停
    def allpause(self):
        for qtext in self.transmissionlist + self.queuelist:
            qtext.set_pause.left_click.emit(qtext)

    # 全部取消
    def allclose(self):
        for qtext in self.allqtext.copy():
            qtext.set_closes.left_click.emit(qtext)

    # 設置目前傳輸大小
    def settransmissionsize(self, size):
        self.transmissionsize += size
        if self.progressbar.value() != (size := int(self.transmissionsize / self.allsize * 100)):
            self.progressbar.setValue(size)

    # qtext切換狀態回調
    def toggle(self, qtext, value):
        # 如果是 恢復下載 and qtxt 在暫停列表內 則刪除 暫停列表內的 qtext
        if value and qtext in self.pauselist:
            # 刪除 暫停列表內的 qtext
            self.pauselist.remove(qtext)
        # 如果是暫停
        if not value:
            # 查看是否在正在傳輸列表中
            if qtext in self.transmissionlist:
                # 刪除 傳輸列表內的 qtext
                self.transmissionlist.remove(qtext)
            # 查看是否在等待列表中
            elif qtext in self.queuelist:
                # 刪除 等待列表內的 qtext
                self.queuelist.remove(qtext)
            # 把 qtext 加入暫停列表
            self.pauselist.append(qtext)
        # 設定進度條按鈕狀態
        self.setbutton(value)

    # 設置進度條按鈕狀態
    def setbutton(self, value):
        if not self.stop.isEnabled() and self.pauselist and not value:
            self.stop.setEnabled(True)
        elif self.stop.isEnabled() and not self.pauselist and not self.queuelist:
            self.stop.setEnabled(False)
        if not self.pause.isEnabled() and self.transmissionlist and value:
            self.pause.setEnabled(True)
        elif self.pause.isEnabled() and not self.transmissionlist and not self.queuelist:
            self.pause.setEnabled(False)

    def _add(self, state, uuid, qtext, value):
        with self.lock:
            self.state.update({uuid: state})
        if 'length' in state:
            # 設置全部下載總量
            self.allsize += state['length']
            # 查看目前傳輸是否 已有傳輸
            if 'size' in state and state['size']:
                # 重新設置進度條
                self.settransmissionsize(state['size'])
        count = len(self.allqtext)
        qtext.end.connect(self.end)
        # 連接 qtext 切換信號
        qtext.toggle.connect(self.toggle)
        qtext.setGeometry(0, count * 56, self.width() - 2, 56)
        qtext.show()
        self.scrollcontents.setGeometry(0, 0, self.width() - 2, (count + 1) * 56)
        self.allqtext.append(qtext)
        if value:
            self.queuelist.append(qtext)
        else:
            qtext.set_switch(False)
        self.text(count + 1)
        # 查看進度條容器是否隱藏  如果隱藏則顯示
        if not self.progresscontents.isVisible():
            # 顯示進度條容器
            self.progresscontents.show()
            # 重新設定大小布局
            self.resize(self.size() - QSize(1, 1))

    def end(self, qtext):
        state = self.state[qtext.uuid]
        if 'state' in state:
            if state['state'] == 'close':
                self.close(qtext, state)
            elif state['state'] == 'end':
                self.complete(qtext, state)
        index = self.allqtext.index(qtext)
        self.allqtext.remove(qtext)
        for i in range(index, len(self.allqtext)):
            self.allqtext[i].setGeometry(0, i * 56, self.width(), 56)
        self.scrollcontents.setGeometry(0, 0, self.width() - 2, len(self.allqtext) * 56)
        if qtext in self.transmissionlist:
            self.transmissionlist.remove(qtext)
        elif qtext in self.queuelist:
            self.queuelist.remove(qtext)
        self.text(len(self.allqtext))
        qtext.setParent(None)
        qtext.deleteLater()

        # 查看 所有qtext 是否還有
        if self.allqtext:
            # 如果還有 重新設置 進度條按鈕 狀態
            self.setbutton(True)
        # 如果 qtext 沒有 則初始化 內容
        else:
            # 所有傳輸大小歸0
            self.allsize = 0
            # 目前傳輸大小歸0
            self.transmissionsize = 0
            # 進度條歸0
            self.progressbar.setValue(0)
            # 進度條容器隱藏
            self.progresscontents.hide()
            # 全部開始按鈕初始化
            self.stop.setEnabled(False)
            # 全部暫停按鈕初始化
            self.pause.setEnabled(True)
            # 重新設定大小布局
            self.resize(self.size() - QSize(1, 1))

        with self.lock:
            del self.state[qtext.uuid]

    def complete(self, qtext, state):
        pass

    def close(self, qtext, state):
        pass

    def resizeEvent(self, event):
        y = 35 if self.allqtext else 0
        self.scrollarea.setGeometry(0, y, self.width(), self.height() - y)
        self.scrollcontents.setGeometry(0, 0, self.width() - 2, self.scrollcontents.height())
        self.progresscontents.resize(self.width(), 35)
        self.buttons.setGeometry(self.width() - 290, 5, 256, 24)
        self.progressbar.setGeometry(88, 10, self.width() - 459, 14)
        for qtext in self.allqtext:
            qtext.setGeometry(0, qtext.y(), self.width() - 2, 56)


class TextQLabel(QLabel):
    def __init__(self, text, move=None, geometry=None, fontsize=None, parent=None):
        super().__init__(parent)
        if fontsize:
            # 獲取字體
            font = QFont()
            # 設置字體大小
            font.setPointSize(fontsize)
            # 替換字體
            self.setFont(font)
        self.setText(text)
        self.adjustSize()
        if move:
            self.move(*move)
        if geometry:
            self.setGeometry(*geometry)


class MyQLabel(QPushButton):

    def __init__(self, text, geometry, qss=0, fontsize=11, parent=None, clicked=None):
        super().__init__(parent)
        _qss = ''
        if qss == 0:
            _qss = 'MyQLabel{border-style:solid;border-width:1;border-color: rgba(200, 200, 200, 125);'\
                   f'border-radius: 5px; font-size:{fontsize}px}}'\
                   'MyQLabel:hover{background-color: rgb(242, 242, 243)}'
        elif qss == 1:
            _qss = f'MyQLabel{{background-color: rgb(39, 119, 248); color: rgb(255, 255, 255);' \
                   f'border-radius: 5px; font-size:{fontsize}px}}' \
                   'MyQLabel:hover{background-color: rgb(38, 110, 227)}'
        elif qss == 2:
            _qss = 'QPushButton{background-color: rgb(225, 226, 226); color: rgb(0, 0, 0);'\
                   f'border:1px solid rgb(173, 173, 173);border-radius: 5px; font-size:{fontsize}px}}'\
                   'QPushButton:hover:pressed{background-color: rgb(204, 228, 247);border-color: rgb(0, 85, 155)}'\
                   'QPushButton:hover{background-color: rgb(229, 241, 251);border-color: rgb(0, 120, 215)}'
        elif qss == 3:
            _qss = 'QPushButton{background-color: rgb(255, 255, 255); color: rgb(0, 0, 0);' \
                   f'border:1px solid rgb(173, 173, 173);border-radius: 5px; font-size:{fontsize}px}}' \
                   'QPushButton:hover:pressed{background-color: rgb(204, 228, 247);border-color: rgb(0, 85, 155)}' \
                   'QPushButton:hover{background-color: rgb(237, 246, 251);border-color: rgb(152, 217, 253)}' \
                   'QPushButton:disabled{border-color: rgb(227, 227, 227);' \
                   'background-color: rgb(247, 247, 247); color: rgb(155, 155, 155)}'

        self.setStyleSheet(_qss)
        self.setText(text)
        self.setGeometry(*geometry)
        self.setCursor(Qt.PointingHandCursor)

        if clicked:
            self.clicked.connect(clicked)


# 側邊框
class Sidebar(QWidget):
    left_click = pyqtSignal(QWidget)

    def __init__(self, text, ico_1, ico_2, move=None, click=None, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.ico_1 = ico_1
        self.ico_2 = ico_2

        self.check = False

        # 獲取字體
        font = QFont()
        # 設置字體大小
        font.setPointSize(10)

        self.text = QLabel(self)
        self.text.move(55, 12)
        self.text.setText(text)
        self.text.setFont(font)
        self.text.adjustSize()
        self.index = QLabel(self)
        self.index.move(self.text.x() + self.text.width() + 5, 12)
        self.index.setFont(font)
        self.ico = QLabel(self)
        self.ico.move(31, 13)
        self.ico.setPixmap(picture(ico_1))

        self.setPalette(backdrop('小淺藍色'))
        self.resize(165, 38)
        self.frame = QLabel(self)
        self.frame.setStyleSheet('background-color:rgb(6, 163, 248)')
        self.frame.resize(5, 38)
        self.frame.hide()
        # 是否設定大小
        if move:
            self.move(*move)
        # 是否設定左鍵點擊事件
        if click:
            self.left_click.connect(click)

    # 鼠標移出label
    def leaveEvent(self, event):
        if not self.check:
            self.setPalette(backdrop('小淺藍色'))

    # 鼠標移入label
    def enterEvent(self, event):
        if not self.check:
            self.setPalette(backdrop('中淺藍色'))

    # 單擊
    def mousePressEvent(self, event):
        # 左鍵
        if event.buttons() == Qt.LeftButton:
            self.left_click.emit(self)

    # 設定選中狀態
    def select(self, _bool):
        self.check = _bool
        if _bool:
            self.frame.show()
            self.setPalette(backdrop('大淺藍色'))
            self.ico.setPixmap(picture(self.ico_2))
        else:
            self.frame.hide()
            self.setPalette(backdrop('小淺藍色'))
            self.ico.setPixmap(picture(self.ico_1))


class Direction(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    LEFTTOP = 4
    LEFTBOTTOM = 5
    RIGHTBOTTOM = 6
    RIGHTTOP = 7
    NONE = 8


class Window(QWidget):
    def __init__(self, titlelabel, height, tracking=True, parent=None):
        super().__init__(parent)

        # 陰影大小
        self.padding = 13
        # 紀錄原本大小
        self._rect = None
        # 窗口是否最大化
        self.state = False
        # 滑鼠方向
        self.dir = None
        # 判斷滑鼠是否按下
        self.isLeftPressDown = False  # 鼠标左键是否按下
        # 獲取移動中滑鼠位置
        self.dragPosition = None
        # 設置是否能夠啟用滑鼠追蹤
        self.tracking = tracking
        # 設定顯示邊框陰影窗口
        self.shadow_widget = QWidget(self)
        # 設定陰影窗口名稱
        self.shadow_widget.setObjectName('shadow_widget')
        # 根據陰影窗口名稱 設定背景顏色
        self.shadow_widget.setStyleSheet('#shadow_widget{background-color:rgb(255,255,255);}')
        # 移動到可以完全顯示陰影
        self.shadow_widget.move(self.padding, self.padding)
        # 安裝事件管理器
        self.shadow_widget.installEventFilter(self)
        # 設定內容窗口
        self.content_widget = QWidget(self.shadow_widget)
        self.content_widget.setObjectName('content_widget')
        # self.content_widget.setStyleSheet('background-color:rgb(0,255,255)')
        self.content_widget.move(0, height)
        # 設定陰影
        self.effect_shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        # 偏移
        self.effect_shadow.setOffset(0, 0)
        # 設定 陰影半徑  模糊顏色
        self.effect_shadow.setBlurRadius(self.padding)
        # 設定 陰影顏色
        self.effect_shadow.setColor(QtCore.Qt.gray)
        # 套用陰影設定
        self.shadow_widget.setGraphicsEffect(self.effect_shadow)
        # 查看是否設置滑鼠追蹤
        if tracking:
            # 啟用滑鼠追蹤 為了可以拉伸窗口
            self.setMouseTracking(True)
        # 設定窗口背景透明
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # 設定無邊框
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        self.titlelabel = titlelabel(self.shadow_widget)
        self.titlelabel.move(1, 0)
        self.titlelabel.resize(self.shadow_widget.width(), height)
        self.titlelabel.installEventFilter(self)

        # 標題板機
        self._move_drag = None
        # 標題座標
        self._move_DragPosition = None

    # 最大化
    def showMaximized(self):
        # 紀錄原本大小位置
        self._rect = self.geometry()
        # 狀態設定成最大化
        self.state = True
        # 獲取螢幕最大大小
        size = self.screen().availableGeometry()
        # 計算移除陰影後的大小
        size = QRect(-self.padding + size.x(), -self.padding, size.width() + self.padding * 2, size.height() + self.padding * 2)
        # 設定位置大小
        self.setGeometry(size)
        if self.tracking:
            # 取消滑鼠追蹤
            self.setMouseTracking(False)
        # 傳遞消息
        self.window_change(True)
        # 取消陰影大小
        self.effect_shadow.setBlurRadius(0)
        # 套用陰影設定
        self.shadow_widget.setGraphicsEffect(self.effect_shadow)

    # 恢復原本窗口大小
    def showNormal(self):
        # 狀態設定成原本大小
        self.state = False
        # 還原成原本窗口大小
        self.setGeometry(self._rect)
        if self.tracking:
            # 恢復滑鼠追蹤
            self.setMouseTracking(True)
        # 傳遞消息
        self.window_change(False)
        # 設定 陰影半徑  模糊距離
        self.effect_shadow.setBlurRadius(self.padding)
        # 套用陰影設定
        self.shadow_widget.setGraphicsEffect(self.effect_shadow)

    # 左鍵雙擊
    def mouseDoubleClickEvent(self, event):
        if self.titlelabel.geometry().contains(self.shadow_widget.mapFromParent(event.pos())):
            # 查看窗口是否最大化
            if self.state:
                # 如果最大化 就還原原本大小
                self.showNormal()
            else:
                # 沒有最大化 就最大化
                self.showMaximized()

    # 獲得窗口最大化 還原 事件
    def window_change(self, value):
        pass

    def changeEvent(self, event) -> None:
        # 查看是否獲得活動窗口
        if event.type() == 99 and self.isActiveWindow():
            # 設定陰影顏色
            self.effect_shadow.setColor(QtCore.Qt.gray)
            # 套用陰影設定
            self.shadow_widget.setGraphicsEffect(self.effect_shadow)
        else:
            # 設定陰影顏色
            self.effect_shadow.setColor(QtCore.Qt.darkGray)
            # 套用陰影設定
            self.shadow_widget.setGraphicsEffect(self.effect_shadow)

    def eventFilter(self, watched, event):
        # 判斷是否進入內容窗口內
        if event.type() == 10:
            # 如果進入 dir 設定成預設
            self.dir = Direction.NONE
            # 滑鼠設定成預設
            self.setCursor(QCursor(Qt.ArrowCursor))
        return super().eventFilter(watched, event)

    # 滑鼠單擊
    def mousePressEvent(self, event):
        # 判斷是否左鍵
        if event.button() == Qt.LeftButton:
            # 判斷點擊範圍是否是在 標題範圍內
            if self.titlelabel.geometry().contains(self.shadow_widget.mapFromParent(event.pos())):
                # 設定標題板機 True
                self._move_drag = True
                # 設定標題座標
                self._move_DragPosition = event.globalPos() - self.pos()
                return
            # 設定可以移動窗口
            self.isLeftPressDown = True
            # 設定移動滑鼠位置
            self.dragPosition = event.globalPos()

    # 滑鼠鬆開
    def mouseReleaseEvent(self, event):
        # 設定不能移動窗口
        self.isLeftPressDown = False
        # 滑鼠樣式初始化
        self.dir = Direction.NONE
        # 設定標題板機 False
        self._move_drag = False

    def region(self, glopoint, tl, rb):
        x = glopoint.x()
        y = glopoint.y()
        # 判斷是否右下角
        if rb.x() >= x >= rb.x() - self.padding and rb.y() >= y >= rb.y() - self.padding:
            self.dir = Direction.RIGHTBOTTOM
            self.setCursor(QCursor(Qt.SizeFDiagCursor))
        # 判斷是否左下角
        elif tl.x() + self.padding >= x >= tl.x() and rb.y() >= y >= rb.y() - self.padding:
            self.dir = Direction.LEFTBOTTOM
            self.setCursor(QCursor(Qt.SizeBDiagCursor))
        # 判斷是否左上角
        elif tl.x() + self.padding >= x >= tl.x() and tl.y() + self.padding >= y >= tl.y() + 13:
            self.dir = Direction.LEFTTOP
            self.setCursor(QCursor(Qt.SizeFDiagCursor))
        # 判斷是右上角
        elif rb.x() >= x >= rb.x() - self.padding and tl.y() + self.padding >= y >= tl.y() + 13:
            self.dir = Direction.RIGHTTOP
            self.setCursor(QCursor(Qt.SizeBDiagCursor))
        # 判斷是否上邊
        elif tl.y() + self.padding >= y >= tl.y():
            self.dir = Direction.UP
            self.setCursor(QCursor(Qt.SizeVerCursor))
        # 判斷是否左邊
        elif tl.x() + self.padding >= x >= tl.x():
            self.dir = Direction.LEFT
            self.setCursor(QCursor(Qt.SizeHorCursor))
        # 判斷是否右邊
        elif rb.x() >= x >= rb.x() - self.padding:
            self.dir = Direction.RIGHT
            self.setCursor(QCursor(Qt.SizeHorCursor))
        # 判斷是否下邊
        elif rb.y() >= y >= rb.y() - self.padding:
            self.dir = Direction.DOWN
            self.setCursor(QCursor(Qt.SizeVerCursor))
        else:
            # 默认
            self.dir = Direction.NONE
            self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        # 獲取滑鼠在全局的座標
        glopoint = event.globalPos()
        # 獲取自身矩形大小
        rect = self.rect()
        # 獲取全局左上角的座標
        tl = self.mapToGlobal(rect.topLeft())
        # 獲取全局右下角的座標
        rb = self.mapToGlobal(rect.bottomRight())
        # 獲取矩形全局大小
        rmove = QRect(tl, rb)
        # 判斷滑鼠移動是否按下 and 是否移動標題
        if not self.isLeftPressDown and not self._move_drag:
            self.region(glopoint, tl, rb)
        # 是否需要移動標題
        elif self._move_drag:
            # 判斷是否取消滑鼠追蹤
            if self.tracking and not self.hasMouseTracking():
                # 重新啟用滑鼠追蹤
                self.setMouseTracking(True)
            # 判斷是否窗口最大化
            # 如果最大化則還原大小 順便移動到滑鼠位置
            if self.state and self._rect:
                # 獲取全局 y座標移動 相差的值
                y = event.globalPos().y() - self._move_DragPosition.y()
                # 重新設定紀錄原本大小 的左上角座標
                self._rect.moveTo(int(event.globalPos().x() - self._rect.width() / 2), y)
                # 獲取目前螢幕的可用大小
                size = self.screen().availableGeometry()
                # 獲取右側的座標
                right = size.x() + size.width()
                # 查看是否小於左側座標
                if self._rect.x() - self.padding < size.x():
                    # 如果小於左側座標 則移動到跟左側座標一樣的位置
                    self._rect.moveLeft(-self.padding + size.x())
                # 查看是否大於右側座標
                elif self._rect.x() + self._rect.width() + self.padding > right:
                    # 如果大於右側座標 則右側底部移動到跟右側座標一樣的位置
                    self._rect.moveLeft(right - self._rect.width() + self.padding)
                # 調用還原大小函數
                self.showNormal()
                # 重新設定標題座標
                self._move_DragPosition = event.globalPos() - self.pos()
            else:
                # 標題跟隨滑鼠拖曳
                self.move(event.globalPos() - self._move_DragPosition)
        else:
            x = glopoint.x() - self.dragPosition.x()
            y = glopoint.y() - self.dragPosition.y()
            # 右下
            if self.dir == Direction.RIGHTBOTTOM:
                rmove.setWidth(rmove.width() + x)
                rmove.setHeight(rmove.height() + y)
            # 左下
            elif self.dir == Direction.LEFTBOTTOM:
                rmove.setX(rmove.x() + x)
                rmove.setHeight(rmove.height() + y)
            # 左上
            elif self.dir == Direction.LEFTTOP:
                rmove.setX(rmove.x() + x)
                rmove.setY(rmove.y() + y)
            # 右上
            elif self.dir == Direction.RIGHTTOP:
                rmove.setWidth(rmove.width() + x)
                rmove.setY(rmove.y() + y)
            # 上邊
            elif self.dir == Direction.UP:
                rmove.setY(rmove.y() + y)
            # 左邊
            elif self.dir == Direction.LEFT:
                rmove.setX(rmove.x() + x)
            # 右邊
            elif self.dir == Direction.RIGHT:
                rmove.setWidth(rmove.width() + x)
            # 下邊
            elif self.dir == Direction.DOWN:
                rmove.setHeight(rmove.height() + y)
            self.setGeometry(rmove)
            self.dragPosition = event.globalPos()

    def resizeEvent(self, event):
        self.shadow_widget.resize(self.width() - self.padding * 2, self.height() - self.padding * 2)
        self.titlelabel.resize(self.shadow_widget.width() - 2, self.titlelabel.height())
        self.content_widget.resize(self.shadow_widget.width(), self.shadow_widget.height() - self.titlelabel.height())


class set_state:
    def __init__(self, state, data):
        self.state = state
        self._state = state[data]
        self.data = data

    def __enter__(self):
        return self._state

    def __exit__(self, type, value, traceback):
        self.state[self.data] = self._state
