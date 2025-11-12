import asyncio
from random import random
from services.requester import make_request

from logger import setup_logger

logger = setup_logger(__name__)

API_registry: dict[str, "API"] = {}


class API:
    def __init__(self, config: dict, stop_event: asyncio.Event):
        self.identifier = config["identifier"]
        self._interval = config.get("rate_limit", {}).get("interval", 0.001) * 1.01
        self.counter = 0
        self.rpd = config.get("rate_limit", {}).get("RPD", -1)
        self.queue = asyncio.Queue()
        self.stop_event = stop_event
        self.add_random = config.get('add_random', False)

    @property
    def interval(self):
        return self._interval + (random() if self.add_random else 0)

    async def worker(self):
        logger.info(f"Worker created for {self.identifier}")
        tasks = {}

        while not self.stop_event.is_set():
            for fut, task in list(tasks.items()):
                if task.done():
                    tasks.pop(fut)
                    fut.set_result(await task)
                    self.queue.task_done()

            if not self.queue.empty():
                fut, req = await self.queue.get()
                logger.info(f"Worker found task {req}")
                task = asyncio.create_task(make_request(req))
                tasks[fut] = task
                await asyncio.sleep(self.interval)
            else:
                await asyncio.sleep(0)

        logger.info(f"Worker {self.identifier} завершён")
