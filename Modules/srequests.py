import requests
import httpx

proxies = None
verify = True


def post(url, data=None, json=None, retry=2, **kwargs):
    stop = 0
    while 1:
        try:
            return requests.post(url, data=data, json=json, **kwargs)
        except:
            if stop == retry:
                return False
            stop += 1


def get(url, params=None, retry=2, **kwargs):
    stop = 0
    while 1:
        try:
            return requests.get(url, params=params, timeout=5, **kwargs)
        except:
            if stop == retry:
                return False
            stop += 1


async def async_post(url, data=None, json=None, retry=2, timeout=5, **kwargs):
    stop = 0
    while 1:
        try:
            async with httpx.AsyncClient(proxies=proxies, verify=verify, timeout=timeout) as client:
                return await client.post(url, data=data, json=json, **kwargs)
        except Exception as f:
            if stop == retry:
                return False
            stop += 1


async def async_get(url, params=None, retry=2, timeout=5, **kwargs):
    stop = 0
    while 1:
        try:
            async with httpx.AsyncClient(proxies=proxies, verify=verify, timeout=timeout) as client:
                return await client.get(url, params=params, **kwargs)
        except Exception as f:
            if stop == retry:
                return False
            stop += 1


async def async_put(url, data=None, retry=2, **kwargs):
    stop = 0
    while 1:
        try:
            async with httpx.AsyncClient(proxies=proxies, verify=verify) as client:
                return await client.put(url, data=data, **kwargs)
        except:
            if stop == retry:
                return False
            stop += 1


async def async_head(url, retry=2, **kwargs):
    stop = 0
    while 1:
        try:
            async with httpx.AsyncClient(proxies=proxies, verify=verify) as client:
                return await client.head(url, **kwargs)
        except:
            if stop == retry:
                return False
            stop += 1