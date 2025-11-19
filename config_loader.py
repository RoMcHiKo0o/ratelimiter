import json

from models.api_manager import api_manager


def load_configs(stop_event):
    with open("apis.json", "r", encoding="utf8") as f:
        data = json.load(f)
    api_manager.init(data["sources"], stop_event)
    api_manager.start()