import aiohttp
from fastapi.responses import JSONResponse

from logger import setup_logger

logger = setup_logger(__name__)


async def make_request(req):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(**req) as resp:
                content = await resp.json()
                r = JSONResponse(status_code=resp.status, content=content, headers=resp.headers)
    except Exception as e:
        r = JSONResponse(content={"error": f"{type(e)} {str(e)}"})
    return r