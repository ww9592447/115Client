from urllib.parse import urlparse
import re
import datetime
import hmac
import hashlib
import time
import base64
import srequests
import xml.etree.ElementTree as ElementTree
from .directory import Directory
from Crypto.Cipher import AES
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import lz4.block
import json
import struct
import random
import binascii
from urllib.parse import urlencode


class ErrInvalidEncodedData(Exception):
    def __init__(self):
        super().__init__()

class Hash:
    @staticmethod
    def md5(data: str) -> str:
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    @staticmethod
    def sha1(data: bytes) -> str:
        s = hashlib.sha1()
        s.update(data)
        return s.hexdigest()

    @staticmethod
    def sha1_file(path: str) -> str:
        with open(path, 'rb') as f:
            sha = hashlib.sha1()
            while True:
                data = f.read(1024 * 128)
                if not data:
                    break
                sha.update(data)
            return sha.hexdigest().upper()

    @staticmethod
    def sha1_file_range(file_path: str, sign_check: str):
        with open(file_path, 'rb') as f:
            sign_check: list[str, ...] = sign_check.split('-')
            f.seek(int(sign_check[0]), 0)
            sha = hashlib.sha1()
            sha.update(f.read(int(sign_check[1]) - int(sign_check[0]) + 1))
            return sha.hexdigest().upper()


class Cipher:
    _pub_key: bytes = None
    _aes_key: bytes = None
    _aes_iv: bytes = None
    _crc_salt = b'^j>WD3Kr?J2gLFjD4W2y@'

    def __init__(self) -> None:
        _server_pub_key = bytes([
            0x04, 0x57, 0xa2, 0x92, 0x57, 0xcd, 0x23, 0x20,
            0xe5, 0xd6, 0xd1, 0x43, 0x32, 0x2f, 0xa4, 0xbb,
            0x8a, 0x3c, 0xf9, 0xd3, 0xcc, 0x62, 0x3e, 0xf5,
            0xed, 0xac, 0x62, 0xb7, 0x67, 0x8a, 0x89, 0xc9,
            0x1a, 0x83, 0xba, 0x80, 0x0d, 0x61, 0x29, 0xf5,
            0x22, 0xd0, 0x34, 0xc8, 0x95, 0xdd, 0x24, 0x65,
            0x24, 0x3a, 0xdd, 0xc2, 0x50, 0x95, 0x3b, 0xee,
            0xba,
        ])
        # Use P-224 curve
        curve = ec.SECP224R1()
        # Parse server key
        server_key = ec.EllipticCurvePublicKey.from_encoded_point(
            curve=curve, data=_server_pub_key)
        # Generate client key
        ec_key = ec.generate_private_key(curve=curve, backend=default_backend())
        self._pub_key = b'\x1d' + ec_key.public_key().public_bytes(
            encoding=Encoding.X962, format=PublicFormat.CompressedPoint)
        # ECDH key exchange
        shared_secret = ec_key.exchange(ec.ECDH(), server_key)
        self._aes_key = shared_secret[:16]
        self._aes_iv = shared_secret[-16:]

    def encode_token(self, timestamp: int) -> str:
        token = bytearray(struct.pack(
            '<15sBII15sBI',
            self._pub_key[:15], 0, 115, timestamp,
            self._pub_key[15:], 0, 1
        ))
        r1, r2 = random.randint(0, 0xff), random.randint(0, 0xff)

        for i in range(len(token)):
            if i < 24:
                token[i] = token[i] ^ r1
            else:
                token[i] = token[i] ^ r2
        # Calculate and append CRC32 checksum
        checksum = binascii.crc32(self._crc_salt + token) & 0xffffffff
        token += struct.pack('<I', checksum)
        # Base64 encode
        return binascii.b2a_base64(token, newline=False).decode()

    def encode(self, data) -> bytes:
        pad_size = AES.block_size - len(data) % AES.block_size
        if pad_size != AES.block_size:
            data += bytes([0] * pad_size)
        encrypter = AES.new(
            key=self._aes_key,
            mode=AES.MODE_CBC,
            iv=self._aes_iv
        )
        return encrypter.encrypt(data)

    def decode(self, data: bytes) -> bytes:
        ciphertext, tail = data[:-12], bytearray(data[-12:])
        if binascii.crc32(self._crc_salt + tail[0:8]) & 0xffffffff != struct.unpack('<I', tail[8:12])[0]:
            raise ErrInvalidEncodedData()
        # Decrypt
        decrypter = AES.new(
            key=self._aes_key,
            mode=AES.MODE_CBC,
            iv=self._aes_iv
        )
        plaintext = decrypter.decrypt(ciphertext)
        # Decompress
        for i in range(4):
            tail[i] = tail[i] ^ tail[7]
        dst_size, = struct.unpack('<I', tail[:4])
        src_size, = struct.unpack('<H', plaintext[:2])
        plaintext = lz4.block.decompress(plaintext[2:src_size + 2], dst_size)
        return plaintext


