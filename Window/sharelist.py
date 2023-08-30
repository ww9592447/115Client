import time
from os.path import splitext
from asyncio import create_task

from PyQt5.Qt import QWidget, QResizeEvent, QApplication

from Modules.image import GifLabel, GifImage, AllImage, IcoImage, get_ico
from Modules.type import TextData, MyTextData, ErrorResult
from Window.hints import error
from MyQlist.QList import QList
from Modules.get_data import pybyte
from API.share import Share


def get_my_text_data(name: str, color: tuple[int, int, int] | None = None) -> MyTextData:
    return MyTextData(text=name, color=color, mouse=False, text_size=[])


def get_review(data: dict[str, any]) -> MyTextData:
    share_state = int(data['share_state'])
    if share_state == 0:
        return get_my_text_data('審核中', (0, 0, 255))
    elif share_state == 7:
        return get_my_text_data('已失效', (164, 169, 174))
    elif 'have_vio_file' in data:
        return get_my_text_data('違規', (255, 0, 0))
    else:
        return get_my_text_data('正常')


class ShareList(QList):
    def __init__(self, parent: QWidget, share: Share):
        super().__init__(parent=parent)

        self.share: Share = share

        self.title_add('名稱', 400, 200)
        self.title_add(' 狀態', 70, 70)
        self.title_add(' 到期時間', 125, 125)
        self.title_add(' 分享時間', 125, 125)
        self.title_add(' 大小', 85, 85)
        self.title_add(' 已接收次數', least=80)
        # 設置背景空白 左邊邊框
        self.setStyleSheet(
            'ShareList{background-color:rgb(255, 255, 255);border-style:solid;'
            'border-left-width:1px; border-color:rgba(200, 200, 200, 125)}'
        )

        self.load: GifLabel = AllImage.get_gif(self, GifImage.MIN_LOAD)

        self.set_text_menu_click()

    # 禁止操作
    def prohibit(self, mode: bool) -> None:
        # 是否顯示 等待動畫
        self.load.setVisible(not mode)
        self.setEnabled(mode)

    async def refresh(self) -> None:
        # 清空目錄
        self.cls()
        # 清空點擊
        self.cls_click()
        # 禁止操作
        self.prohibit(False)

        result = await self.share.get_share(0, 1000)

        text_data_list: list[TextData, ...] = []
        if result:
            for data in result['list']:
                # 獲取檔案cid
                data_ico = get_ico(splitext(data['share_title'])[1] if data['file_category'] == 1 else 'folder')

                if data['share_ex_time'] == -1:
                    share_ex_time = get_my_text_data('長期')
                else:
                    share_ex_time = get_my_text_data(time.strftime('%Y-%m-%d %H:%M', time.localtime(data['share_ex_time'])))

                create_time = get_my_text_data(time.strftime('%Y-%m-%d %H:%M', time.localtime(int(data['create_time']))))

                text_data: TextData = TextData(
                    data={
                        'share_code': data['share_code'],
                        'url': f"{data['share_url']}?password={data['receive_code']}",
                    },
                    ico=data_ico,
                    my_text={
                        '名稱': get_my_text_data(data['share_title']),
                        ' 狀態': get_review(data),
                        ' 到期時間': share_ex_time,
                        ' 分享時間': create_time,
                        ' 大小': get_my_text_data(pybyte(int(data['file_size']))),
                        ' 已接收次數': get_my_text_data(data['receive_count']),

                    },
                    mouse=False
                )

                text_data_list.append(text_data)
            self.add_text(text_data_list, refresh=True)
        # 恢復操作
        self.prohibit(True)

    # 設置 text | 背景 右鍵回調
    def set_text_menu_click(self) -> None:
        # 設定 text 下載 右鍵
        self.text_menu_click_connect(
            '複製鏈結', self.copy_url, ico=AllImage.get_ico(IcoImage.COPY)
        )
        # 設定 text 下載 右鍵
        self.text_menu_click_connect(
            '變更訪問碼', lambda: create_task(self.set_receive_code()), ico=AllImage.get_ico(IcoImage.CHANGE)
        )
        self.text_menu_click_connect(
            '取消分享', lambda: create_task(self.cancel_share()), ico=AllImage.get_ico(IcoImage.CANCEL)
        )

    def copy_url(self) -> None:
        data = self.extra()
        url_text = ''
        if isinstance(data, dict):
            url_text = data['url']
        else:
            for _data in data:
                url_text += f"{_data['url']}\n"
        QApplication.clipboard().setText(url_text)

    @error()
    async def set_receive_code(self) -> ErrorResult:
        # 禁止操作
        self.prohibit(False)
        data = self.extra()
        if isinstance(data, dict):
            result = await self.share.cancel_share(data['share_code'])
        else:
            share_code_list = []
            for _data in data:
                share_code_list.append(_data['share_code'])
            result = await self.share.cancel_share(share_code_list)
        # 恢復操作
        self.prohibit(True)
        if result:
            create_task(self.refresh())
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='網路異常取消分享失敗', name='請問是否重新嘗試', result='')

    @error()
    async def cancel_share(self) -> ErrorResult:
        # 禁止操作
        self.prohibit(False)
        data = self.extra()
        if isinstance(data, dict):
            result = await self.share.cancel_share(data['share_code'])
        else:
            share_code_list = []
            for _data in data:
                share_code_list.append(_data['share_code'])
            result = await self.share.cancel_share(share_code_list)
        # 恢復操作
        self.prohibit(True)
        if result:
            create_task(self.refresh())
            return ErrorResult(state=True, title='', name='', result='')
        return ErrorResult(state=False, title='網路異常取消分享失敗', name='請問是否重新嘗試', result='')

    def raise_(self) -> None:
        QWidget.raise_(self)
        create_task(self.refresh())

    # 調整大小事件
    def resizeEvent(self, event: QResizeEvent) -> None:
        QList.resizeEvent(self, event)
        self.load.move(int(self.width() / 2), int(self.height() / 2))

