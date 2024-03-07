from mmap import mmap, ACCESS_WRITE
from pathlib import Path
from ....definitions.files import MMapStream


class ISOStreamBuilder:
    def __init__(self, path_to_image: "Path | str") -> None:
        with open(path_to_image, "r") as iso:
            stream_mmap = mmap(iso.fileno(), 0, access=ACCESS_WRITE)
            self.byte_stream = MMapStream(stream_mmap)

    def read_byte(self, offset: int):
        return self.byte_stream.get_byte_at_offset(offset)

    def read_bytes(self, offset: int, count: int):
        return self.byte_stream.get_bytes_at_offset(
            offset, count
        )

    def __del__(self):
        if self.byte_stream is not None:
            self.byte_stream.close()
