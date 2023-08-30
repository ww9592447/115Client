import time
import threading
from asyncio import sleep, run, Future, AbstractEventLoop, gather, CancelledError
from functools import wraps
from pathlib import Path, PureWindowsPath
from winfspy import (
    FileSystem,
    BaseFileSystemOperations,
    FILE_ATTRIBUTE,
    CREATE_FILE_CREATE_OPTIONS,
    NTStatusObjectNameNotFound,
    NTStatusDirectoryNotEmpty,
    NTStatusNotADirectory,
    NTStatusObjectNameCollision,
    NTStatusEndOfFile,
    NTStatusMediaWriteProtected,
)
from winfspy.plumbing.win32_filetime import filetime_now
from winfspy.plumbing.security_descriptor import SecurityDescriptor
from API.download import Download


def operation(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            with self._thread_lock:
                result = fn(self, *args, **kwargs)
        except Exception as exc:
            raise
        else:
            return result

    return wrapper


class FileObj:
    def __init__(self, path: PureWindowsPath, attributes: FILE_ATTRIBUTE, security_descriptor: SecurityDescriptor,
                 allocation_size: int = 0, download: Download = None, pc: str = None, loop=None) -> None:
        # 虛擬文件路徑
        self.path: PureWindowsPath = path
        # 文件屬性
        self.attributes: FILE_ATTRIBUTE = attributes
        # 安全描述符
        self.security_descriptor: SecurityDescriptor = security_descriptor
        # 獲取現在文件時間
        now = filetime_now()
        # 設置建立日期
        self.creation_time: int = now
        # 設置上次訪問時間
        self.last_access_time: int = now
        # 設置存取日期
        self.last_write_time: int = now
        # 設置修改日期
        self.change_time: int = now
        # 設置索引
        self.index_number: int = 0
        # 設置檔案大小
        self.file_size: int = allocation_size
        # 設置檔案內存
        self.data: bytearray = bytearray(allocation_size)
        # 115下載api
        self.download: Download = download
        # 115下載id
        self.pc: str = pc
        # 115下載url
        self.url: str = ''
        # 設置下載index
        self.index: int = 0
        # 設置待下載數據
        self.wait_data: list[list[int, int], ...] = []
        # 設置已下載數據
        self.download_data: list[list[int, int], ...] = []
        # 設置是否關閉
        self.end: bool = False
        # 設置任務
        self.task: Future[type[any, ...]] | None = None
        # 設置任務是否取消
        self.task_cancel = False

        self.loop: AbstractEventLoop = loop
        # self.loop = new_event_loop()
        # set_event_loop(self.loop)

    @property
    def name(self) -> str:
        """File name, without the path"""
        return self.path.name

    @property
    def file_name(self) -> str:
        """File name, including the path"""
        return str(self.path)

    @property
    def allocation_size(self) -> int:
        return len(self.data)

    def set_file_size(self, file_size: int) -> None:
        self.data = bytearray(file_size)
        self.file_size = file_size

    def set_download_data(self, offset: int, size: int) -> None:
        if not self.download_data:
            self.download_data.append([offset, size])
            return
        for index, data in enumerate(self.download_data):
            if offset == data[1] + 1:
                data[1] = size
                if len(self.download_data) > index + 1:
                    _data = self.download_data[index + 1]
                    if size + 1 == _data[0]:
                        data[1] = _data[1]
                        self.download_data.pop(index + 1)
                break
            elif size + 1 == data[0]:
                data[0] = offset
                break
            elif offset < data[0]:
                self.download_data.insert(index, [offset, size])
                break
        else:
            self.download_data.append([offset, size])

    async def download_run(self) -> bool:
        end_time = None
        while 1:
            while self.index != -1 and len(self.wait_data) > self.index and self.url:
                if self.end:
                    if end_time is None:
                        end_time = time.time()
                    elif time.time() - end_time > 5:
                        return True
                elif end_time and not self.end:
                    end_time = None
                offset, size = self.wait_data.pop(self.index)
                result = await self.download.download_part(self.file_size, self.url, offset, size)
                if result['state']:
                    self.data[offset: size + 1] = result['data']
                    self.set_download_data(offset, size)
                else:
                    raise CancelledError
                await sleep(0.1)
            if self.wait_data:
                self.index = 0
            else:
                return True

    def set_range(self) -> None:
        part = 11000000
        index = 0
        if self.file_size > part:
            for index in range(self.file_size // part):
                size = index * 11000000
                self.wait_data.append([index * part, size + part - 1])
            if self.file_size % part != 0:
                index += 1
                self.wait_data.append([index * part, self.file_size])
        else:
            self.wait_data.append([0, self.file_size])

    async def get(self, offset: int, length: int) -> bool:
        _time = time.time()
        for index, data in enumerate(self.wait_data):
            if data[0] <= offset <= data[1]:
                self.index = index
                break
        else:
            for index, data in enumerate(self.wait_data):
                if data[0] > offset:
                    self.index = index - 1
                    break
            else:
                self.index = len(self.wait_data) - 1
        while 1:
            if self.task_cancel:
                return False
            elif time.time() - _time > 7:
                print(offset, length, offset + length, self.download_data)
            size = min(self.file_size, offset + length)
            for index, data in enumerate(self.download_data):
                if data[0] <= offset <= data[1] and data[1] >= size:
                    return True
            await sleep(0.1)

    async def wait_download(self):
        task_list = [self.loop.create_task(self.download_run()), self.loop.create_task(self.download_run())]
        task = gather(*task_list)
        try:
            await task
        except CancelledError:
            for task in task_list:
                task.cancel()
            for task in task_list:
                if not task.done():
                    await task
            self.task_cancel = True

    def read(self, offset: int, length: int) -> bytearray:
        if self.end:
            self.end = False
        if len(self.data) == 0:
            self.data: bytearray = bytearray(self.file_size)
        if self.url == '':
            result = run(self.download.get_url(self.pc))
            if result['state'] is False:
                raise NTStatusEndOfFile()
            self.url = result['result']
            self.set_range()
        if self.wait_data and (self.task is None or self.task.done()):
            self.task = self.loop.create_task(self.wait_download())
            self.task.add_done_callback(self.close)
        if run(self.get(offset, length)) is False:
            raise NTStatusEndOfFile()
        data = self.data[offset: offset + length]
        return data

    def get_file_info(self) -> dict:
        return {
            "file_attributes": self.attributes,
            "allocation_size": self.allocation_size,
            "file_size": self.file_size,
            "creation_time": self.creation_time,
            "last_access_time": self.last_access_time,
            "last_write_time": self.last_write_time,
            "change_time": self.change_time,
            "index_number": self.index_number,
        }

    def close(self, task=None) -> None:
        if self.end and self.task and self.task.done():
            print('初始化')
            self.data.clear()
            self.wait_data.clear()
            self.download_data.clear()
            self.url: str = ''
            self.index: int = 0
            self.end: bool = False
            self.task: Future | None = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}:{self.file_name}"


class FolderObj:
    def __init__(self, path: PureWindowsPath, attributes: FILE_ATTRIBUTE, security_descriptor: SecurityDescriptor):
        # 虛擬文件路徑
        self.path: PureWindowsPath = path
        # 文件屬性
        self.attributes: FILE_ATTRIBUTE = attributes
        # 安全描述符
        self.security_descriptor: SecurityDescriptor = security_descriptor
        # 獲取現在文件時間
        now = filetime_now()
        # 設置建立日期
        self.creation_time: int = now
        # 設置上次訪問時間
        self.last_access_time: int = now
        # 設置存取日期
        self.last_write_time: int = now
        # 設置修改日期
        self.change_time: int = now
        # 設置索引
        self.index_number: int = 0
        # 設置目錄大小
        self.file_size = 0

        self.allocation_size = 0
        assert self.attributes & FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY

    @property
    def name(self) -> str:
        """File name, without the path"""
        return self.path.name

    @property
    def file_name(self) -> str:
        """File name, including the path"""
        return str(self.path)

    def get_file_info(self) -> dict:
        return {
            "file_attributes": self.attributes,
            "allocation_size": self.allocation_size,
            "file_size": self.file_size,
            "creation_time": self.creation_time,
            "last_access_time": self.last_access_time,
            "last_write_time": self.last_write_time,
            "change_time": self.change_time,
            "index_number": self.index_number,
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}:{self.file_name}"


class InMemoryFileSystemOperations(BaseFileSystemOperations):
    def __init__(self, volume_label: str, read_only: bool = False) -> None:
        super().__init__()
        if len(volume_label) > 31:
            raise ValueError("`volume_label` must be 31 characters long max")
        max_file_nodes = 1024
        max_file_size = 16 * 1024 * 1024
        file_nodes = 1

        self._volume_info = {
            "total_size": max_file_nodes * max_file_size,
            "free_size": (max_file_nodes - file_nodes) * max_file_size,
            "volume_label": volume_label,
        }
        # 設定是否只讀
        self.read_only: bool = read_only
        # 設置初始目錄路徑
        self._root_path: PureWindowsPath = PureWindowsPath("/")
        # 設置初始目錄
        self._root_obj: FolderObj = FolderObj(
            self._root_path,
            FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY,
            SecurityDescriptor.from_string("O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;FA;;;WD)"),
        )
        self._entries: dict[PureWindowsPath, FileObj | FolderObj] = {self._root_path: self._root_obj}
        self._thread_lock = threading.Lock()

    @operation
    def get_volume_info(self):
        return self._volume_info

    @operation
    def set_volume_label(self, volume_label):
        self._volume_info["volume_label"] = volume_label

    @operation
    def get_security_by_name(self, file_name):
        file_name = PureWindowsPath(file_name)

        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            raise NTStatusObjectNameNotFound()

        return (
            file_obj.attributes,
            file_obj.security_descriptor.handle,
            file_obj.security_descriptor.size,
        )

    @operation
    def create(
        self,
        file_name: str,
        create_options: int,
        granted_access: int,
        file_attributes: FILE_ATTRIBUTE,
        security_descriptor: SecurityDescriptor,
        allocation_size: int,
        download: Download,
        pc: str,
        loop: AbstractEventLoop
    ):
        if self.read_only:
            raise NTStatusMediaWriteProtected()

        file_name = PureWindowsPath(file_name)

        # 獲取父目錄路徑
        try:
            parent_file_obj = self._entries[file_name.parent]
            if isinstance(parent_file_obj, FileObj):
                raise NTStatusNotADirectory()
        except KeyError:
            raise NTStatusObjectNameNotFound()

        # 查看文件是否存在
        if file_name in self._entries:
            raise NTStatusObjectNameCollision()

        if create_options & CREATE_FILE_CREATE_OPTIONS.FILE_DIRECTORY_FILE:
            file_obj = self._entries[file_name] = FolderObj(
                file_name, file_attributes, security_descriptor
            )
        else:
            file_obj = self._entries[file_name] = FileObj(
                file_name, file_attributes, security_descriptor, allocation_size, download, pc, loop
            )

        return file_obj

    @operation
    def get_security(self, file_context: FileObj | FolderObj):
        return file_context.security_descriptor

    @operation
    def set_security(self, file_context: FileObj | FolderObj, security_information, modification_descriptor):
        if self.read_only:
            raise NTStatusMediaWriteProtected()

        new_descriptor = file_context.security_descriptor.evolve(
            security_information, modification_descriptor
        )
        file_context.security_descriptor = new_descriptor

    @operation
    def rename(self, file_context: FileObj | FolderObj, file_name: PureWindowsPath, new_file_name: PureWindowsPath
               , replace_if_exists):
        pass

    @operation
    def open(self, file_name: PureWindowsPath, create_options: int, granted_access: int) -> FileObj:
        file_name = PureWindowsPath(file_name)

        try:
            file_obj = self._entries[file_name]
        except KeyError:
            raise NTStatusObjectNameNotFound()

        return file_obj

    @operation
    def close(self, file_context: FileObj | FolderObj) -> None:
        file_context.end = True

        if isinstance(file_context, FileObj):
            file_context.close()

    @operation
    def get_file_info(self, file_context: FileObj | FolderObj) -> dict:
        return file_context.get_file_info()

    @operation
    def set_basic_info(
        self,
        file_context: FileObj | FolderObj,
        file_attributes: FILE_ATTRIBUTE,
        creation_time: int,
        last_access_time: int,
        last_write_time: int,
        change_time: int,
        file_info,
    ) -> None:
        pass

    @operation
    def set_file_size(self, file_context: FileObj | FolderObj, new_size: int, set_allocation_size: bool) -> None:
        pass

    @operation
    def can_delete(self, file_context: FileObj | FolderObj, file_name: str) -> None:
        file_name = PureWindowsPath(file_name)

        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            raise NTStatusObjectNameNotFound

        if isinstance(file_obj, FolderObj):
            for entry in self._entries.keys():
                try:
                    if entry.relative_to(file_name).parts:
                        raise NTStatusDirectoryNotEmpty()
                except ValueError:
                    continue

    @operation
    def read_directory(self, file_context: FileObj | FolderObj, marker):
        entries = []
        file_obj = file_context

        # Not a directory
        if isinstance(file_obj, FileObj):
            raise NTStatusNotADirectory()

        # The "." and ".." should ONLY be included if the queried directory is not root
        if file_obj.path != self._root_path:
            parent_obj = self._entries[file_obj.path.parent]
            entries.append({"file_name": ".", **file_obj.get_file_info()})
            entries.append({"file_name": "..", **parent_obj.get_file_info()})

        # Loop over all entries
        for entry_path, entry_obj in self._entries.items():
            try:
                relative = entry_path.relative_to(file_obj.path)
            # Filter out unrelated entries
            except ValueError:
                continue
            # Filter out ourself or our grandchildren
            if len(relative.parts) != 1:
                continue
            # Add direct chidren to the entry list
            entries.append({"file_name": entry_path.name, **entry_obj.get_file_info()})

        # Sort the entries
        entries = sorted(entries, key=lambda x: x["file_name"])

        # No filtering to apply
        if marker is None:
            return entries

        # Filter out all results before the marker
        for i, entry in enumerate(entries):
            if entry["file_name"] == marker:
                return entries[i + 1:]

    @operation
    def get_dir_info_by_name(self, file_context: FolderObj | FileObj, file_name: PureWindowsPath):
        path = file_context.path / file_name
        try:
            entry_obj = self._entries[path]
        except KeyError:
            raise NTStatusObjectNameNotFound()

        return {"file_name": file_name, **entry_obj.get_file_info()}

    @operation
    def read(self, file_context: FolderObj | FileObj, offset: int, length: int) -> bytearray:
        return file_context.read(offset, length)

    @operation
    def write(self, file_context: FolderObj | FileObj, buffer, offset, write_to_end_of_file, constrained_io) -> None:
        pass

    @operation
    def cleanup(self, file_context: FolderObj | FileObj, file_name: PureWindowsPath, flags) -> None:
        pass

    @operation
    def overwrite(
        self, file_context: FolderObj | FileObj, file_attributes: FILE_ATTRIBUTE, replace_file_attributes: bool,
            allocation_size: int
    ) -> None:
        pass

    @operation
    def flush(self, file_context: FolderObj | FileObj) -> None:
        pass


def create_memory_file_system(mountpoint, testing=False):
    mountpoint = Path(mountpoint)
    is_drive = mountpoint.parent == mountpoint
    reject_irp_prior_to_transact0 = not is_drive and not testing

    operations = InMemoryFileSystemOperations("memfs")

    fs = FileSystem(
        str(mountpoint),
        operations,
        sector_size=512,
        sectors_per_allocation_unit=1,
        volume_creation_time=filetime_now(),
        volume_serial_number=0,
        file_info_timeout=1000,
        case_sensitive_search=1,
        case_preserved_names=1,
        unicode_on_disk=1,
        persistent_acls=1,
        post_cleanup_when_modified_only=1,
        um_file_context_is_user_context2=1,
        file_system_name=str(mountpoint),
        prefix="\Server\Share",
        debug=False,
        reject_irp_prior_to_transact0=reject_irp_prior_to_transact0,
        # security_timeout_valid=1,
        # security_timeout=10000,
    )
    return fs


class Play:
    def __init__(self, download: Download, loop: AbstractEventLoop):
        self.disk: str = 'X:'
        self.loop: AbstractEventLoop = loop
        self.fs = create_memory_file_system(self.disk)
        self.download = download
        self.data = bytearray()

    def add(self, name, size, pc):
        security_descriptor = SecurityDescriptor.from_string("O:BAG:BAD:NO_ACCESS_CONTROL")
        self.fs.operations.create(
            fr'\{name}', 33554500, 1507743, FILE_ATTRIBUTE.FILE_ATTRIBUTE_ARCHIVE, security_descriptor, int(size),
            self.download, pc, self.loop
        )

    def start(self) -> None:
        self.fs.start()

    def stop(self) -> None:
        self.fs.stop()
