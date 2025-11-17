import asyncio

import aiohttp


async def req():
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:8000/http://127.0.0.1:8000/add_api.com/asd?id=1&priority=5', json={
            'identifier': None,
            "rate_limit": {}
        }) as resp:
            print(resp.status)
            print(await resp.json())

asyncio.run(req())
