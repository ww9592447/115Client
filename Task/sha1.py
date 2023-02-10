from threading import Thread
from module import hashlib, sleep, setstate


class GetSha1:
    def __init__(self, state, lock):
        self.state = state
        self.lock = lock

    async def get(self, uuid):
        path = self.state[uuid]['path']
        getsha1 = ThreadGetSha1(path, self.state, uuid)
        getsha1.start()
        while getsha1.is_alive():
            await sleep(0.1)
        if self.state[uuid]['state']:
            with self.lock:
                with setstate(self.state, uuid) as state:
                    state.update({'stop': False})
        else:
            blockhash, sha1 = getsha1.get_result()
            with self.lock:
                with setstate(self.state, uuid) as state:
                    state.update({'blockhash': blockhash.upper(), 'sha1': sha1.upper(), 'stop': False})


class ThreadGetSha1(Thread):
    def __init__(self, path, state, uuid):
        Thread.__init__(self)
        self.path = path
        self.state = state
        self.uuid = uuid
        self.result = None

    def run(self):
        with open(self.path, 'rb') as f:
            sha = hashlib.sha1()
            sha.update(f.read(1024 * 128))
            blockhash = sha.hexdigest().upper()
            f.seek(0, 0)
            sha = hashlib.sha1()
            while True:
                data = f.read(1024 * 128)
                if self.state[self.uuid]['state']:
                    return
                if not data:
                    break
                sha.update(data)
            sha1 = sha.hexdigest().upper()
        self.result = (blockhash, sha1)

    def get_result(self):
        return self.result
