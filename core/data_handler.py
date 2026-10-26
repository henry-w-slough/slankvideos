from ..models.responses import Response, ErrorResponse, SuccessResponse
from ..models.data_types.formats import VideoFormat
from ..logging import logging
import asyncio
import json
import os
import tempfile


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


    async def validate_file(self, src: str) -> bool:
        """Checks if a given directory is a valid file and has data properly written to it using ffmpeg."""
        if not os.path.isfile(src) or os.path.getsize(src) <= 0:
            return False

        process = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration,size",
            "-of", "json",
            src,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return False

        try:
            probe_data = json.loads(stdout.decode(errors="replace"))
            duration = float(probe_data.get("format", {}).get("duration", 0))
            size = int(probe_data.get("format", {}).get("size", 0))
            return duration > 0 and size > 0
        
        except (TypeError, ValueError, json.JSONDecodeError):
            return False


    async def transcode_file(self, original_src: str, transcoded_src: str, format: VideoFormat | None = None, delete_src: bool = True) -> None:
        """Takes the source of an untranscoded file and transcodes it, putting the new version  in transcoded_src.
        Optionally, you can pass in a VideoFormat to specify transcoding file type, or specify whether to delete the untranscoded file path."""

        if format is None:
            format = self.default_format

        transcoded_path = f"{transcoded_src}{format.extension}"
        destination_dir = os.path.dirname(transcoded_path)

        if destination_dir:
            os.makedirs(destination_dir, exist_ok=True)

        temporary_file = tempfile.NamedTemporaryFile(
            prefix=".slankvideos-",
            suffix=format.extension,
            dir=destination_dir or None,
            delete=False,
        )
        temporary_output = temporary_file.name
        temporary_file.close()

        args = [
            "ffmpeg",
            "-y",
            "-i", original_src,
            "-c", "copy",
            "-movflags",
            "+faststart", temporary_output,
        ]

        logging.log(
            f"Starting transcode from '{os.path.abspath(original_src)}' to '{os.path.abspath(transcoded_path)}' in {format.name} format.",
            logging.Severity.INFO,
        )

        try:
            #starting ffmpeg async with previous arguments
            process = await asyncio.create_subprocess_exec(
                *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()

            #waiting for ffmpeg to finish
            if process.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {stderr.decode(errors='replace')}")

            #probe for the transcoded file
            probe = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration,size",
                "-of", "json",
                temporary_output,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            #waiting for probe to finish
            probe_stdout, probe_stderr = await probe.communicate()

            #bad probe return
            if probe.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {probe_stderr.decode(errors='replace')}")

            probe_data = json.loads(probe_stdout.decode(errors="replace"))
            duration = float(probe_data.get("format", {}).get("duration", 0))
            size = int(probe_data.get("format", {}).get("size", 0))

            if duration <= 0 or size <= 0:
                raise RuntimeError("Transcoded output contains no valid media data.")

            os.replace(temporary_output, transcoded_path)
            logging.log(
                f"Transcode completed successfully: '{os.path.abspath(transcoded_path)}'.",
                logging.Severity.SUCCESS,
            )

            if delete_src and os.path.exists(original_src):
                os.remove(original_src)
                
        except Exception as error:
            if os.path.exists(temporary_output):
                os.remove(temporary_output)
            logging.log(
                f"Transcoding from '{temporary_output}' failed: {type(error).__name__} caught in process. Removed temporary directory.",
                logging.Severity.ERROR,
            )
            raise


    def _write(self, data: bytes) -> None:
        
        if self._file is None:
            raise RuntimeError("File source was not open to write. Call open_file() before writing.")
        
        self._file.write(data)
    

    def open_file(self, src: str) -> None:
        """Opens the given file path for writing bytes."""
        self._file = open(src, "wb")
        logging.log(
            f"Opened file for writing: '{os.path.abspath(src)}'.",
            logging.Severity.INFO,
        )


    def close_file(self) -> None:
        """Closes the file path opened with open_file()."""
        if self._file:
            self._file.close()
            self._file = None


