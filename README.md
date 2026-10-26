# slankvideos

`slankvideos` is a Python library for discovering HLS (`.m3u8`) streams in web pages, downloading media segments concurrently, and transcoding the result to a video file. It works great for self-hosted websites or data storage that need quick public accessibility.

## Features

- Discovers HLS playlist requests with Playwright and Chromium
- Captures playlist request headers and cookies
- Parses HLS master and media playlists
- Selects high-resolution variants and media initialization segments
- Downloads segments concurrently through `httpx`
- Transcodes output with FFmpeg and validates completed files with FFprobe
- Supports MP4, MKV, AVI, FLV, and MPEG transport stream output

## Requirements

- Python 3.10 or newer
- FFmpeg and FFprobe available on `PATH`
- Playwright Chromium browser

Python packages used by the library include:

- `httpx`
- `m3u8`
- `playwright`

Install the Python dependencies in your environment, then install the Chromium browser:

```bash
python -m pip install httpx m3u8 playwright
python -m playwright install chromium
```

Verify FFmpeg is installed:

```bash
ffmpeg -version
ffprobe -version
```

## Installation from Source

Clone the repository and run it from the project directory:

```bash
git clone https://github.com/henry-w-slough/slankvideos.git
cd slankvideos
python -m pip install httpx m3u8 playwright
python -m playwright install chromium
```

## Public API

- `RequestHandler` sends and retries HTTP requests.
- `WebScraper` loads pages and discovers HLS requests.
- `M3U8Handler` parses playlists and selects variants.
- `DataHandler` writes segments, validates files, and runs FFmpeg transcoding.
- `Request` describes an HTTP request.
- `SuccessResponse` and `ErrorResponse` contain HTTP results or request failures.
- `ProxyData` stores HTTP and HTTPS proxy URLs.
- `M3U8Data` stores a captured playlist URL plus headers and cookies.
- `VideoFormat` lists supported output formats.

## License

This project is licensed under the terms of the MIT License.



