from dataclasses import dataclass


@dataclass
class Request:
    
    url: str
    method: str
    headers: dict[str, str] | None = None
    cookies: dict[str, str] | None = None