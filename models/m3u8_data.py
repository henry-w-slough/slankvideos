from dataclasses import dataclass


@dataclass
class M3U8Data:
    """The information that comes when resolving an M3U8 link."""
    url: str
    headers: dict[str, str]