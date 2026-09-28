from dataclasses import dataclass
from enum import Enum, auto

import httpx


class Types(Enum):
    Error = auto()
    Success = auto()

    
@dataclass
class Response:
    """Response to an HTTP request. Can provide error information, or response information."""
    ok: bool
    url: str


@dataclass
class SuccessResponse(Response):
    http_response: httpx.Response | None = None


@dataclass
class ErrorResponse(Response):
    error: Exception | None = None
    error_message: str = ""
