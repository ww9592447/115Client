from module import create_task, get_event_loop, sleep
from API.download115 import Download115
from API.upload115 import Upload115
from Task.download import Download
from Task.upload import Upload
from Task.sha1 import GetSha1


class Mprocess:
    def __init__(self, state, lock, wait, wait_lock, closes, directory, config):
        # 共享數據
        self.state = state
        # 共享數據鎖
        self.lock = lock
        # 傳送列表
        self.wait = wait
        # 傳送列表鎖
        self.wait_lock = wait_lock
        # 115API
        self.directory = directory
        # 關閉信號
        self.closes = closes
        # 下載API
        self.download115 = Download115(config)
        # 下載任務
        self.download = Download(self.download115, state, lock, closes, config)
        # 上傳API
        self.upload115 = Upload115(config)
        # 上傳任務
        self.upload = Upload(self.upload115, state, lock, closes, self.directory, config)
        # sha1任務
        self.sha1 = GetSha1(self.state, self.lock)
        # 用戶資料
        self.config = config
        self.loop = get_event_loop()
        self.loop.run_until_complete(self.stop())

    # 檢查傳送列表
    async def stop(self):
        while 1:
            if self.closes.value:
                return
            elif not self.closes.value and self.wait:
                with self.wait_lock:
                    uuid = self.wait.pop(0)
                select = uuid[0]

                if select == '0':
                    create_task(self.download.download_task(uuid))
                elif select == '2':
                    create_task(self.download.aria2_task(uuid))
                elif select == '4':
                    create_task(self.download.sha1_task(uuid))
                elif select == '6':
                    create_task(self.upload.upload_task(uuid))
                elif select == '7':
                    create_task(self.upload.sha1_task(uuid))
                elif select == '8':
                    create_task(self.sha1.get(uuid))

            else:
                await sleep(0.1)
                continue
