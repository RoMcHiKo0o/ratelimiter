import json
from typing import Literal, Annotated

from pydantic import BaseModel, AnyHttpUrl, PlainSerializer, AfterValidator

HTTP_METHODS_LITERAL = Literal["GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"]
HTTP_METHODS_LIST = list(HTTP_METHODS_LITERAL.__args__)


class RateLimitModel(BaseModel):
    interval: float = 0.001
    RPD: int = -1
    add_random: bool = False


def identifier_validator(v):
    if not isinstance(v,dict):
        raise ValueError('Identifier must be a dict')
    if "url" not in v:
        raise ValueError(f"{v} must have required 'url' key")
    AnyHttpUrl(v["url"])
    v['method'] = v.get("method", "ANY")
    if v.get("method") not in HTTP_METHODS_LIST + ["ANY"]:
        raise ValueError(f"Unprocessable method. Choose from {HTTP_METHODS_LIST}")
    v['extra'] = v.get("extra", "")
    if {"extra", "method", "url"} != set(sorted(v.keys())):
        print(v)
        raise ValueError(f"Identifier can have only ('extra', 'method', 'url') keys")
    try:
        return json.dumps(v, sort_keys=True, ensure_ascii=False)
    except Exception:
        raise ValueError(f"{v} can't be identifier, it is not JSON serializable")


IdentifierType = Annotated[dict, AfterValidator(identifier_validator)]


class APIModel(BaseModel):
    identifier: IdentifierType
    rate_limit: RateLimitModel


def url_serializer(val: AnyHttpUrl):
    return str(val)


class RequestModel(BaseModel):
    url: Annotated[AnyHttpUrl, PlainSerializer(url_serializer)]
    method: HTTP_METHODS_LITERAL
    headers: dict = {}
    params: dict = {}
    json: dict = {}


class RequestIdentifierModel(BaseModel):
    identifier: IdentifierType
    request: RequestModel
    priority: int = 0
