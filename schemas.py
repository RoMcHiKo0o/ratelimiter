import json
from typing import Any, Literal, Annotated

from pydantic import BaseModel, AnyHttpUrl, Field, PlainSerializer, AfterValidator

HTTP_METHODS_LITERAL = Literal["GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"]
HTTP_METHODS_LIST = list(HTTP_METHODS_LITERAL.__args__)


class RateLimitModel(BaseModel):
    interval: float = 0.001
    RPD: int = -1
    add_random: bool = False


def identifier_validator(v):
    try:
        return json.dumps(v, sort_keys=True, ensure_ascii=False)
    except Exception:
        raise ValueError(f"{v} can't be identifier, it is not JSON serializable")


IdentifierType = Annotated[Any, AfterValidator(identifier_validator)]


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
    json_data: dict = Field(default={}, alias="json")


class RequestIdentifierModel(BaseModel):
    identifier: IdentifierType
    request: RequestModel
    priority: int = 0
