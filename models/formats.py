from enum import Enum


class VideoFormat(Enum):
    TS = "ts"
    MP4 = "mp4"
    MKV = "mkv"
    AVI = "avi"
    FLV = "flv"


    @property
    def ffmpeg_name(self) -> str:
        """The format name ffmpeg's -f flag expects for this format."""
        return {
            VideoFormat.TS: "mpegts",
            VideoFormat.MP4: "mp4",
            VideoFormat.MKV: "matroska",
            VideoFormat.AVI: "avi",
            VideoFormat.FLV: "flv",
        }[self]


    @property
    def extension(self) -> str:
        """The typical file extension for this format."""
        return self.value