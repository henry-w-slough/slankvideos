from ..models.responses import Response, ErrorResponse, SuccessResponse
from ..models.formats import VideoFormat
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


    async def transcode_file(self, src: str, dest: str, format: VideoFormat | None = None, delete_src: bool = True) -> str:
        """Passes src to ffmpeg directly to transcode into dest. Note that dest must ONLY be the filename without the extension,
        as ffmpeg will infer the format based on the extension, which is set with the optional format arg.
        
        Returns the path of dest with it's new format."""

        if format is None:
            format = self.default_format

        dest_filename = f"{dest}.{format.extension}"

        os.makedirs(os.path.dirname(dest_filename), exist_ok=True)

        args = [
            "ffmpeg", 
            "-i", src, 
            "-c", "copy", 
            "-movflags", 
            "+faststart", dest_filename]

        process = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {stderr.decode(errors='replace')}")

        if delete_src:
            os.remove(src)

        return dest_filename
    

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


