import asyncio
import logging
import time

import uvicorn
from fastapi import FastAPI

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi.requests import Request

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)
app = FastAPI()
app.state.limiter = limiter


# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(RateLimitExceeded)
async def exc_handler(request: Request, exc: RateLimitExceeded):
    print(f"BAD {time.time()}")
    return JSONResponse(status_code=429, content={"msg": "Too Many Requests"})


@app.get("/limited2secs")
@limiter.limit("2/second")
async def hello(request: Request):
    # await asyncio.sleep(2.5)
    return JSONResponse(status_code=200, content=await request.json())

@app.get("/limited2secs/slow")
@limiter.limit("2/second")
async def hello(request: Request):
    print(time.time())
    await asyncio.sleep(10)
    print(await request.json())

    return JSONResponse(status_code=200, content=await request.json())


if __name__ == "__main__":
    uvicorn.run(app, reload=True, port=8889)
