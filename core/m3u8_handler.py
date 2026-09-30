import m3u8
import re

from ..models.m3u8_data import M3U8Data


class M3U8Handler:


    def __init__(self) -> None:
        pass


    def get_m3u8(self, content: str, base_uri: str) -> m3u8.M3U8:
        """Parses raw m3u8 content into a structured object."""
        return m3u8.loads(content, uri=base_uri)


    def get_best_variant(self, candidates: list[M3U8Data]) -> M3U8Data:
        """Guesses quality from the URL (e.g. '720p', '1080p') and returns the highest match.
        Falls back to the first candidate if no quality marker is found in any URL."""
        if not candidates:
            raise ValueError("No candidate M3U8Data entries provided.")

        def quality_score(data: M3U8Data) -> int:
            match = re.search(r"(\d{3,4})p", data.url.lower())
            return int(match.group(1)) if match else 0

        return max(candidates, key=quality_score)


    def get_init_segment_url(self, variant: m3u8.M3U8) -> str | None:
        """Returns te first initialization segment of the variant if available."""
        if not variant.segment_map:
            return None
        return variant.segment_map[0].absolute_uri

    
