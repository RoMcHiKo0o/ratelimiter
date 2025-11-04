import yaml
import asyncio

class APIConfig:
    def init(self, name, url, rate_limit):
        self.name = name
        self.url = url
        self.rate_limit = rate_limit
        self.semaphore = asyncio.Semaphore(rate_limit)
        self.queue = asyncio.Queue()

configs = {}

async def load_configs():
    with open("apis.json") as f:
        data = yaml.safe_load(f)
    for name, conf in data["sources"].items():
        if name not in configs:
            configs[name] = APIConfig(name, conf["url"], conf["rate_limit"])
        else:
            api = configs[name]
            api.url = conf["url"]
            api.rate_limit = conf["rate_limit"]
            api.semaphore = asyncio.Semaphore(api.rate_limit)

