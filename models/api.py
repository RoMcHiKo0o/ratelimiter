import asyncio
from random import random

from schemas import APIModel
from services.requester import make_request

from logger import setup_logger

logger = setup_logger(__name__)


class API:
    def __init__(self, config: APIModel, stop_event: asyncio.Event):
        self.identifier = config.identifier
        self._interval = config.rate_limit.interval * 1.1
        self.counter = 0
        self.rpd = config.rate_limit.RPD
        self.queue = asyncio.PriorityQueue()
        self.stop_event = stop_event
        self.add_random = config.rate_limit.add_random

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
                item = await self.queue.get()
                pr, (fut, req) = item.priority, item.item
                logger.info(
                    f"Worker {self.identifier} found task with priority {pr}: {req.get('method')}, {req.get('url')}")
                task = asyncio.create_task(make_request(req))
                tasks[fut] = task
                await asyncio.sleep(self.interval)
            else:
                await asyncio.sleep(0)

        logger.info(f"Worker {self.identifier} завершён")
