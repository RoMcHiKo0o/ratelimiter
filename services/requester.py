import aiohttp
from fastapi.responses import JSONResponse

from logger import setup_logger

logger = setup_logger(__name__)


async def make_request(req):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(**req) as resp:
                content = await resp.json()
                filtered_headers = {
                    k: v
                    for k, v in resp.headers.items()
                    if k.lower() not in {"content-length", "content-encoding", "transfer-encoding"}
                }
                r = JSONResponse(status_code=resp.status, content=content, headers=filtered_headers)
    except Exception as e:
        r = JSONResponse(content={"error": f"{type(e)} {str(e)}"})
    return r