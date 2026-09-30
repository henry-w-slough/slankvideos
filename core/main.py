import asyncio
import slankvideos


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


async def display_logs() -> None:
    await asyncio.sleep(0.1)
    for log in slankvideos.logging.get_logs():
        print(f"---{log.severity.name} LOG ---")
        print(log.message)
        print(f"-------------------------------")

async def main() -> None:

    await downloader.start()

    await downloader.download(
        "https://cinejoy.pk/watch/movie/315635",
        "Movies/movie.ts"
    )

    await downloader.close()



async def run():
    try:
        await main()
    except Exception:
        pass
    finally:
        try:
            await display_logs()
        except:
            pass



if __name__ == "__main__":
    asyncio.run(run())



    