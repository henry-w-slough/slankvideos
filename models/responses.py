from dataclasses import dataclass
from typing import Literal
import httpx


@dataclass
class SuccessResponse:
    url: str
    http_response: httpx.Response


@dataclass
class ErrorResponse:
    url: str
    error: Exception
    error_message: str


Response = SuccessResponse | ErrorResponse