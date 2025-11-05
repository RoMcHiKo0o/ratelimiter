import asyncio
import time

import aiohttp
import requests

# for i in range(4):
#     resp = requests.get('http://127.0.0.1:8889/limited2secs/slow',json={i:i})
#     print(resp)
#     print(resp.json())

async def req(session: aiohttp.ClientSession):
    async with session.get('http://127.0.0.1:8000') as resp:
        print(resp.status)
        print(await resp.json())
#

async def req2(session: aiohttp.ClientSession):
    async with session.get('http://127.0.0.1:8889/limited2secs/slow',json={}) as resp:
        print(resp.status)
        print(await resp.json())

async def spam():
    tasks = []

    async with aiohttp.ClientSession() as session:
        for _ in range(10):
            tasks.append(req(session))
        await asyncio.gather(*tasks)


# asyncio.run(spam())

async def spam_with_pause():
    async with aiohttp.ClientSession() as session:
        for _ in range(10):
            await req2(session)
            await asyncio.sleep(2.1)

asyncio.run(spam_with_pause())