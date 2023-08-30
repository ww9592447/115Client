from sys import argv
from asyncio import create_task, get_event_loop, sleep, Lock
from multiprocessing import Lock, Value
from typing import TypeVar

from PyQt5.Qt import QFont, QApplication, QFontMetrics

from Modules.type import Credential, Config
from API.download import Download
from API.upload import Upload
from API.directory import Directory
from Task.uploadtask import UploadTask
from Task.downloadtask import DownloadTask

try:
    from winfspy.plumbing import bindings
    bindings.get_winfsp_bin_dir()
    from Task.play115 import Play
    WinFsp = True
except RuntimeError:
    WinFsp = False

T = TypeVar('T')


class MyQFontMetrics:
    def __init__(self, size: int, state: dict[str, any], lock: Lock) -> None:
        self.app = QApplication(argv)
        self.state = state
        self.lock = lock
        # 獲取QT 字體設置
        font = QFont()
        # 設置字體大小
        font.setPointSize(size)
        self.font_metrics = QFontMetrics(font)

    def horizontal_advance(self, uuid: str) -> None:
        with self.lock:
            text_data_list = self.state[uuid]['list'].copy()
        for text_data in text_data_list:
            for my_text_data in text_data['my_text'].values():
                # 初始化文字大小
                size = 0
                # 獲取text列表
                text_size = my_text_data['text_size']
                # 獲取全部文字順序大小
                for char in my_text_data['text']:
                    # 獲取文字大小
                    size = size + self.font_metrics.horizontalAdvance(char)
                    # 添加文字大小 位置
                    text_size.append(size)
                # 文字大小翻轉 從大到小
                text_size.reverse()
        with self.lock:
            self.state[uuid] = {'state': True, 'list': text_data_list}


class MultiProgress:
    def __init__(
            self,
            state: dict[str, T],
            lock: Lock,
            wait: list[str, ...],
            wait_lock: Lock,
            closes: Value,
            font_size: int,
            directory: Directory,
            credential: Credential,
            config: Config
    ) -> None:
        # 共享數據
        self.state: dict[str, T] = state
        # 共享數據鎖
        self.lock: Lock = lock
        # 傳送列表
        self.wait: list[str, ...] = wait
        # 傳送列表鎖
        self.wait_lock: Lock = wait_lock
        # 關閉信號
        self.closes: Value = closes
        # 設置下載API
        self.download: Download = Download(credential)
        # 設置上傳API
        self.upload: Upload = Upload(credential)
        # 下載任務
        self.download_task: DownloadTask = DownloadTask(self.download, state, lock, config)
        # 設置目錄API
        self.directory: Directory = directory

        self.upload_task: UploadTask = UploadTask(self.upload, state, lock, self.directory, config)

        self.my_font_metrics = MyQFontMetrics(font_size, self.state, self.lock)
        self.loop: get_event_loop = get_event_loop()

        self.play: Play | None = None

        self.loop.run_until_complete(self.stop())

    def play_start(self):
        self.play.start()

    # 檢查傳送列表
    async def stop(self) -> None:
        try:
            while 1:
                with self.wait_lock:
                    if not self.closes.value and self.wait:
                        uuid = self.wait.pop(0)
                        select = uuid[0]
                        if select == '0':
                            self.my_font_metrics.horizontal_advance(uuid)
                        elif select == '1':
                            if self.play is None and WinFsp:
                                self.play: Play = Play(self.download, self.loop)
                                self.play.start()
                            await sleep(0.1)
                            data = uuid[1:].split('!')
                            self.play.add(data[0], data[1], data[2])
                            with self.lock:
                                self.state[uuid] = True
                        elif select == '2':
                            create_task(self.download_task.download_task(uuid))
                        elif select == '3':
                            create_task(self.upload_task.upload_task(uuid))
                        elif select == '4':
                            create_task(self.download_task.aria2_task(uuid))
                    elif self.closes.value:
                        if self.play and self.play.fs.started:
                            self.play.stop()
                        return
                await sleep(0.1)

        except Exception as f:
            print('進程終止', f)
            if self.play and self.play.fs.started:
                self.play.stop()

