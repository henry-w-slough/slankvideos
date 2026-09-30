from ..models.responses import Response, ErrorResponse, SuccessResponse
from ..models.data_types.formats import VideoFormat
import asyncio
import os


class DataHandler:


    def __init__(self, default_format: VideoFormat = VideoFormat.MP4):
        """Handles all file and data management, including reading, writing, and transcoding."""

        self._file = None
        self.default_format: VideoFormat = default_format


    async def write_response(self, response: Response) -> None:
        """Writes the response.http_response.content of the given Response to the open file. Make sure to run open_file() first."""

        if isinstance(response, ErrorResponse):
            return

        await asyncio.to_thread(self._write, response.http_response.content)


    async def transcode_file(self, original_src: str, transcoded_src: str, format: VideoFormat | None = None, delete_src: bool = True) -> None:
        """Takes the source of an untranscoded file and transcodes it, putting the new version  in transcoded_src.
        Optionally, you can pass in a VideoFormat to specify transcoding file type, or specify whether to delete the untranscoded file path."""

        if format is None:
            format = self.default_format

        transcoded_path = f"{transcoded_src}{format.extension}"

        os.makedirs(os.path.dirname(transcoded_path), exist_ok=True)

        args = [
            "ffmpeg", 
            "-i", original_src, 
            "-c", "copy", 
            "-movflags", 
            "+faststart", transcoded_path]

        process = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {stderr.decode(errors='replace')}")

        if delete_src:
            os.remove(original_src)


    def _write(self, data: bytes) -> None:
        
        if self._file is None:
            raise RuntimeError("File source was not open to write. Call open_file() before writing.")
        
        self._file.write(data)
    

    def open_file(self, src: str) -> None:
        """Opens the given file path for writing bytes."""
        self._file = open(src, "wb")


    def close_file(self) -> None:
        """Closes the file path opened with open_file()."""
        if self._file:
            self._file.close()
            self._file = None


