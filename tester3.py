import asyncio
import time
from threading import Thread

import aiohttp
import requests
from aiohttp import ClientTimeout


# for i in range(4):
#     resp = requests.get('http://127.0.0.1:8000',timeout=15)
#     print(resp)
#     print(resp.json())

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

async def spam():
    tasks = []
    # loop = asyncio.new_event_loop()
    async with aiohttp.ClientSession(timeout=ClientTimeout(123521343)) as session:
        for i in range(5):
            tasks.append(asyncio.create_task(req(session, i)))
            # await req(session, i)
        for i in range(5):
            tasks.append(asyncio.create_task(req2(session, i)))
            # await req(session, i)
        for i in range(5):
            tasks.append(asyncio.create_task(req3(session, i)))
            # await req(session, i)
        await asyncio.gather(*tasks)
        # loop.run_until_complete(asyncio.wait(tasks))
    # loop.cancel()

def run():
    return asyncio.run(spam())
start = time.time()
run()
print(time.time()-start)
# thread = Thread(target=run)
# thread.start()
# thread.join()