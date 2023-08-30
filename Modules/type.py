from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeVar, Optional, TypedDict, Awaitable, Generic, Self, NotRequired

from PyQt5.Qt import QWidget, QFont, QListWidgetItem

from .image import Image

from Modules.menu import Menu


NClickCallable = list[Callable[[], None], ...] | list[Callable[[], Awaitable[None]], ...] | None
YClickCallable = list[Callable[[any], None], ...] | list[Callable[[any], Awaitable[None]], ...] | None
T = TypeVar('T')
Value = TypeVar('Value')


class Config(TypedDict):
    download_max: int
    download_path: str
    download_sha1: bool
    upload_max: int
    upload_thread_max: int
    aria2_rpc_max: int
    aria2_rpc_url: str
    aria2_sha1: bool


class Credential(TypedDict):
    headers: dict[str, str]
    user_id: str


class MyDict(Generic[Value]):
    def __init__(self) -> None:
        self.key: list[str, ...] = []
        self.value: dict[str, Value] = {}

    def append(self, key: str, value: Value) -> None:
        self.key.append(key)
        self.value[key] = value

    def sort(self, key: Self) -> None:
        self.key.sort(key=list(key.value).index)

    def update(self, my_dict: Self) -> None:
        self.key = my_dict.key.copy()
        self.value = my_dict.value.copy()

    def remove(self, key: str) -> None:
        self.key.remove(key)
        self.value.pop(key)

    def index(self, key: str) -> int:
        return self.key.index(key)

    def __len__(self) -> int:
        return len(self.key)

    def __iter__(self) -> Self:
        return iter([self.value[key] for key in self.key])

    def __setitem__(self, key: str, value: Value) -> None:
        self.key.append(key)
        self.value[key] = value

    def __getitem__(self, key: str | int | slice) -> Value:
        if isinstance(key, str):
            return self.value[key]
        elif isinstance(key, int):
            return self.value[self.key[key]]
        elif isinstance(key, slice):
            return [self.value[_key] for _key in self.key[key]]

    def __contains__(self, key: str) -> bool:
        return key in self.value


class QlistData(TypedDict):
    # 目前頁數
    page: int
    # text數量上限
    quantity_limit: int
    # 設置 text 最大大小
    text_height_max: int
    # 設置標題離左邊框多遠
    title_interval: int
    # 設置標題 窗口 最大大小
    title_max: int
    # my_text字體
    font: QFont
    # my_text y座標位置
    my_text_y: int
    # 標題移動條可觸碰大小
    title_moving_bar_size: int
    # 間隔符號
    spacer_symbol: str
    # 間隔符號大小
    spacer_symbol_size: int
    # 空白數量
    spacer_space: int
    # 空白數量大小
    spacer_space_size: int
    # 內容窗口
    scroll_contents: QWidget
    # 最後一個點擊窗口
    first_click: Optional[QWidget]
    # 右鍵菜單
    context_menu: Menu
    # 所有 text 右鍵菜單內容
    menu: dict[str, QListWidgetItem]
    # text右鍵回調
    menu_callable: Callable[[], bool] | None
    # 頁數點擊回調
    page_callable: Callable[[int], None] | None


class NlistData(TypedDict):
    # 目前頁數
    page: int
    # text數量上限
    quantity_limit: int
    # 設置 text 最大大小
    text_height_max: int
    # 內容窗口
    scroll_contents: QWidget
    # 右鍵菜單
    context_menu: Menu
    # 所有 text 右鍵菜單內容
    menu: dict[str, QListWidgetItem]
    # text右鍵回調
    menu_callable: Callable[[], bool] | None
    # 頁數點擊回調
    page_callable: Callable[[int], None] | None
    # 最後一個點擊窗口
    first_click: QWidget | None


class MyTextSlots(TypedDict):
    connect_left_click: YClickCallable
    disconnect_left_click: YClickCallable


class NTextSlots(TypedDict):
    connect_left_click: YClickCallable
    connect_double_click: YClickCallable
    disconnect_left_click: YClickCallable
    disconnect_double_click: YClickCallable
    text: MyTextSlots


class NMyTextData(TypedDict):
    text: str
    color: tuple[tuple[int, int, int], tuple[int, int, int]] | None
    mouse: bool | None


class NTextData(TypedDict, Generic[T]):
    data: T
    ico: Image | None
    text: NMyTextData
    mouse: bool


class MyTextData(TypedDict):
    text: str
    color: tuple[tuple[int, int, int], tuple[int, int, int]] | tuple[int, int, int] | None
    mouse: bool | None
    text_size: list[int, ...]


class TextSlots(TypedDict):
    connect_left_click: YClickCallable
    connect_double_click: YClickCallable
    disconnect_left_click: YClickCallable
    disconnect_double_click: YClickCallable
    my_text: dict[str, MyTextSlots]


class TextData(TypedDict, Generic[T]):
    data: T
    ico: Image | None
    my_text: dict[str, MyTextData]
    mouse: bool


class AllCidData(TypedDict):
    data: dict[int, list[TextData, ...]]
    path: list[tuple[str, str], ...]
    index: dict[str, dict[str, any]]
    refresh: bool
    count: int
    page: int


class NAllCidData(TypedDict):
    data: dict[int, list[NTextData, ...]]
    path: list[tuple[str, str], ...]
    index: dict[str, dict[str, any]]
    refresh: bool
    count: int
    page: int


class StateData(Enum):
    NONE = 'None'
    ERROR = 'Error'
    TEXT = 'Text'
    PAUSE = 'Pause'
    CANCEL = 'Cancel'
    COMPLETE = 'Complete'


class GetFolderData(TypedDict):
    state: bool
    result: dict[str, dict[str, any]] | str


class DownloadFileData(TypedDict):
    start: bool
    pc: str
    url: str
    name: str
    ico: Image
    sha1: str
    path: str
    file_size: int
    all_size: int
    all_range: dict[str, tuple[int, int]]
    state: StateData
    result: str


class DownloadFolderData(TypedDict):
    state: StateData
    path: str
    name: str
    cid: str
    ico: Image
    result: str


@dataclass
class PartInfo:
    index: str
    crc64: str
    etag: str
    size: int


class UploadFileData(TypedDict):
    bucket: str
    upload_key: str
    cb: dict[str, str]
    url: str
    upload_id: str
    path: str
    all_size: int
    all_range: dict[str, tuple[int, int]]
    parts: dict[str, PartInfo]
    file_size: int
    ico: Image
    cid: str
    second: bool
    name: str
    sha1: str
    state: StateData
    dir: str
    result: str
    start: bool


class UploadFolderData(TypedDict):
    cid: str
    dir: str
    name: str
    ico: Image


class Aria2FileData(TypedDict):
    file_size: int
    ico: Image
    name: str
    pc: str
    all_size: int
    path: str
    gid: str
    state: StateData
    sha1: str
    result: str


class ErrorResult(TypedDict):
    state: bool
    title: str
    name: str
    result: str
    retry: NotRequired[bool]


class QrCode(TypedDict):
    state: bool
    uid: NotRequired[str]
    time: NotRequired[str]
    sign: NotRequired[str]
    url: NotRequired[str]


class Cookie(TypedDict):
    uid: str
    cid: str
    seid: str


class LoginResult(TypedDict):
    state: bool
    cookie: NotRequired[Cookie]
    usersessionid: NotRequired[str]
    user_id: NotRequired[str]
    mobile: NotRequired[str]


class ChecksCookie(TypedDict):
    state: int
    user_id: str
