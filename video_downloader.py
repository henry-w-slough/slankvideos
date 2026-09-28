from .core.request_handler import RequestHandler
from .core.web_scraper import WebScraper
from .core.m3u8_handler import M3U8Handler
from .core.data_handler import DataHandler
from .models.request import Request
from . import logging

import os


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
        
        scraped_master_info = await self.web_scraper.resolve_m3u8_playlists(
            video_url
        )

        master_info = self.m3u8_handler.get_best_variant(scraped_master_info)

        master_response = await self.request_handler.send_request(
            Request(
                master_info.url,
                "get",
                master_info.headers
            )
        )

        
















    