import asyncio
import time
from random import random

import aiohttp
from aiohttp import ClientTimeout


# RATELIMITER_URL = "http://127.0.0.1:8000/"
RATELIMITER_URL = ""
async def req(session: aiohttp.ClientSession, i):
    if random() > 0.5:
        async with session.get(f'{RATELIMITER_URL}http://127.0.0.1:8889/limited2secs',
                                headers={"priority": str(1000 * random())}, params={
                    'msg': f'Hello world {i}'
                }) as resp:
            print(resp.status)
            print(await resp.json())
    else:
        async with session.get(f'{RATELIMITER_URL}http://127.0.0.1:8889/limited2secs', params={
            'msg': f'Hello world {i}'
        }) as resp:
            print(resp.status)
            print(await resp.json())


async def req2(session: aiohttp.ClientSession, i):
    if random() > 0.5:
        async with session.get(f'{RATELIMITER_URL}http://127.0.0.1:8889/unlimited',
                                headers={"priority": str(1000 * random())}, params={
                    'msg': f'Hello unlimited world {i}'
                }) as resp:
            print(resp.status)
            print(await resp.json())
    else:
        async with session.get(f'{RATELIMITER_URL}http://127.0.0.1:8889/unlimited', params={
            'msg': f'Hello unlimited world {i}'
        }) as resp:
            print(resp.status)
            print(await resp.json())


async def req3(session: aiohttp.ClientSession, i):
    if random() > 0.5:
        async with session.get(f'{RATELIMITER_URL}http://127.0.0.1:8889/limited2secs',
                                headers={"priority": str(1000 * random())}, json={
                    'msg': f'Hello world {i}'
                }) as resp:
            print(resp.status)
            print(await resp.json())
    else:
        async with session.get(f'{RATELIMITER_URL}http://127.0.0.1:8889/limited2secs', json={
            'msg': f'Hello world {i}'
        }) as resp:
            print(resp.status)
            print(await resp.json())


async def req4(session: aiohttp.ClientSession, i):
    if random() > 0.5:
        async with session.post(f'{RATELIMITER_URL}http://127.0.0.1:8889/limitedveryslow', headers={"priority": str(1000*random())}, json={
            'msg': f'Hello very slow world {i}'
        }) as resp:
            print(resp.status)
            print(await resp.json())
    else:
        async with session.post(f'{RATELIMITER_URL}http://127.0.0.1:8889/limitedveryslow', json={
            'msg': f'Hello very slow world {i}'
        }) as resp:
            print(resp.status)
            print(await resp.json())


async def spam():
    tasks = []
    async with aiohttp.ClientSession(timeout=ClientTimeout(123521343)) as session:
        for i in range(5):
            tasks.append(asyncio.create_task(req(session, i)))
        for i in range(5):
            tasks.append(asyncio.create_task(req2(session, i)))
        # for i in range(5):
        #     tasks.append(asyncio.create_task(req3(session, i)))
        for i in range(5):
            tasks.append(asyncio.create_task(req4(session, i)))
        await asyncio.gather(*tasks)


def run():
    return asyncio.run(spam())


start = time.time()
run()
print(time.time() - start)
