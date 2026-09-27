import m3u8

from ..models.m3u8_data import M3U8Data


class M3U8Handler:


    def __init__(self) -> None:
        pass


    def get_m3u8(self, content: str, base_uri: str) -> m3u8.M3U8:
        """Parses raw m3u8 content into a structured object."""
        return m3u8.loads(content, uri=base_uri)
