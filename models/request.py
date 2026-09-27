from dataclasses import dataclass


@dataclass
class Request:

    url: str
    headers: dict[str, str]
    method: str