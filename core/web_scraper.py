import asyncio
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Request as PlaywrightRequest,
    async_playwright,
)

from ..models.m3u8_data import M3U8Data


class WebScraper:
    """
    Playwright-based scraper for discovering HLS (.m3u8) requests.

    The browser configuration intentionally stays close to a normal
    Playwright Chromium environment instead of manually spoofing a large
    collection of browser fingerprint properties.
    """

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

        self.captured_m3u8s: list[M3U8Data] = []

        self.resolve_timeout: float = 30.0

        # Keep browser identity internally consistent.
        #
        # Avoid manually overriding navigator.webdriver, WebGL,
        # permissions, navigator properties, etc. Those overrides can
        # themselves create detectable inconsistencies.
        self.context_options = {
            "viewport": {
                "width": 1920,
                "height": 1080,
            },
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "extra_http_headers": {
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        self.launch_arguments = [
        ]


    async def start(self) -> None:
        """Start Playwright, Chromium, and the browser context."""

        if self.browser is not None:
            return

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=self._headless,
            args=self.launch_arguments,
        )

        self.context = await self.browser.new_context(
            **self.context_options,
        )


    async def close(self) -> None:
        """Safely shut down the browser and Playwright."""

        #stopping and resetting context
        if self.context is not None:
            try:
                await self.context.close()
            except Exception:
                pass
            finally:
                self.context = None

        #stopping and resetting browser
        if self.browser is not None:
            try:
                await self.browser.close()
            except Exception:
                pass
            finally:
                self.browser = None

        #stopping and resetting playwright ref
        if self.playwright is not None:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            finally:
                self.playwright = None


    async def resolve_m3u8_playlists(self, video_url: str) -> list[M3U8Data]:
        """
        Load a page and return M3U8 requests observed while the page
        initializes and attempts playback.
        """

        if self.context is None:
            raise RuntimeError("Browser context is null. Call WebScraper.start() before scraping.")

        self.captured_m3u8s = []

        page = await self.context.new_page()

        # Register request interception BEFORE navigation.
        page.on("request", self._capture_request)

        try:
            await page.goto(
                video_url,
                wait_until="domcontentloaded",
            )

            # Give the page a chance to finish initializing its player.
            await self._wait_for_video_elements(page)

            # Attempt playback on all currently available video elements.
            await self._attempt_video_playback(page)

            # Some players initialize asynchronously after the first pass.
            # Continue watching for requests until timeout or success.
            deadline = asyncio.get_running_loop().time() + self.resolve_timeout

            #main running catch loop
            while (not self.captured_m3u8s and asyncio.get_running_loop().time() < deadline):
                # Re-attempt playback periodically because some players
                # create their <video> element after page load.
                await self._attempt_video_playback(page)

                remaining = deadline - asyncio.get_running_loop().time()

                if remaining <= 0:
                    break

                await asyncio.sleep(min(1.0, remaining))

            if not self.captured_m3u8s:
                raise RuntimeError(f"No M3U8 URLs were observed while scraping {video_url}.")

            return self.captured_m3u8s

        finally:
            await page.close()


    async def _wait_for_video_elements(self, page: Page) -> None:
        """Wait briefly for a native video element to appear."""

        try:
            await page.wait_for_selector(
                "video",
                timeout=5000,
                state="attached",
            )
        except Exception:
            pass


    async def _attempt_video_playback(self, page: Page) -> None:
        """
        Attempt muted playback on all native video elements.

        This is deliberately best-effort. Autoplay, DRM, custom players,
        and cross-origin frames may prevent playback.
        """

        try:
            await page.evaluate(
                """
                () => {
                    const videos = Array.from(
                        document.querySelectorAll("video")
                    );

                    for (const video of videos) {
                        try {
                            video.muted = true;
                            video.volume = 0;

                            const result = video.play();

                            if (result && typeof result.catch === "function") {
                                result.catch(() => {});
                            }
                        } catch (_) {
                            // Playback is best-effort.
                        }
                    }
                }
                """
            )
        except Exception:
            pass


    async def _capture_request(self, request: PlaywrightRequest) -> None:
        """Capture requests whose URL identifies an HLS playlist."""

        url = request.url

        # Case-insensitive detection without modifying the original URL.
        if ".m3u8" not in url.lower():
            return

        try:
            headers = await request.all_headers()
        except Exception:
            return

        # Playwright normally exposes useful request headers without
        # needing pseudo-header fields such as :authority.
        headers = {
            key: value
            for key, value in headers.items()
            if not key.startswith(":")
        }

        if self.context is None:
            raise RuntimeError

        m3u8_data = M3U8Data(
            url,
            headers
        )

        # Avoid duplicates when the player repeatedly requests the same
        # playlist.
        if not any(existing.url == m3u8_data.url for existing in self.captured_m3u8s):
            self.captured_m3u8s.append(m3u8_data)







