import asyncio
import slankvideos

import datetime
import gzip
import json
import io
from pydantic import BaseModel


request_handler = slankvideos.RequestHandler()
web_scraper = slankvideos.WebScraper()
m3u8_handler = slankvideos.M3U8Handler()
data_handler = slankvideos.DataHandler()


#injecting dependencies
downloader = slankvideos.VideoDownloader(
    request_handler,
    web_scraper,
    m3u8_handler,
    data_handler
)


class Movie(BaseModel):
    name: str
    id: int


async def get_movie_entries(adult: bool = False, rating_floor: float = 40.0) -> list[ Movie]:

    movies: list[Movie] = []

    date = datetime.datetime.now().strftime("%m_%d_%Y")

    url_to_send = f"https://files.tmdb.org/p/exports/movie_ids_{date}.json.gz" if not adult else f"https://files.tmdb.org/p/exports/adult_movie_ids_{date}.json.gz"
    movie_db_response = await request_handler.send_request(
        slankvideos.Request(
            url_to_send,
            "get",
            headers = {}
        )
    )

    if isinstance(movie_db_response, slankvideos.ErrorResponse):
        raise movie_db_response.error

    with gzip.GzipFile(fileobj=io.BytesIO(movie_db_response.http_response.content)) as gz:
        movie_db_content = gz.read().decode('utf-8')

    for line in movie_db_content.splitlines():

        if not line.strip():  # Skip empty lines
            continue

        entry = json.loads(line)

        if entry["popularity"] < rating_floor:
            continue

        movies.append(
            Movie(
                name = entry["original_title"],
                id = entry["id"]
            )
        )

    return movies


async def display_logs() -> None:
    while True:
        await asyncio.sleep(0.5)
        for log in slankvideos.logging.get_logs():
            if log.severity == slankvideos.logging.Severity.INFO:
                continue

            print(f"{log.severity.name} LOG")
            print(log.message)
            print("--------")

        slankvideos.logging.clear_log()


async def main() -> None:

    await downloader.start()

    movies = await get_movie_entries(rating_floor = 80)

    for movie in movies:
        print(f"ATTEMPTING DONWLOAD FOR {movie.name} (id: {movie.id})")
        try:
            await downloader.download(
                f"https://cinejoy.pk/watch/movie/{movie.id}",
                f"Movies/{movie.name}"
            )
        except Exception as e:
            print(f"DOWNLOAD FOR {movie.name} FAILED ({type(e).__name__})")

    await downloader.close()



async def run():
    display_task = asyncio.create_task(display_logs())
    try:
        await main()
    except Exception as e:
        print(f"main() failed: {type(e).__name__}: {e}")
    finally:
        display_task.cancel()
        try:
            await display_task
        except asyncio.CancelledError:
            pass



if __name__ == "__main__":
    asyncio.run(run())



    