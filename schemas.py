import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, field_validator, field_serializer, AnyHttpUrl, model_validator


class RateLimitModel(BaseModel):
    interval: float = 0.001
    RPD: int = -1
    add_random: bool = False


class IdentifierModel(BaseModel):
    value: Any

    @model_validator(mode="before")
    @classmethod
    def wrap_any_input(cls, data):
        return {"value": data}

    @field_validator("value", mode="after")
    def after_identifier_validator(cls, v):
        try:
            return json.dumps(v, sort_keys=True, ensure_ascii=False)
        except Exception:
            raise ValueError(f"{v} can't be identifier, it is not JSON serializable")


class APIModel(BaseModel):
    identifier: IdentifierModel
    rate_limit: RateLimitModel

    @field_serializer('identifier')
    def shortened_identifier(self, v):
        return v.value


class HTTPMethod(Enum):
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    CONNECT = "CONNECT"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    PATCH = "PATCH"


class RequestModel(BaseModel):
    url: AnyHttpUrl
    method: HTTPMethod
    headers: dict = {}
    params: dict = {}
    payload: dict = {}


class RequestIdentifierModel(BaseModel):
    identifier: IdentifierModel
    request: RequestModel
    priority: int = 0
