from ..models.responses import Response

import asyncio


class DataHandler:


    def __init__(self):
        self._file = None


    def open_file(self, src: str) -> None:
        """Opens the given file path for writing bytes."""
        self._file = open(src, "wb")


    def close_file(self) -> None:
        """Closes the file path opened with open_file()."""
        if self._file:
            self._file.close()
            self._file = None


    def _write(self, content: bytes) -> None:
        
        if self._file is None:
            raise RuntimeError("File source was not open to write. Call open_for_write() before writing.")
        
        self._file.write(content)


    async def write_response(self, response: Response) -> None:
        """Writes the response.http_response.content of the given Response to the open file. Make sure to run open_file() first."""
        if response.error is not None or response.http_response is None:
            return
        await asyncio.to_thread(self._write, response.http_response.content)




