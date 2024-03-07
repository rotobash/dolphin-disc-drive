import abc
from mmap import ACCESS_READ, mmap
from pathlib import Path

from . import MMapStream

class StreamReader(abc.ABC):
    def __init__(self, path_to_image: "Path | str") -> None:
        self.byte_stream = None
        path_to_image = Path(path_to_image)
        if path_to_image.exists():
            with path_to_image.open("r") as iso:
                stream_mmap = mmap(iso.fileno(), 0, access=ACCESS_READ)
                self.byte_stream = MMapStream(stream_mmap)
                self.decompress()
        else:
            raise FileNotFoundError("File could not be loaded because it doesn't exist. Check the path and try again.")

    @abc.abstractmethod
    def decompress(self):
        """
        Apply decompression to the loaded stream. 
        This is to allow support for other file formats.
        """

    def read_byte(self, offset: int):
        return self.byte_stream.get_byte_at_offset(offset)

    def read_bytes(self, offset: int, count: int):
        return self.byte_stream.get_bytes_at_offset(offset, count)

    def __del__(self):
        if self.byte_stream is not None:
            self.byte_stream.close()