class Upload115:
    # 獲取 用戶 key
    _api_key: str = 'http://proapi.115.com/app/uploadinfo'
    # 獲取 上傳所需資料 url
    _api_info: str = 'https://uplb.115.com/3.0/getuploadinfo.php'
    # 獲取 秒傳 url
    _api_upload: str = 'https://uplb.115.com/4.0/initupload.php'
    # 新增資料夾 url
    _api_new_files: str = 'https://webapi.115.com/files/add'
    # 115 數字id
    user_id: str = ''
    # 115 用戶key
    user_key: str = ''
    # 上傳線程數量
    thread: int = 0
    # 鹽
    salt: str = 'Qclm8MGWUv59TnrR0XPg'
    app_version: str = '2.0.3.6'
    headers: dict[str, str] = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0; Windows NT/10.0.19045; 115Desktop/2.0.3.6',
        'cookie': ''
    }
    token = {'time': 0}
    _ecc: Cipher = Cipher()

    def __init__(self, config):
        self.headers['cookie'] = config['設定'].get('cookie', raw=True)
        self.directory = Directory(config)
        self.thread = int(config['upload']['單文件上傳線程'])

    async def getuserkey(self):
        result = await srequests.async_get(self._api_key, headers=self.headers)
        if result is False:
            return False
        result = result.json()
        self.user_id = str(result['user_id'])
        self.user_key = str(result['userkey']).upper()

    async def getinfo(self):
        body = await srequests.async_get(self._api_info, params={'t': int(time.time())}, headers=self.headers)
        if body is False:
            return False
        self.token.update(body.json())

    async def gettoken(self):
        _body = await srequests.async_get(self.token['gettokenurl'], params={'t': int(time.time())},
                                          headers=self.headers)
        if _body is False:
            return False
        self.token.update(_body.json())
        self.token['time'] = int(time.time())

    def _calculate_token_v4(self, fileid: str, file_size: str, sign_key: str, sign_value: str, timestamp: int) -> str:
        return Hash.md5(
            self.salt + fileid + str(file_size) + sign_key + sign_value + self.user_id +
            str(timestamp) + Hash.md5(self.user_id) + self.app_version
        )

    def get_sig(self, fileid: str, target: str) -> str:
        sz_text = self.user_id + fileid + target + "0"
        result = Hash.sha1(sz_text.encode())
        sz_text = self.user_key + result + "000000"
        return Hash.sha1(sz_text.encode()).upper()

    # 使用sha1開始秒傳
    async def upload_file_by_sha1(self, file_path, fileid, file_size, filename, cid) -> dict[str, str|int]:
        target = f'U_1_{cid}'
        sign_key, sign_value = '', ''
        data = {
            'appid': '0',
            'appversion': self.app_version,
            'filename': filename,
            'filesize': file_size,
            'fileid': fileid,
            'target': target,
            'userid': self.user_id,
            'sig': self.get_sig(fileid, target),
        }
        while True:
            now = int(time.time())
            data.update({
                    't': str(now),
                    'token': self._calculate_token_v4(
                        fileid, file_size, sign_key, sign_value, now
                    )
                })
            if sign_key != '' and sign_value != '':
                data.update({
                    'sign_key': sign_key,
                    'sign_val': sign_value
                })

            url = f'https://uplb.115.com/4.0/initupload.php?k_ec={self._ecc.encode_token(now)}'
            result = await srequests.async_post(
                url, data=self._ecc.encode(urlencode(data).encode()), headers=self.headers
            )
            result = json.loads(self._ecc.decode(result.content))
            if result['status'] == 7:
                sign_key = result['sign_key']
                sign_value = Hash.sha1_file_range(file_path, result['sign_check'])
            else:
                return result

    def get_headers(self, method, key, headers, params=None):
        def get_time():
            timeval = time.time()
            dt = datetime.datetime.fromtimestamp(timeval, datetime.timezone.utc)
            timetuple = dt.timetuple()
            zone = 'GMT'
            return '%s, %02d %s %04d %02d:%02d:%02d %s' % (
                ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][timetuple[6]],
                timetuple[2],
                ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][timetuple[1] - 1],
                timetuple[0], timetuple[3], timetuple[4], timetuple[5],
                zone)

        if params is not None:
            if 'partNumber' in params:
                resource_bytes = f'/fhnfile/{key}?partNumber={params["partNumber"]}&uploadId={params["uploadId"]}'.encode()
            else:
                resource_bytes = f'/fhnfile/{key}?uploadId={params["uploadId"]}'.encode()
        else:
            resource_bytes = f'/fhnfile/{key}?uploads'.encode()

        canon_headers = []
        for k, v in headers.items():
            canon_headers.append((k, v))
        canon_headers.sort(key=lambda x: x[0])
        headers_bytes = ('\n'.join(k + ':' + v for k, v in canon_headers) + '\n').encode()
        date = get_time()
        string_to_sign = b'\n'.join([method.encode(),
                                     b'',
                                     b'',
                                     date.encode(),
                                     headers_bytes + resource_bytes])
        h = hmac.new(self.token['AccessKeySecret'].encode(), string_to_sign, hashlib.sha1)

        signature = base64.b64encode(h.digest()).decode()

        return {'date': date, 'authorization': f"OSS {self.token['AccessKeyId'].strip()}:{signature}",
                **headers}

    async def get_upload_id(self, url, key):
        headers = self.get_headers('POST', key, {'x-oss-security-token': self.token['SecurityToken']})
        result = await srequests.async_post(url, params={'uploads': ''}, headers=headers)
        try:
            ret = result.text
            return re.search('<UploadId>(\S+)</UploadId>', ret)[1]
        except:
            return False

    @staticmethod
    def get_url(endpoint, bucket_name, key):
        p = urlparse(endpoint)
        scheme = p.scheme
        netloc = p.netloc
        return '{0}://{1}.{2}/{3}'.format(scheme, bucket_name, netloc, key)

    async def combine(self, etag, url, key, upload_id, cb):
        root = ElementTree.Element('CompleteMultipartUpload')
        for i in range(1, len(etag) + 1):
            part_node = ElementTree.SubElement(root, "Part")
            ElementTree.SubElement(part_node, 'PartNumber').text = str(i)
            ElementTree.SubElement(part_node, 'ETag').text = etag[str(i)]
        data = ElementTree.tostring(root, encoding='utf-8')
        params = {'uploadId': upload_id}
        headers = self.get_headers('POST', key, {'x-oss-security-token': self.token['SecurityToken'], **cb},
                                   params=params)
        result = await srequests.async_post(url, params=params, data=data,
                                            headers=self.get_headers('POST', f'{key}', headers, params=params))
        if result is False:
            return False
        try:
            return result.json()
        except Exception as e:
            print(result.text)
            return False
