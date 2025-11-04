import asyncio
import os

from fastapi.logger import logger

from config import load_configs


async def watcher():
    ts = 0
    while True:
        new_ts = os.path.getmtime("apis.json")
        if new_ts != ts:
            await load_configs()
            logger.info("configs_reloaded")
            ts = new_ts
        await asyncio.sleep(5)