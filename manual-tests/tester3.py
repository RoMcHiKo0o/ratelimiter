import asyncio
import time

import aiohttp
from aiohttp import ClientTimeout

async def req(session: aiohttp.ClientSession,i):
    async with session.post('http://127.0.0.1:8000', json={
        'identifier': {
            'url': 'http://127.0.0.1:8889/limited2secs'
        },
        'request': {
            'url': 'http://127.0.0.1:8889/limited2secs',
            'method': 'GET',
            'json': {
                'msg': f'Hello world {i}'
            }
        }
    }) as resp:
        print(resp.status)
        print(await resp.json())

async def req2(session: aiohttp.ClientSession,i):
    async with session.post('http://127.0.0.1:8000', json={
        'identifier': {
            'url': 'http://127.0.0.1:8889/unlimited'
        },
        'request': {
            'url': 'http://127.0.0.1:8889/unlimited',
            'method': 'GET',
            'json': {
                'msg': f'Hello unlimited world {i}'
            }
        }
    }) as resp:
        print(resp.status)
        print(await resp.json())

async def req3(session: aiohttp.ClientSession,i):
    async with session.post('http://127.0.0.1:8000', json={
        'identifier': {
            'url': 'http://127.0.0.1:8889/limitedveryslow'
        },
        'request': {
            'url': 'http://127.0.0.1:8889/limitedveryslow',
            'method': 'GET',
            'json': {
                'msg': f'Hello very slow world {i}'
            }
        }
    }) as resp:
        print(resp.status)
        print(await resp.json())


async def req4(session: aiohttp.ClientSession,i):
    async with session.post('http://127.0.0.1:8000', json={
        'identifier': {
            'url': '123'
        },
        'request': {
            'url': 'http://127.0.0.1:8889/limitedveryslow',
            'method': 'GET',
            'json': {
                'msg': f'Hello very slow world {i}'
            }
        }
    }) as resp:
        print(resp.status)
        print(await resp.json())

async def spam():
    tasks = []
    async with aiohttp.ClientSession(timeout=ClientTimeout(123521343)) as session:
        # for i in range(5):
        #     tasks.append(asyncio.create_task(req(session, i)))
        # for i in range(5):
        #     tasks.append(asyncio.create_task(req2(session, i)))
        # for i in range(5):
        #     tasks.append(asyncio.create_task(req3(session, i)))
        for i in range(5):
            tasks.append(asyncio.create_task(req4(session, i)))
        await asyncio.gather(*tasks)

def run():
    return asyncio.run(spam())
start = time.time()
run()
print(time.time()-start)