import time
import math
import base64
import srequests
from urllib.parse import quote
import json
import c_rsa

# os.environ["EXECJS_RUNTIME"] = "JScript"


class Download115:
    def __init__(self, config=None):
        self.g_key_l = [0x42, 0xDA, 0x13, 0xBA, 0x78, 0x76, 0x8D, 0x37, 0xE8, 0xEE, 0x04, 0x91]
        self.g_kts = [0xF0, 0xE5, 0x69, 0xAE, 0xBF, 0xDC, 0xBF, 0x5A, 0x1A, 0x45, 0xE8, 0xBE, 0x7D, 0xA6, 0x73, 0x88, 0xDE,
                 0x8F, 0xE7, 0xC4, 0x45, 0xDA, 0x86, 0x94, 0x9B, 0x69, 0x92, 0x0B, 0x6A, 0xB8, 0xF1, 0x7A, 0x38, 0x06,
                 0x3C, 0x95, 0x26, 0x6D, 0x2C, 0x56, 0x00, 0x70, 0x56, 0x9C, 0x36, 0x38, 0x62, 0x76, 0x2F, 0x9B, 0x5F,
                 0x0F, 0xF2, 0xFE, 0xFD, 0x2D, 0x70, 0x9C, 0x86, 0x44, 0x8F, 0x3D, 0x14, 0x27, 0x71, 0x93, 0x8A, 0xE4,
                 0x0E, 0xC1, 0x48, 0xAE, 0xDC, 0x34, 0x7F, 0xCF, 0xFE, 0xB2, 0x7F, 0xF6, 0x55, 0x9A, 0x46, 0xC8, 0xEB,
                 0x37, 0x77, 0xA4, 0xE0, 0x6B, 0x72, 0x93, 0x7E, 0x51, 0xCB, 0xF1, 0x37, 0xEF, 0xAD, 0x2A, 0xDE, 0xEE,
                 0xF9, 0xC9, 0x39, 0x6B, 0x32, 0xA1, 0xBA, 0x35, 0xB1, 0xB8, 0xBE, 0xDA, 0x78, 0x73, 0xF8, 0x20, 0xD5,
                 0x27, 0x04, 0x5A, 0x6F, 0xFD, 0x5E, 0x72, 0x39, 0xCF, 0x3B, 0x9C, 0x2B, 0x57, 0x5C, 0xF9, 0x7C, 0x4B,
                 0x7B, 0xD2, 0x12, 0x66, 0xCC, 0x77, 0x09, 0xA6]
        self.g_key_s = [0x29, 0x23, 0x21, 0x5E]

        self._prsa = "-----BEGIN RSA PUBLIC KEY-----\n\
                MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDR3rWmeYnRClwLBB0Rq0dlm8Mr\n\
                PmWpL5I23SzCFAoNpJX6Dn74dfb6y02YH15eO6XmeBHdc7ekEFJUIi+swganTokR\n\
                IVRRr/z16/3oh7ya22dcAqg191y+d6YDr4IGg/Q5587UKJMj35yQVXaeFXmLlFPo\n\
                kFiz4uPxhrB7BGqZbQIDAQAB\n\
                -----END RSA PUBLIC KEY-----"

        self._srsa = "-----BEGIN RSA PRIVATE KEY-----\n\
        MIICXAIBAAKBgQCMgUJLwWb0kYdW6feyLvqgNHmwgeYYlocst8UckQ1+waTOKHFC\n\
        TVyRSb1eCKJZWaGa08mB5lEu/asruNo/HjFcKUvRF6n7nYzo5jO0li4IfGKdxso6\n\
        FJIUtAke8rA2PLOubH7nAjd/BV7TzZP2w0IlanZVS76n8gNDe75l8tonQQIDAQAB\n\
        AoGANwTasA2Awl5GT/t4WhbZX2iNClgjgRdYwWMI1aHbVfqADZZ6m0rt55qng63/\n\
        3NsjVByAuNQ2kB8XKxzMoZCyJNvnd78YuW3Zowqs6HgDUHk6T5CmRad0fvaVYi6t\n\
        viOkxtiPIuh4QrQ7NUhsLRtbH6d9s1KLCRDKhO23pGr9vtECQQDpjKYssF+kq9iy\n\
        A9WvXRjbY9+ca27YfarD9WVzWS2rFg8MsCbvCo9ebXcmju44QhCghQFIVXuebQ7Q\n\
        pydvqF0lAkEAmgLnib1XonYOxjVJM2jqy5zEGe6vzg8aSwKCYec14iiJKmEYcP4z\n\
        DSRms43hnQsp8M2ynjnsYCjyiegg+AZ87QJANuwwmAnSNDOFfjeQpPDLy6wtBeft\n\
        5VOIORUYiovKRZWmbGFwhn6BQL+VaafrNaezqUweBRi1PYiAF2l3yLZbUQJAf/nN\n\
        4Hz/pzYmzLlWnGugP5WCtnHKkJWoKZBqO2RfOBCq+hY4sxvn3BHVbXqGcXLnZPvo\n\
        YuaK7tTXxZSoYLEzeQJBAL8Mt3AkF1Gci5HOug6jT4s4Z+qDDrUXo9BlTwSWP90v\n\
        wlHF+mkTJpKd5Wacef0vV+xumqNorvLpIXWKwxNaoHM=\n\
        -----END RSA PRIVATE KEY-----"

        # self.prsa = JSEncrypt()
        # self.prsa.setPublicKey(self._prsa)
        # self.srsa = JSEncrypt()
        # self.srsa.setPrivateKey(self._srsa)

        self.prsa_ = c_rsa.JSEncrypt()
        self.prsa_.setPublicKey(self._prsa.encode())
        self.srsa_ = c_rsa.JSEncrypt()
        self.srsa_.setPrivateKey(self._srsa.encode())

        # self.js = execjs.compile(open('rsa.js', encoding='utf-8').read())
        # self.js = execjs.compile(_js)
        if config:
            self.headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Cookie': config['設定'].get('cookie', raw=True),
                    "User-Agent": 'Mozilla/5.0  115disk/11.2.0'
                }
        self.downurl = 'http://proapi.115.com/app/chrome/downurl?t={}'

    def md5(self, str):
        str = str.encode('utf-8')
        import hashlib
        m = hashlib.md5()
        m.update(str)
        return m.hexdigest()

    def stringToBytes(self, s):
        ret = []
        for i in s:
            ret.append(ord(i))
        return ret

    def bytesToString(self, b):
        ret = ''
        for i in b:
            ret += chr(i)
        return ret

    def m115_getkey(self, length, key):
        if key is not None:
            results = []
            for i in range(length):
                results.append(((key[i] + self.g_kts[length * i]) & 0xff) ^ self.g_kts[length * (length - 1 - i)])
            return results
        if length == 12:
            return self.g_key_l
        return self.g_key_s

    def xor115_enc(self, src, srclen, key, keylen):
        mod4 = srclen % 4
        ret = []
        if mod4 != 0:
            for i in range(mod4):
                ret.append(src[i] ^ key[i % keylen])
        for i in range(mod4, srclen):
            ret.append(src[i] ^ key[(i - mod4) % keylen])
        return ret

    def m115_sym_encode(self, src, srclen, key1, key2):
        k1 = self.m115_getkey(4, key1)
        k2 = self.m115_getkey(12, key2)
        ret = self.xor115_enc(src, srclen, k1, 4)
        ret.reverse()
        ret = self.xor115_enc(ret, srclen, k2, 12)
        return ret

    def m115_sym_decode(self, src, srclen, key1, key2):
        k1 = self.m115_getkey(4, key1)
        k2 = self.m115_getkey(12, key2)
        ret = self.xor115_enc(src, srclen, k2, 12)
        ret.reverse()
        ret = self.xor115_enc(ret, srclen, k1, 4)
        return ret

    def m115_asym_encode(self, src, srclen):
        # ret = self.js.call('m115_asym_encrypt', src, srclen, self._prsa)
        # return base64.b64encode(ret.encode("latin1"))

        m = 128 - 11
        ret = b''
        for i in range(math.floor((srclen + m - 1) / m)):
            ret += base64.b64decode(self.prsa_.encrypt(src[i * m:min((i + 1) * m, srclen)]))
        return base64.b64encode(ret)


        # m = 128 - 11
        # ret = b''
        # for i in range(math.floor((srclen + m - 1) / m)):
        # #     # print(src[i * m:min((i + 1) * m, srclen)])
        # #     ret += base64.b64decode(self.prsa.encrypt(self.bytesToString(src[i * m:min((i + 1) * m, srclen)])).encode("utf8")).decode("latin1")
        # #     ret += base64.b64decode(self.prsa.encrypt(self.bytesToString(src[i * m:min((i + 1) * m, srclen)])).encode("utf8"))
        #     ret += base64.b64decode(self.prsa.encrypt(self.bytesToString(src[i * m:min((i + 1) * m, srclen)])).encode("utf8"))
        # #     ret += base64.b64decode(self.prsa_.encrypt(self.bytesToString(src[i * m:min((i + 1) * m, srclen)])).encode("utf8"))
        # #     # ret += base64.b64decode(self.js.call('getencrypt', self.bytesToString(src[i * m:min((i + 1) * m, srclen)]), self._prsa).encode("utf8")).decode("latin1")
        # return base64.b64encode(ret)


    def m115_asym_decode(self, src, srclen):
        # ret = self.js.call('m115_asym_decode', src, srclen, self._srsa)
        # return self.stringToBytes(ret)
        # ret = c_rsa.m115_asym_decode(src, srclen, self.srsa_)
        # return self.stringToBytes(ret)

        m = 128

        ret = []
        for i in range(math.floor((srclen + m - 1) / m)):
            ret.append(base64.b64encode(bytes(src[i * m:min((i + 1) * m, srclen)])))
            # ret += srsa.decrypt(base64.b64encode(bytes(src[i * m:min((i + 1) * m, srclen)])))
        return self.srsa_.decrypt__(ret)


        # ret = []
        # for i in range(math.floor((srclen + m - 1) / m)):
        #     z = self.srsa_.decrypt(base64.b64encode(bytes(src[i * m:min((i + 1) * m, srclen)])))
        #     print(len(z))
        #     ret += z
        # print(len(ret), '**----')
        # return ret



        # t = time.time()
        # m = 128
        # ret = ''
        # for i in range(math.floor((srclen + m - 1) / m)):
        #     # ret += self.srsa.decrypt(base64.b64encode(self.bytesToString(src[i * m:min((i + 1) * m, srclen)]).encode("latin1")).decode())
        # #     # print(self.bytesToString(src[i * m:min((i + 1) * m, srclen)]))
        #     ret += self.srsa.decrypt(base64.b64encode(bytes(src[i * m:min((i + 1) * m, srclen)])).decode())
        # #     ret += self.srsa_.decrypt(base64.b64encode(bytes(src[i * m:min((i + 1) * m, srclen)])).decode())
        # #     # ret += self.js.call('getdecrypt', base64.b64encode(self.bytesToString(src[i * m:min((i + 1) * m, srclen)]).encode("latin1")).decode(), self._srsa)
        # return self.stringToBytes(ret)

    def m115_encode(self, src, tm):
        key = self.stringToBytes(self.md5(f'!@###@#{tm}DFDR@#@#'))
        tmp = self.stringToBytes(src)
        tmp = self.m115_sym_encode(tmp, len(tmp), key, None)
        tmp = key[0:16] + tmp

        return self.m115_asym_encode(tmp, len(tmp)), key

    def m115_decode(self, src, key):
        tmp = self.stringToBytes(base64.b64decode(src.encode()).decode("latin1"))
        tmp = self.m115_asym_decode(tmp, len(tmp))
        return self.bytesToString(self.m115_sym_decode(tmp[16:], len(tmp) - 16, key, tmp[0:16]))

    async def CreateDownloadTask(self, pc):
        # start = time.time()
        tmus = int(time.time())
        tm = math.floor(tmus)
        data, key = self.m115_encode(f'{{"pickcode":"{pc}"}}', tm)
        data = quote(data, safe='...')
        data = f'data={data}'
        # _start = time.time() - start
        ret = await srequests.async_post(self.downurl.format(tm), data=data, headers=self.headers, timeout=5, retry=5)
        # start = time.time()
        try:
            if ret:
                # end = time.time()
                # print(_start + (end - start))
                return json.loads(self.m115_decode(ret.json()['data'], key))
            return False
        except:
            return False
            # raise
if __name__ == '__main__':
    d = Download115()

    z = [102, 99, 97, 102, 98, 49, 57, 97, 100, 56, 101, 102, 49, 48, 101, 57, 44, 60, 83, 162, 7, 202, 133, 118, 137, 67, 80, 207, 57, 100, 82, 226, 14, 198, 209, 62, 193, 8, 89, 222, 62, 125, 64, 242, 2, 194, 151, 103]
    # x = [45, 14, 119, 211, 176, 148, 203, 100, 159, 212, 254, 83, 44, 27, 60, 147, 243, 148, 220, 108, 134, 141, 240, 80, 57, 90, 101]
    # print(d.m115_asym_encode(z, len(z)))