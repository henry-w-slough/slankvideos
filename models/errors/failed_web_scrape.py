

class FailedWebScrape(Exception):

    def __init__(self, url: str, *args: object) -> None:
        """Exception raised when a web scrape fails for any reason."""
        super().__init__(f"Failed to web scrape '{url}'.", *args)

        