import re
import qrcode
import ctypes
from io import BytesIO
from sys import argv
from typing import Callable, Coroutine
from asyncio import set_event_loop, create_task, sleep, current_task, Future
from qasync import QEventLoop
from configparser import ConfigParser
from multiprocessing import freeze_support

from PyQt5.Qt import QWidget, QDialog, QApplication, Qt, QLabel, QFrame, QPixmap

from Window.window import NFramelessWindow
from Window.hints import error
from Modules.image import Image, AllImage, GifImage, IcoImage, get_transparent_pixmap
from Modules.type import Credential, ErrorResult, QrCode, Config, Cookie
from Modules.widgets import MyIco, TextLabel, MyPushButton, LineEdit
from fake115 import Fake115
from API.login import Login, LoginResult

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("starter")


def show_fake115() -> None:
    fake115 = Fake115(config, credential)
    fake115.show()


def set_cookie(result: LoginResult, usersessionid: str) -> None:
    config_data['帳號']['usersessionid'] = usersessionid
    config_data['帳號']['uid'] = result['cookie']['uid']
    config_data['帳號']['cid'] = result['cookie']['cid']
    config_data['帳號']['seid'] = result['cookie']['seid']
    cookie = ';'.join(['='.join((data[0].upper(), data[1])) for data in config_data['帳號'].items()])
    credential['headers']['Cookie'] = cookie
    credential['user_id'] = result['user_id']
    with open('config.ini', 'w', encoding='utf-8') as w:
        config_data.write(w)


class GetCode(QDialog, NFramelessWindow):
    def __init__(self, user_id: str, mobile: str, usersessionid: str) -> None:
        super().__init__()
        # 設置標題窗口
        title: QWidget = QWidget()
        # 設置標題窗口大小
        title.resize(self.width(), 60)
        # 設置標題
        TextLabel(title, '登入', font_size=14, geometry=(30, 25, 300, 30))
        # 設置 關閉按鈕
        MyIco(
            title, Image.BLACK_CLOSE, Image.BLUE_CLOSE, state=True, coordinate=(300, 35, 12, 12), click=self.reject
        )
        # 更新標題 到 主窗口
        self.set_title(title)

        # 115用戶id
        self.user_id: str = user_id
        # 115會話id
        self.usersessionid = usersessionid

        TextLabel(self.content_widget, '需要進行手機短信驗證', font_size=16, move=(90, 20))
        TextLabel(self.content_widget, mobile, font_size=20, move=(90, 60))
        self.code_line: LineEdit = LineEdit(self.content_widget, '短信驗證碼', '', (20, 110, 150, 50), 3)

        sms = QLabel(self.content_widget)
        sms.setPixmap(AllImage.get_image(Image.SMS))
        self.get_code: MyPushButton = MyPushButton(
            self.content_widget, '獲取驗證碼', qss=1, font_size=18,
            geometry=(180, 110, 150, 50), click=lambda: create_task(self.send_code())
        )
        MyPushButton(
            self.content_widget, '確定', qss=1, font_size=18,
            geometry=(20, 170, 310, 50), click=lambda: create_task(self.yes())
        )
        sms.move(20, 22)

        self.setStyleSheet('GetCode{background-color:rgb(255, 255, 255)}')

        self.resize(350, 300)

        # 設定 等待GIF
        self.load = AllImage.get_gif(
            self,
            GifImage.MAX_LOAD,
            (int((self.width() - 32) / 2), int((self.height() - 32) / 2), 32, 32)
        )

    @error(True)
    async def yes(self) -> ErrorResult:
        result = await login.login_verify(self.user_id, self.code_line.text())
        if result['state'] and result['user_id'] != '':
            set_cookie(result, self.usersessionid)
            self.accept()
            return ErrorResult(state=True, title='', name='', result='')
        elif 'user_id' in result:
            return ErrorResult(state=False, title='錯誤', name='短信驗證碼錯誤', result='', retry=False)
        else:
            return ErrorResult(state=False, title='網路異常', name='請問是否重新嘗試', result='')

    # 禁止操作
    def prohibit(self, mode: bool) -> None:
        # 是否顯示 等待動畫
        self.load.setVisible(not mode)
        self.content_widget.setEnabled(mode)

    @error()
    async def send_code(self) -> ErrorResult:
        self.prohibit(False)
        result = await login.send_code(self.user_id)
        self.prohibit(True)
        if result is False:
            return ErrorResult(state=False, title='網路異常發送簡訊失敗', name='請問是否重新發送', result='')
        self.get_code.setEnabled(False)
        for index in range(60, 0, -1):
            self.get_code.setText(f'{index}秒後可重新獲取')
            await sleep(1)
        self.get_code.setText('獲取驗證碼')
        self.get_code.setEnabled(True)
        return ErrorResult(state=True, title='', name='', result='')

    @classmethod
    def get(cls, user_id: str, mobile: str, usersessionid: str) -> int:
        return cls(user_id, mobile, usersessionid).exec()


