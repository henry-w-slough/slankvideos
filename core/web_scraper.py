from playwright.async_api import Request as PlaywrightRequest, async_playwright
import asyncio

from ..models.m3u8_data import M3U8Data


class WebScraper:


    def __init__(self, headless: bool = True) -> None:

        self._headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.captured_m3u8s: list[M3U8Data] = []

        self.resolve_timeout: float = 30.0


    async def start(self) -> None:
        """Starts the web scraper by loading all necessary browser utilities. Chromium is used for the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self._headless)
        self.context = await self.browser.new_context()


    async def close(self) -> None:
        """Ends the web scraper by stopping all browser utilities safely."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


    async def resolve_m3u8_playlists(self, video_url: str) -> list[M3U8Data]:
        """Scrapes the given URL for m3u8 data. Returns a list of all found m3u8-related request info."""
        self.captured_m3u8s = []

        if self.context is None:
            raise RuntimeError("Browser context is null. Make sure to call WebScraper.start() before scraping.")

        #setting up page to listen for requests
        page = await self.context.new_page()
        page.on("request", self._capture_request)

        #setting up video scraping
        try:
            await page.goto(video_url, wait_until="domcontentloaded", timeout=int(self.resolve_timeout*1000))

            #waiting between getting m3u8s. Uses resolve_timeout while also breaking if a m3u8 is found
            deadline = asyncio.get_running_loop().time() + self.resolve_timeout
            while not self.captured_m3u8s:
                if asyncio.get_running_loop().time() >= deadline:
                    break
                await asyncio.sleep(0.2)

            if not self.captured_m3u8s:
                raise TimeoutError(f"No M3U8 requests were observed during scrape of '{video_url}'.")
            return self.captured_m3u8s
        finally:
            await page.close()


    def _capture_request(self, request: PlaywrightRequest) -> None:
        """The logic ran after an incoming request is caught during web scraping."""
        url = request.url.lower()
        if ".m3u8" in url:
            self.captured_m3u8s.append(
                M3U8Data(request.url, request.headers)
            )








