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


class Upload115:
    def __init__(self, config):
        self.directory = Directory(config)
        # 獲取 Token url
        self.getinfoURL = 'https://uplb.115.com/3.0/getuploadinfo.php'
        # 新增資料夾 url
        self.directoryURL = 'https://webapi.115.com/files/add'
        # 秒傳 url
        self.initURL = 'http://uplb.115.com/3.0/initupload.php?appid=0&appversion=2.0.1.7&format=json&isp=0&sig={}&t={}&topupload=0&rt=0&token={}'

        self.user_id = None
        self.userkey = None
        self.token = {}
        self.retry = 0
        self.task = None
        self.headers = {
            'Cookie': config['設定'].get('cookie', raw=True),
            'Content-Type': 'application/x-www-form-urlencoded',
            "User-Agent": 'Mozilla/5.0;  Mac  OS  X/10.15.7;  115Desktop/2.0.1.7'
        }
        self.detect = {}
        self.thread = int(config['upload']['單文件上傳線程'])

    async def getuserkey(self):
        result = await srequests.async_get("http://proapi.115.com/app/uploadinfo", headers=self.headers)
        if result is False:
            return False
        result = result.json()
        self.user_id = str(result['user_id'])
        self.userkey = str(result['userkey']).upper()

    async def getinfo(self):
        body = await srequests.async_get(self.getinfoURL, params={'t': int(time.time())}, headers=self.headers)
        if body is False:
            return False
        self.token.update(body.json())

    async def gettoken(self):
        _body = await srequests.async_get(self.token['gettokenurl'], params={'t': int(time.time())},
                                          headers=self.headers)
        if _body is False:
            return False
        self.token.update(_body.json())
        self.token['time'] = time.time()

    # 使用sha1開始秒傳
    async def upload_file_by_sha1(self, preid, fileid, filesize, filename, cid):
        target = f'U_1_{cid}'
        tm = int(time.time())
        s1 = hashlib.sha1(f'{self.user_id}{fileid}{target}0'.encode('utf8')).hexdigest()
        s2 = self.userkey + s1 + "000000"
        sig = hashlib.sha1(s2.encode('utf8')).hexdigest().upper()
        h1 = hashlib.md5(self.user_id.encode('utf8')).hexdigest()
        _token = f'Qclm8MGWUv59TnrR0XPg{fileid}{filesize}{preid}{self.user_id}{str(tm)}{h1}2.0.1.7'.encode('utf8')
        token = hashlib.md5(_token).hexdigest()
        url = self.initURL.format(sig, tm, token)
        data = {
            'fileid': fileid,
            'filename': filename,
            'filesize': filesize,
            'preid': preid,
            'target': target,
            'userid': self.user_id,
        }
        result = await srequests.async_post(url, data=data, headers=self.headers)
        if result is False:
            return False
        return result.json()

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
            print(cb)
            print('-----------2')
            print(self.token['SecurityToken'])
            print('-----------2')
            print(url)
            print('-----------2')
            print(key)
            print('-----------2')
            print(data)
            print('-----------2')
            print(headers)
            return False
        try:
            return result.json()
        except Exception as e:
            print(cb)
            print('-----------6')
            print(self.token['SecurityToken'])
            print('-----------6')
            print(url)
            print('-----------6')
            print(key)
            print('-----------6')
            print(data)
            print('-----------6')
            print(headers)
            print('-----------')
            print(e)
            print('-----------')
            print(result)
            print('------------')
            print(result.text)
            raise e