class QrcodeLogin(QFrame):
    def __init__(
            self,
            parent: QWidget,
            qr_code_login: Callable[[LoginResult], None]
    ) -> None:
        super().__init__(parent)
        self.qr_code_login: Callable[[LoginResult], None] = qr_code_login
        # qrcode圖片
        self.qrcode_label: QLabel = QLabel(self)
        self.qrcode_label.setStyleSheet('QLabel{border: 1px solid rgb(230, 230, 230)}')
        self.qrcode_label.setGeometry(110, 0, 220, 220)
        self.qrcode_label.setScaledContents(True)

        self.refresh_image: QLabel = QLabel(self)
        self.refresh_image.setGeometry(110, 0, 220, 220)
        self.refresh_image.setStyleSheet('QLabel{background: transparent}')
        self.refresh_image.setPixmap(get_transparent_pixmap(Image.BLUE_REFRESH_MAX, 200))
        self.refresh_image.hide()

        self.task: Future | None = None

        self.setStyleSheet('QFrame{background-color: rgb(255, 255, 255)}')
        self.resize(440, 220)
        # 設定 等待GIF
        self.load = AllImage.get_gif(
            self,
            GifImage.MAX_LOAD,
            (int((self.width() - 32) / 2), int((self.height() - 32) / 2), 32, 32)
        )

    async def set_qr_label(self) -> None:
        self.load.show()
        result = await login.get_qr_code()
        if result['state']:
            buf = BytesIO()
            img = qrcode.make(result['url'])
            img.save(buf, "PNG")
            qt_pixmap = QPixmap()
            qt_pixmap.loadFromData(buf.getvalue(), "PNG")
            self.qrcode_label.setPixmap(qt_pixmap)
            create_task(self.wait_scanning(result))
        else:
            self.task = None
            self.refresh_image.show()
        self.load.hide()

    # 等待qr_code掃描
    async def wait_scanning(self, qr_code: QrCode) -> None:
        while 1:
            result = await login.get_qr_code_status(qr_code)
            if result == 0:
                create_task(self.set_qr_label())
                return
            if result == 3:
                result = await login.qr_code_login(qr_code['uid'])
                self.qr_code_login(result)
                return

    def raise_(self):
        QFrame.raise_(self)
        if self.task is None:
            self.task = create_task(self.set_qr_label())


class EnterLogin(QFrame):
    def __init__(
            self,
            parent: QWidget,
            click: Callable[[str, str, str], Coroutine]
    ) -> None:
        super().__init__(parent)
        self.usersessionid = LineEdit(
            self, 'usersessionid', config_data['帳號']['usersessionid'], (40, 0, 350, 50), 2, IcoImage.COOKIE
        )
        self.user = LineEdit(self, '帳號', config_data['帳號']['user'], (40, 50, 350, 50), 2, IcoImage.USER)
        self.password = LineEdit(self, '密碼', config_data['帳號']['password'], (40, 100, 350, 50), 2, IcoImage.PASSWORD)

        MyPushButton(
            self, '登入',
            qss=1,
            font_size=18,
            geometry=(30, 160, 390, 60),
            click=lambda: create_task(click(self.usersessionid.text(), self.user.text(), self.password.text()))
        )
        self.setStyleSheet('QFrame{background-color: rgb(255, 255, 255)}')
        self.resize(440, 220)


