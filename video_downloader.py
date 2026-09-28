from .core.request_handler import RequestHandler
from .core.web_scraper import WebScraper
from .core.m3u8_handler import M3U8Handler
from .core.data_handler import DataHandler
from .models.request import Request

import m3u8
import os

from .models.responses import Response


class VideoDownloader:


    def __init__(self, request_handler: RequestHandler, web_scraper: WebScraper, m3u8_handler: M3U8Handler, data_handler: DataHandler) -> None:

        self.request_handler = request_handler
        self.web_scraper = web_scraper
        self.m3u8_handler = m3u8_handler
        self.data_handler = data_handler


    async def start(self) -> None:
        """Initializes all handlers used by the downloader."""
        await self.web_scraper.start()


    async def close(self) -> None:
        """Deintializes all handlers used by the downloader."""
        await self.web_scraper.close()


    async def download(self, video_url: str, src: str) -> None:

        all_playlists = await self.web_scraper.resolve_m3u8_playlists(
            video_url
        )

        playlist_info = self.m3u8_handler.get_best_variant(all_playlists)

        playlist_response = await self.request_handler.send_request(
            Request(
                playlist_info.url,
                "get",
                playlist_info.headers
            )
        )

        if playlist_response.error is not None:
               raise playlist_response.error
        
        if playlist_response.http_response is None:
             raise RuntimeError("HTTP response for playlist was None.")


        playlist = self.m3u8_handler.get_m3u8(
            playlist_response.http_response.text,
            playlist_info.url
        )

        segment_requests = [
            Request(
                seg.absolute_uri, "get", {
                    "accept": "*/*",
                    "accept-encoding": "gzip, deflate, br, zstd",
                    "accept-language": "en-US,en;q=0.9",
                    "connection": "keep-alive",
                    "origin": "https://cinejoy.pk",
                    "referer": "https://cinejoy.pk/",
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "cross-site",
                    "sec-gpc": "1",
                    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:156.0) Gecko/20100101 Firefox/156.0",
                }
            ) for seg in playlist.segments
        ]

        os.makedirs(os.path.dirname(src), exist_ok=True)

        self.data_handler.open_file(src)

        await self.request_handler.request_batch(
            segment_requests,
            self.data_handler.write_response
        )

        self.data_handler.close_file()
















    