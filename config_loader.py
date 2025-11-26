import json

from models.api_manager import APIManager


def load_configs():
    with open("apis.json", "r", encoding="utf8") as f:
        data = json.load(f)
    api_manager = APIManager(data["sources"])
    api_manager.start()
    return api_manager