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
        
        if os.path.exists(src):
            raise ValueError(f"'{src}' already exists on disk.")

        playlists_data = await self.web_scraper.resolve_m3u8_playlists(video_url)

        # change this shit
        playlist_data = playlists_data[0]

        master_response: Response = await self.request_handler.send_request(
            playlist_data.url, "get", headers=playlist_data.headers
        )

        if master_response.error is not None:
            print(master_response.error_message)
            raise master_response.error

        if master_response.http_response is None:
            raise RuntimeError("Master playlist could not be accessed.")

        master_playlist = self.m3u8_handler.get_m3u8(master_response.http_response.text, master_response.url)

        if not master_playlist.playlists:
            raise RuntimeError("No variant playlists found in master.")

        variant = master_playlist.playlists[0]

        variant_response: Response = await self.request_handler.send_request(
            variant.absolute_uri, "get", headers=playlist_data.headers
        )

        if variant_response.error is not None:
            print(variant_response.error_message)
            raise variant_response.error

        if variant_response.http_response is None:
            raise RuntimeError("Variant playlist could not be accessed.")

        playlist = self.m3u8_handler.get_m3u8(variant_response.http_response.text, variant_response.url)

        urls = [
            Request(segment.absolute_uri, playlist_data.headers, "get")
            for segment in playlist.segments
        ]

        os.makedirs(os.path.dirname(src), exist_ok=True)
        self.data_handler.open_file(src)

        await self.request_handler.get_response_batch(urls, self.data_handler.write_response)

        self.data_handler.close_file()
            
        









    