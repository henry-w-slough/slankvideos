from dataclasses import dataclass
from typing import Literal

import httpx


@dataclass
class Response:
    """Response to an HTTP request. Can provide error information, or response information."""
    ok: bool
    url: str
    http_response: httpx.Response | None = None
    error: Exception | None = None
    error_message: str | None = None
