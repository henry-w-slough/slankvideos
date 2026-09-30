from .core.request_handler import RequestHandler
from .core.web_scraper import WebScraper
from .core.m3u8_handler import M3U8Handler
from .core.data_handler import DataHandler
from .models.request import Request
from .models.responses import Response, ErrorResponse, SuccessResponse
from .models.m3u8_data import M3U8Data
from .logging import logging

import m3u8
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
        
        all_scraped_masters = await self.web_scraper.resolve_m3u8_playlists(
            video_url
        )
        master_info = self.m3u8_handler.get_best_variant(all_scraped_masters)

        master_info_response = await self.request_handler.send_request(
            Request(
                master_info.url,
                "get",
                master_info.headers
            )
        )

        if isinstance(master_info_response, ErrorResponse):
            raise master_info_response.error

        master = self.m3u8_handler.get_m3u8(master_info_response.http_response.text, master_info.url)


        variant: m3u8.M3U8
        variant_info: M3U8Data

        #if the master is already at segment-parsing level
        if not master.is_variant:
            variant = master
            variant_info = master_info

        #if there is streams to parse to find
        else:

            all_playlist_info = []
            all_playlist_info.extend(
                M3U8Data(
                    playlist.absolute_uri,
                    master_info.headers
                ) 
                for playlist in master.playlists if playlist.absolute_uri is not None
            )

            variant_info = self.m3u8_handler.get_best_variant(all_playlist_info)

            playlist_response = await self.request_handler.send_request(
                Request(
                    variant_info.url,
                    "get",
                    variant_info.headers
                )
            )

            if isinstance(playlist_response, ErrorResponse):
                raise playlist_response.error

            variant = self.m3u8_handler.get_m3u8(playlist_response.http_response.text, variant_info.url)


        segment_requests = []

        init_segment_url = self.m3u8_handler.get_init_segment_url(variant)
        if init_segment_url:
            segment_requests.append(
                Request(
                    init_segment_url,
                    "get",
                    variant_info.headers
                )
            )

        segment_requests.extend(
            Request(
                seg.absolute_uri,
                "get",
                variant_info.headers
            ) for seg in variant.segments if seg.absolute_uri is not None
        )



        temp_src = f"temp_{src}"
        os.makedirs(os.path.dirname(temp_src), exist_ok=True)

        self.data_handler.open_file(temp_src)

        await self.request_handler.request_batch(
            segment_requests,
            self.data_handler.write_response,
        )

        self.data_handler.close_file()

        os.makedirs(src, exist_ok=True)

        await self.data_handler.transcode_file(temp_src, src)
        



        
















    