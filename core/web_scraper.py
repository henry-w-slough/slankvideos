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

        self.initialization_scripts = [
            # 1. webdriver flag
            """
            Object.defineProperty(Navigator.prototype, 'webdriver', {
                get: () => false, configurable: true,
            });
            """,

            # 2. window.chrome object
            """
            if (!window.chrome) {
                window.chrome = { runtime: {}, app: {}, csi: () => ({}), loadTimes: () => ({}) };
            }
            """,

            # 3. languages / hardware hints
            """
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en'], configurable: true});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8, configurable: true});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8, configurable: true});
            """,

            # 4. WebGL vendor/renderer
            """
            const patch = (ctx) => {
                if (!ctx || ctx.__patched) return ctx;
                const info = ctx.getExtension('WEBGL_debug_renderer_info');
                if (info) {
                    const orig = ctx.getParameter.bind(ctx);
                    ctx.getParameter = (p) =>
                        p === info.UNMASKED_VENDOR_WEBGL ? 'Apple' :
                        p === info.UNMASKED_RENDERER_WEBGL ? 'Apple M2' : orig(p);
                }
                ctx.__patched = true;
                return ctx;
            };
            const orig = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, ...args) {
                const ctx = orig.call(this, type, ...args);
                return ['webgl', 'experimental-webgl', 'webgl2'].includes(type) ? patch(ctx) : ctx;
            };
            """,

            # 5. permissions query
            """
            if (window.Notification && navigator.permissions) {
                const q = navigator.permissions.query.bind(navigator.permissions);
                navigator.permissions.query = (p) =>
                    p.name === 'notifications' ? Promise.resolve({state: 'prompt'}) : q(p);
            }
            """,
        ]

        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
        )

        self.context_options = {
            "user_agent": self.user_agent,
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "extra_http_headers": {
                "Accept-Language": "en-US,en;q=0.9",
                "Sec-CH-UA": '"Chromium";v="151", "Not_A Brand";v="24", "Google Chrome";v="151"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"macOS"',
            },
        }

        self.launch_arguments = [
            "--headless=new",
            "--disable-blink-features=AutomationControlled",
        ]


    async def start(self) -> None:
        """Starts the web scraper by loading all necessary browser utilities. Chromium is used for the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self._headless, args=self.launch_arguments)
        self.context = await self.browser.new_context(**self.context_options)
        for script in self.initialization_scripts:
            await self.context.add_init_script(script)


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

        try:
            await page.goto(video_url, wait_until="domcontentloaded", timeout=int(self.resolve_timeout * 1000))

            # try to trigger playback on the native video element directly
            try:
                await page.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        if (video) {
                            video.muted = true;
                            video.play().catch(() => {});
                        }
                    }
                """)
            except Exception:
                pass

            #waiting between getting m3u8s. Uses resolve_timeout while also breaking if a m3u8 is found
            deadline = asyncio.get_running_loop().time() + self.resolve_timeout
            while not self.captured_m3u8s:
                if asyncio.get_running_loop().time() >= deadline:
                    break
                await asyncio.sleep(2.0)

            if not self.captured_m3u8s:
                raise RuntimeError(f"No M3U8 URLs were observed while scraping {video_url}.")

            return self.captured_m3u8s
        
        finally:
            await page.close()


    async def _capture_request(self, request: PlaywrightRequest) -> None:
        """The logic ran after an incoming request is caught during web scraping."""
        
        url = request.url.lower()

        if not ".m3u8" in url:
            return
        
        try:
            headers = await request.all_headers()
        except Exception:
            return
        
        headers = {k: v for k, v in headers.items() if not k.startswith(":")}

        cookie_header = headers.pop("cookie", None)
        cookies = None
        if cookie_header:
            cookies = dict(
                pair.strip().split("=", 1)
                for pair in cookie_header.split(";")
                if "=" in pair
            )
        self.captured_m3u8s.append(M3U8Data(request.url, headers, cookies))








