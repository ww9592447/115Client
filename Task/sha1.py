from threading import Thread
from module import hashlib, sleep, getsize, set_state


class GetSha1:
    def __init__(self, state, lock):
        self.state = state
        self.lock = lock

    async def get(self, uuid):
        path = self.state[uuid]['path']
        getsha1 = ThreadGetSha1(path)
        getsha1.start()
        while getsha1.is_alive():
            await sleep(0.1)
        blockhash, sha1 = getsha1.get_result()
        length = getsize(path)
        with self.lock:
            with set_state(self.state, uuid) as state:
                state.update({'blockhash': blockhash.upper(), 'sha1': sha1.upper(), 'length': length})


class ThreadGetSha1(Thread):
    def __init__(self, path):
        Thread.__init__(self)
        self.path = path
        self.result = None

    def run(self):
        with open(self.path, 'rb') as f:
            sha = hashlib.sha1()
            sha.update(f.read(1024 * 128))
            blockhash = sha.hexdigest()
            f.seek(0, 0)
            sha = hashlib.sha1()
            sha.update(f.read())
            sha1 = sha.hexdigest()
        self.result = (blockhash, sha1)

    def get_result(self):
        return self.result
