import requests, contextlib
from io import BytesIO
from uuid import uuid4


@contextlib.contextmanager
def reset(buffer):
    original_position = buffer.tell()
    buffer.seek(0, 2)
    yield
    buffer.seek(original_position, 0)


class Callback:
    def __init__(self):
        self.all_size = 0

    def __call__(self, f, callback=None):
        multipart = MultipartEncoder(f)
        return MultipartEncoderMonitor(multipart, self, callback)


class CustomBytesIO(BytesIO):
    def __init__(self, buffer=None):
        super(CustomBytesIO, self).__init__(buffer)

    def _get_end(self):
        current_pos = self.tell()
        self.seek(0, 2)
        length = self.tell()
        self.seek(current_pos, 0)
        return length

    @property
    def len(self):
        length = self._get_end()
        return length - self.tell()

    def append(self, bytes):
        with reset(self):
            written = self.write(bytes)
        return written

    # 刪除已上傳數據
    def smart_truncate(self):
        to_be_read = self.len
        already_read = self._get_end() - to_be_read
        if already_read >= to_be_read:
            old_bytes = self.read()
            self.seek(0, 0)
            self.truncate()
            self.write(old_bytes)
            self.seek(0, 0)  # We want to be at the beginning


class Part(object):
    def __init__(self, body):
        self.body = body
        #可能沒用
        self.len = self.body.len

    @classmethod
    def from_field(cls, field):
        body = CustomBytesIO(field)
        return cls(body)

    def bytes_left_to_write(self):
        return self.body.len > 0

    def write_to(self, buffer, size):
        written = 0

        while self.body.len > 0 and (size == -1 or written < size):
            written += buffer.append(self.body.read(size))
        return written


class MultipartEncoder:
    def __init__(self, fields):

        self.boundary_value = uuid4().hex

        self._encoded_boundary = b''.join([f'--{self.boundary_value}'.encode(),b'\r\n'])

        self._end_boundary = f'--{self.boundary_value}--\r\n'.encode()

        self.fields = fields

        self._current_part = None

        self.finished = False

        self._len = None

        self.parts = [Part.from_field(i)for i in self._iter_fields()]

        self._iter_parts = iter(self.parts)

        self._buffer = CustomBytesIO()

    def _iter_fields(self):
        Content_Disposition = b'Content-Disposition: form-data'
        if isinstance(self.fields, dict):
            for _name,_data in self.fields.items():
                if 'filename' in _data and 'data' in _data:
                    name = f'name="{_name}"'.encode()
                    filename = f'filename="{_data["filename"]}"'.encode()
                    if 'type' in _data:
                        content_type = f'Content-Type: {_data["type"]}\r\n\r\n'.encode()
                        content_type = content_type + _data['data'] + b'\r\n'
                        data = self._encoded_boundary + b'; '.join([Content_Disposition, name, filename, content_type])
                        yield data
                    else:
                        filename = filename + b'\r\n\r\n' + _data['data'] + b'\r\n'
                        data = self._encoded_boundary + b'; '.join([Content_Disposition, name, filename])
                        yield data
        elif isinstance(self.fields, bytes):
            yield self.fields

    def _next_part(self):
        try:
            p = self._current_part = next(self._iter_parts)
        except StopIteration:
            p = None
        return p

    def _load(self, amount):
        self._buffer.smart_truncate()

        part = self._current_part or self._next_part()
        while amount == -1 or amount > 0:

            written = 0
            if part and not part.bytes_left_to_write():
                part = self._next_part()
            if not part:
                if isinstance(self.fields, dict):
                    self._buffer.append(self._end_boundary)
                self.finished = True
                break
            written += part.write_to(self._buffer, amount)

            if amount != -1:
                amount -= written

    @property
    def content_type(self):
        return str(
            'multipart/form-data; boundary={0}'.format(self.boundary_value)
            )

    def read(self, size=-1):
        if not self.finished:
            self._load(size)
        return self._buffer.read(size)

    @property
    def len(self):
        return self._len or self._calculate_length()

    def _calculate_length(self):
        if isinstance(self.fields, dict):
            self._len = sum(p.len for p in self.parts) + len(self._end_boundary)
        else:
            self._len = sum(p.len for p in self.parts)
        return self._len


class MultipartEncoderMonitor():
    def __init__(self, encoder, size, callback=None):
        self.size = size

        self.encoder = encoder

        self.callback = callback

        self.len = self.encoder.len

        self.bytes_read = 0

    @property
    def content_type(self):
        return self.encoder.content_type

    def read(self, size=-1):
        try:
            string = self.encoder.read(size)
            if self.callback:
                self.size.all_size += len(string)
                self.bytes_read += len(string)
                self.callback(self.size.all_size)
            return string
        except Exception as f:
            self.size.all_size -= self.bytes_read
            raise f

    async def async_read(self, size=8192):
        try:
            while (string := self.encoder.read(size)) != b'':
                if self.callback:
                    self.size.all_size += len(string)
                    self.bytes_read += len(string)
                    self.callback(self.size.all_size)
                yield string
        except Exception as f:
            self.size.all_size -= self.bytes_read
            self.bytes_read = 0
            raise f

    def delete(self):
        self.size.all_size -= self.bytes_read
        self.bytes_read = 0


if __name__ == '__main__':
    z = b'b456'
    callback = Callback()
    multipart = callback(z)
    # multipart.read(8192)
    # multipart.read(8192)
    r = requests.post('http://httpbin.org/post', data=multipart)
    print(r.text)
    # multipart.read(8192)
