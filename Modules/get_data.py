from pathlib import Path
from typing import TypeVar, Generic
from multiprocessing import Lock


T = TypeVar('T')


def pybyte(bytes_: int, s: bool = False) -> str:
    if s:
        s = '/s'
    else:
        s = ''
    if bytes_ >= 1024:
        kb = bytes_ / 1024
        if kb <= 1024:
            return "%.2fKB%s" % (kb, s)
        mb = kb / 1024
        if mb <= 1024:
            return "%.2fMB%s" % (mb, s)
        else:
            gb = mb / 1024
            if gb <= 1024:
                return "%.2fGB%s" % (gb, s)
            tb = gb / 1024
            return "%.2fTB%s" % (tb, s)
    else:
        return "%.2fB%s" % (bytes_, s)


def get_path(path: str, value: bool = True) -> str | Path:
    _path = Path(path)
    if value:
        try:
            _path = _path.resolve()
        except (Exception, ):
            pass
        return str(_path)
    return _path


class SetData(Generic[T]):
    def __init__(self, all_data: dict[str, T], uuid: str, lock: Lock) -> None:
        self.lock: Lock = lock
        self.all_data: dict[str, T] = all_data
        with self.lock:
            self._all_data: T = all_data[uuid].copy()
        self.uuid: str = uuid

    def __enter__(self) -> T:
        return self._all_data

    def __exit__(self, _type, value, traceback) -> None:
        with self.lock:
            self.all_data[self.uuid] = self._all_data
