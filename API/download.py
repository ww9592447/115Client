import time
import math
import base64
import json
import hashlib
import httpx
from urllib.parse import quote
from typing import TypedDict, Callable, NotRequired
from asyncio import CancelledError

from Modules import srequests
from Modules.type import Credential


class Result(TypedDict):
    state: bool
    result: NotRequired[str]
    data: NotRequired[bytearray]


class MyRsa:
    def __init__(self):
        self.n = int(
            '8686980c0f5a24c4b9d43020cd2c22703ff3f450756529058b1cf88f09b8602136477198a6e2683149659bd122c33592fdb5ad479'
            '44ad1ea4d36c6b172aad6338c3bb6ac6227502d010993ac967d1aef00f0c8e038de2e4d3bc2ec368af2e9f10a6f1eda4f7262f136'
            '420c07c331b871bf139f74f3010e3c4fe57df3afb71683',
            16
        )
        self.e = int('10001', 16)

    @staticmethod
    def a2hex(array: dict[int, int]) -> str:
        hex_string = ''
        for i in range(len(array)):
            next_hex_byte = hex(array[i])[2:]
            if len(next_hex_byte) < 2:
                next_hex_byte = f'0{next_hex_byte}'
            hex_string += next_hex_byte
        return hex_string

    @staticmethod
    def hex2a(_hex) -> str:
        text = ''
        for i in range(0, len(_hex), 2):
            text += chr(int(_hex[i:i + 2], 16))
        return text

    def pkcs1pad2(self, s, n):
        if n < len(s) + 11:
            return
        ba = {}
        i = len(s) - 1
        while i >= 0 and n > 0:
            ba[(n := n - 1)] = ord(s[i])
            i -= 1
        ba[(n := n - 1)] = 0
        while n > 2:
            ba[(n := n - 1)] = 0xff
        ba[(n := n - 1)] = 2
        ba[(n - 1)] = 0
        c = self.a2hex(ba)
        return int(c, 16)

    def pkcs1unpad2(self, a):
        b = hex(a)[2:]
        if len(b) % 2 != 0:
            b = '0' + b
        c = self.hex2a(b)
        i = 1
        while ord(c[i]) != 0:
            i += 1
        return c[i + 1:]

    def encrypt(self, text):
        m = self.pkcs1pad2(text, 0x80)
        c = pow(m, self.e, self.n)
        h = hex(c)[2:]
        while len(h) < 0x80 * 2:
            h = '0' + h
        return h

    def decrypt(self, text):
        ba = {}
        i = 0
        while i < len(text):
            ba[i] = ord(text[i])
            i += 1
        a = int(self.a2hex(ba), 16)
        c = pow(a, self.e, self.n)
        d = self.pkcs1unpad2(c)
        return d


