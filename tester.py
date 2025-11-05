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
            'url': 'http://127.0.0.1:8889/limited2secs/slow',
            'method': 'GET',
            'json': {
                'msg': f'Hello world {i}'
            }
        }
    }) as resp:
        print(resp.status)
        print(await resp.json())

async def spam():
    tasks = []
    # loop = asyncio.new_event_loop()
    async with aiohttp.ClientSession(timeout=ClientTimeout(123521343)) as session:
        for i in range(7):
            tasks.append(req(session, i))
            # await req(session, i)
        await asyncio.gather(*tasks)
        # loop.run_until_complete(asyncio.wait(tasks))
    # loop.cancel()

def run():
    return asyncio.run(spam())

run()
# thread = Thread(target=run)
# thread.start()
# thread.join()