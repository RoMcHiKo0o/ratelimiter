import asyncio
import logging
import time
import uvicorn
from fastapi import FastAPI

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi.requests import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def exc_handler(request: Request, exc: RateLimitExceeded):
    print(f"BAD {time.time()}")
    return JSONResponse(status_code=429, content={"msg": "Too Many Requests"})


@app.get("/unlimited")
async def hello_unlimited(request: Request):
    await asyncio.sleep(7)
    return JSONResponse(status_code=200, content=dict(request.query_params.items()))


@app.post("/limitedveryslow")
@limiter.limit("6/minute")
async def hello_limited(request: Request):
    await asyncio.sleep(2.5)
    return JSONResponse(status_code=200, content=await request.json())


@app.get("/limited2secs")
@limiter.limit("2 per second")
async def hello(request: Request):
    print(time.time())
    await asyncio.sleep(0.1)

    return JSONResponse(status_code=200, content=dict(request.query_params.items()))


if __name__ == "__main__":
    uvicorn.run(app, reload=True, port=8889)
