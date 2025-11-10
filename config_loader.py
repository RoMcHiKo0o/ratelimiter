import json

from models.api_manager import APIManager

def load_configs(stop_event):
    with open("apis.json", "r", encoding="utf8") as f:
        data = json.load(f)
    APIManager.init(data["sources"], stop_event)
    APIManager.start()