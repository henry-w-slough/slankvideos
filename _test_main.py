import asyncio
import datetime
import gzip
import io
import json
from dataclasses import dataclass
import os
import re

import slankvideos


request_handler = slankvideos.RequestHandler(200, 150, 60.0)
data_handler = slankvideos.DataHandler()
m3u8_handler = slankvideos.M3U8Handler()
web_scraper = slankvideos.WebScraper(headless=True)

downloader = slankvideos.VideoDownloader(
    request_handler,
    web_scraper,
    m3u8_handler,
    data_handler,
)


@dataclass
class Movie:
    name: str
    id: str
    rating: float


async def get_movie_entries(rating_floor: float = 40.0) -> list[Movie]:
    movies: list[Movie] = []

    date = datetime.datetime.now().strftime("%m_%d_%Y")
    url_to_send = f"https://files.tmdb.org/p/exports/movie_ids_{date}.json.gz"

    movie_db_response = await request_handler.send_request(
        slankvideos.Request(
            url_to_send,
            "get",
            headers={},
        )
    )

    if isinstance(movie_db_response, slankvideos.ErrorResponse):
        raise movie_db_response.error

    with gzip.GzipFile(
        fileobj=io.BytesIO(movie_db_response.http_response.content)
    ) as gz:
        movie_db_content = gz.read().decode("utf-8")

    for line in movie_db_content.splitlines():
        if not line.strip():
            # Skip empty lines
            continue

        entry = json.loads(line)

        if entry["popularity"] < rating_floor:
            continue

        movies.append(
            Movie(
                name=entry["original_title"],
                id=entry["id"],
                rating=entry["popularity"],
            )
        )

    return movies


async def display_log() -> None:
    while True:
        await asyncio.sleep(1)

        for log in slankvideos.logging.get_logs():
            print(f"{log.severity.name} LOG ---")
            print(log.message)
            print("------")

        slankvideos.logging.clear_log()


def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9 ]', "_", name)


async def main() -> None:
    await downloader.start()

    for movie in await get_movie_entries(20):

        src = f"Movies/{sanitize_filename(movie.name)}" 

        slankvideos.logging.log(
            f"Attemping to download {movie.name} (id: {movie.id}) to {src}",
            slankvideos.logging.Severity.INFO,
        )

        if os.path.exists(f"{src}{data_handler.default_format.extension}"):
            slankvideos.logging.log(
                f"Movie source path {src} already exists. Continuing.",
                slankvideos.logging.Severity.WARNING,
            )
            continue
        
        try:
            await downloader.download(
                f"https://cinejoy.pk/watch/movie/{movie.id}",
                src,
            )
        except Exception as e:
            slankvideos.logging.log(
                f"Download of {movie.name} (id: {movie.id}) failed. "
                f"Exception type: {type(e).__name__}",
                slankvideos.logging.Severity.ERROR,
            )
            continue

        slankvideos.logging.log(
            f"Successfully downloaded {movie.name} (id: {movie.id}) to {src}",
            slankvideos.logging.Severity.INFO,
        )

    await downloader.close()


async def run() -> None:
    display_task = asyncio.create_task(display_log())

    try:
        await main()
    finally:
        display_task.cancel()

        try:
            await display_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(run())
