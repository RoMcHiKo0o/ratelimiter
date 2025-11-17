import asyncio

from pydantic import AnyHttpUrl

from schemas import HTTPMethod, IdentifierModel, RequestModel, RequestIdentifierModel

import aiohttp


async def req():
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:8000/http://127.0.0.1:8000/add_api.com/asd?id=1', headers={'n': "1"}, json={
            'identifier': None,
            "rate_limit": {}
        }) as resp:
            print(resp.status)
            print(await resp.json())

asyncio.run(req())
# a = RequestIdentifierModel(identifier=IdentifierModel(value=1),request=RequestModel(url="http://127.0.0.1:8000", method=HTTPMethod("GET"), params={}, headers={},
#                        json={}), priority=None)
# print(a)
