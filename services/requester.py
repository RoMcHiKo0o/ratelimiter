import aiohttp
import time
from datetime import datetime
from fastapi.responses import JSONResponse

from logger import setup_logger

logger = setup_logger(__name__)


async def make_request(req):
    logger.info(f"Request {req}")
    try:
        logger.info(f"{datetime.fromtimestamp(time.time())} session open by {req['json']['msg']}")
        async with aiohttp.ClientSession() as session:
            async with session.request(**req) as resp:
                content = await resp.json()
                r = JSONResponse(status_code=resp.status, content=content, headers=resp.headers)
                logger.info(f"Response done for {req['json']['msg']}")
    except Exception as e:
        r = JSONResponse(content={"error": f"{type(e)} {str(e)}"})
    return r