class CookieLogin(QFrame):
    def __init__(
            self,
            parent: QWidget,
            click: Callable[[str, str, str], Coroutine]
    ) -> None:
        super().__init__(parent)
        self.uid = LineEdit(self, 'uid', '', (40, 0, 350, 50), 2)
        self.cid = LineEdit(self, 'cid', '', (40, 50, 350, 50), 2)
        self.seid = LineEdit(self, 'seid', '', (40, 100, 350, 50), 2)
        MyPushButton(
            self, '登入',
            qss=1,
            font_size=18,
            geometry=(30, 160, 390, 60),
            click=lambda: create_task(click(self.uid.text(), self.cid.text(), self.seid.text()))
        )
        self.setStyleSheet('QFrame{background-color: rgb(255, 255, 255)}')
        self.resize(440, 220)


class LoginWindow(QDialog, NFramelessWindow):
    def __init__(self) -> None:
        super().__init__()
        # 設置標題窗口
        title: QWidget = QWidget()
        # 設置標題窗口大小
        title.resize(self.width(), 60)
        # 設置標題
        TextLabel(title, '登入', font_size=14, geometry=(30, 20, 300, 30))
        # 設置 關閉按鈕
        MyIco(
            title, Image.BLACK_CLOSE, Image.BLUE_CLOSE, state=True, coordinate=(380, 30, 12, 12), click=self.close
        )
        # 更新標題 到 主窗口
        self.set_title(title)

        # qrcode登入窗口
        self.qr_code_login = QrcodeLogin(self.content_widget, self.qr_code_login_callable)
        # 輸入登入窗口
        self.username_login = EnterLogin(self.content_widget, self.username_login_callable)
        # cookie登入窗口
        self.cookie_login = CookieLogin(self.content_widget, self.cookie_login_callable)

        self.qr_code_text = MyPushButton(
            self.content_widget, '二維碼登入', qss=3, font_size=20,
            click=lambda: self.set_login_visible(self.qr_code_login, self.qr_code_text)
        )
        self.username_text = MyPushButton(
            self.content_widget, '帳號登入', qss=3, font_size=20,
            click=lambda: self.set_login_visible(self.username_login, self.username_text)
        )
        self.cookie_text = MyPushButton(
            self.content_widget, 'cookie登入', qss=3, font_size=20, move=(110, 235),
            click=lambda: self.set_login_visible(self.cookie_login, self.cookie_text)
        )
        self.set_login_visible(self.username_login, self.username_text)

        self.resize(440, 330)

        # 設定 等待GIF
        self.load = AllImage.get_gif(
            self,
            GifImage.MAX_LOAD,
            (int((self.width() - 32) / 2), int((self.height() - 32) / 2), 32, 32)
        )
        # 設置任務欄圖標
        self.setWindowIcon(AllImage.get_ico(IcoImage.FAVICON))

        self.setStyleSheet('LoginWindow{background-color: rgb(255, 255, 255)}')

    # 禁止操作
    def prohibit(self, mode: bool) -> None:
        # 是否顯示 等待動畫
        self.load.setVisible(not mode)
        self.content_widget.setEnabled(mode)

    def get_code(self, user_id: str, mobile: str, usersessionid: str) -> None:
        if GetCode.get(user_id, mobile, usersessionid) == 1:
            self.accept()
            show_fake115()

    @error(True)
    # 使用帳號登入
    async def username_login_callable(self, usersessionid: str, user: str, password: str) -> ErrorResult:
        result = await login.login(user, password, usersessionid)
        if result['state'] is False:
            return ErrorResult(state=False, title='網路異常登入失敗', name='請問使否重新嘗試', result='')
        elif result['state'] is True and 'mobile' in result:
            current_task().add_done_callback(
                lambda task: self.get_code(result['user_id'], result['mobile'], result['usersessionid'])
            )
            return ErrorResult(state=True, title='', name='', result='')
        elif result['state'] is True:
            set_cookie(result, usersessionid)
            self.accept()
            show_fake115()
            return ErrorResult(state=True, title='', name='', result='')

    def qr_code_login_callable(self, result: LoginResult) -> None:
        set_cookie(result, result['usersessionid'])
        self.accept()
        show_fake115()

    @error(True)
    async def cookie_login_callable(self, uid: str, cid: str, seid: str) -> ErrorResult:
        credential['headers']['Cookie'] = f'UID={uid};CID={cid};SEID={seid}'

        result = await login.checks_cookie(credential['headers']['Cookie'])
        if result['state'] == 1:
            login_result: LoginResult = LoginResult(
                state=True,
                user_id=result['user_id'],
                cookie=Cookie(
                    uid=uid,
                    cid=cid,
                    seid=seid
                )
            )
            set_cookie(login_result, '')
            show_fake115()
            self.accept()
            return ErrorResult(state=True, title='', name='', result='')
        elif result['state'] == -1:
            return ErrorResult(state=False, title='網路異常檢查cookie有效失敗', name='請問是否重新檢查', result='')
        elif result['state'] == 0:
            return ErrorResult(state=False, title='cookie已失效', name='cookie已失效', result='', retry=False)

    def set_login_visible(self, widget: QWidget, text: MyPushButton) -> None:
        if widget == self.username_login:
            self.cookie_text.move(110, 235)
            self.qr_code_text.move(230, 235)
        elif widget == self.qr_code_login:
            self.cookie_text.move(110, 235)
            self.username_text.move(250, 235)
        elif widget == self.cookie_login:
            self.username_text.move(110, 235)
            self.qr_code_text.move(240, 235)
        self.cookie_text.show()
        self.qr_code_text.show()
        self.username_text.show()
        text.hide()
        widget.raise_()

    @error(True)
    async def start(self) -> ErrorResult:
        self.show()
        result = await login.checks_cookie(credential['headers']['Cookie'])
        if result['state'] == 1:
            show_fake115()
            self.accept()
            return ErrorResult(state=True, title='', name='', result='')
        elif result['state'] == -1:
            return ErrorResult(state=False, title='網路異常檢查cookie有效失敗', name='請問是否重新檢查', result='')
        # elif (user := config_data['帳號']['user']) and (password := config_data['帳號']['password']):
        #     await self.username_login_callable(config_data['帳號']['usersessionid'], user, password)

        return ErrorResult(state=True, title='', name='', result='')


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    freeze_support()
    app = QApplication(argv)
    loop = QEventLoop(app)
    set_event_loop(loop)

    # 初始化設定
    config_data: ConfigParser = ConfigParser()
    # 獲取115設定
    config_data.read('config.ini', encoding='utf-8')
    # 設置傳輸相關數據
    config: Config = Config(
        download_max=config_data['Download'].getint('最大同時下載數'),
        download_path=config_data['Download']['下載路徑'],
        download_sha1=config_data['Download'].getboolean('Download_sha1'),
        upload_max=config_data['Upload'].getint('最大同時上傳數'),
        upload_thread_max=config_data['Upload'].getint('rpc最大同時下載數'),
        aria2_rpc_max=config_data['Aria2-rpc'].getint('rpc最大同時下載數'),
        aria2_rpc_url=config_data['Aria2-rpc']['rpc_url'],
        aria2_sha1=config_data['Aria2-rpc'].getboolean('aria2_sha1'),

    )
    # 設置 115 用戶資料
    credential: Credential = Credential(
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': ';'.join(
                ['='.join((data[0].upper(), data[1] if data[1] != '' else '0'))
                 for data in config_data['帳號'].items()]
            ),
            'User-Agent': 'Mozilla/5.0  115disk/11.2.0'
        },
        user_id=_user_id[1] if (_user_id := re.search(r'(\d+)_', config_data['帳號']['UID'])) else ''
    )
    login = Login()
    login_window = LoginWindow()
    create_task(login_window.start())
    with loop:
        loop.run_forever()