class Download:
    def __init__(self, credential: Credential) -> None:
        # 設置115標頭
        self.headers = credential['headers']

        self.rsa = MyRsa()
        self.kts = [
            240, 229, 105, 174, 191, 220, 191, 138, 26, 69, 232, 190, 125, 166, 115, 184, 222, 143, 231, 196,
            69, 218, 134, 196, 155, 100, 139, 20, 106, 180, 241, 170, 56, 1, 53, 158, 38, 105, 44, 134, 0, 107,
            79, 165, 54, 52, 98, 166, 42, 150, 104, 24, 242, 74, 253, 189, 107, 151, 143, 77, 143, 137, 19, 183,
            108, 142, 147, 237, 14, 13, 72, 62, 215, 47, 136, 216, 254, 254, 126, 134, 80, 149, 79, 209, 235,
            131, 38, 52, 219, 102, 123, 156, 126, 157, 122, 129, 50, 234, 182, 51, 222, 58, 169, 89, 52, 102,
            59, 170, 186, 129, 96, 72, 185, 213, 129, 156, 248, 108, 132, 119, 255, 84, 120, 38, 95, 190, 232,
            30, 54, 159, 52, 128, 92, 69, 44, 155, 118, 213, 27, 143, 204, 195, 184, 245
        ]

        self.keyS = [0x29, 0x23, 0x21, 0x5E]
        self.keyL = [120, 6, 173, 76, 51, 134, 93, 24, 76, 1, 63, 70]

        self.downurl = 'http://proapi.115.com/app/chrome/downurl?t={}'

    def xor115Enc(self, src, srclen, key, keylen):
        mod4 = srclen % 4
        ret = []
        if mod4 != 0:
            i = 0
            j = 0
            ref = mod4
            while j < ref if ref >= 0 else j > ref:
                ret.append(src[i] ^ key[i % keylen])
                i = (j := j + 1) if ref >= 0 else (j := j - 1)
        i = mod4
        k = mod4
        ref1 = mod4
        ref2 = srclen
        while k < ref2 if ref1 <= ref2 else k > ref2:
            _key = (i - mod4) % keylen
            if _key < len(key):
                ret.append(src[i] ^ key[(i - mod4) % keylen])
            else:
                ret.append(src[i])

            i = (k := k + 1) if ref1 <= ref2 else (k := k - 1)
        return ret

    def getkey(self, length, key):
        if key is not None:
            results = []
            for i in range(length):
                results.append(((key[i] + self.kts[length * i]) & 0xff) ^ self.kts[length * (length - 1 - i)])
            return results
        if length == 12:
            return self.keyL
        return self.keyS

    def asymEncode(self, src, srclen):
        m = 128 - 11
        ret = ''
        for i in range(math.floor((srclen + m - 1) / m)):
            ret += self.rsa.encrypt(self.bytesToString(src[i * m:min((i + 1) * m, srclen)]))
        return base64.b64encode(self.rsa.hex2a(ret).encode("latin1"))

    def asymDecode(self, src, srclen):
        m = 128
        ret = ''
        for i in range(math.floor((srclen + m - 1) / m)):
            ret += self.rsa.decrypt(self.bytesToString(src[i * m:min((i + 1) * m, srclen)]))
        return self.stringToBytes(ret)

    def symEncode(self, src, srclen, key1, key2):
        k1 = self.getkey(4, key1)
        k2 = self.getkey(12, key2)
        ret = self.xor115Enc(src, srclen, k1, 4)
        ret.reverse()
        ret = self.xor115Enc(ret, srclen, k2, 12)
        return ret

    def symDecode(self, src, srclen, key1, key2):
        k1 = self.getkey(4, key1)
        k2 = self.getkey(12, key2)
        ret = self.xor115Enc(src, srclen, k2, 12)
        ret.reverse()
        ret = self.xor115Enc(ret, srclen, k1, 4)
        return ret

    def bytesToString(self, buf):
        ret = ''
        for i in buf:
            ret += chr(i)
        return ret

    def stringToBytes(self, s):
        ret = []
        for i in s:
            ret.append(ord(i))
        return ret

    def encode(self, src, tm):
        key = self.stringToBytes(self.md5(f'!@###@#{tm}DFDR@#@#'))
        tmp = self.stringToBytes(src)
        tmp = self.symEncode(tmp, len(tmp), key, None)
        tmp = key[0:16] + tmp
        return self.asymEncode(tmp, len(tmp)), key

    def decode(self, src, key):
        tmp = self.stringToBytes(base64.b64decode(src.encode()).decode("latin1"))
        tmp = self.asymDecode(tmp, len(tmp))
        return self.bytesToString(self.symDecode(tmp[16:], len(tmp) - 16, key, tmp[0:16]))

    @staticmethod
    def md5(string) -> str:
        string = string.encode('utf-8')
        m = hashlib.md5()
        m.update(string)
        return m.hexdigest()

    async def get_url(self, pc: str) -> Result:
        tmus = int(time.time())
        tm = math.floor(tmus)
        data, key = self.encode(f'{{"pickcode":"{pc}"}}', tm)
        data = quote(data, safe='...')
        data = f'data={data}'
        ret = await srequests.async_post(self.downurl.format(tm), data=data, headers=self.headers, timeout=5, retry=5)
        try:
            if ret:
                result = json.loads(self.decode(ret.json()['data'], key))
                return Result(state=True, result=result[list(result)[0]]['url']['url'])
            return Result(state=False, result='')
        except:
            return Result(state=False, result='')

    async def download_part(
            self,
            file_size: int,
            url: str,
            offset: int,
            length: int,
            size_callback: Callable[[int], None] | None = None
    ) -> Result:
        _offset = offset
        _data = bytearray()
        for stop in range(5):
            try:
                async with httpx.AsyncClient() as client:
                    headers = {**{'Range': 'bytes=%d-%d' % (_offset, length)}, **self.headers}
                    async with client.stream('GET', url, headers=headers, timeout=5) as response:
                        async for data in response.aiter_bytes():
                            _data += data
                            _size = len(data)
                            _offset += _size
                            if size_callback:
                                size_callback(_size)
                if _offset == file_size or _offset - 1 == length:
                    return Result(state=True, data=_data)
            except CancelledError:
                raise CancelledError
            except httpx.RequestError:
                pass
        else:
            return Result(state=False, result='網路異常下載失敗')
