import abc

from mmap import mmap
from typing_extensions import Self
from .unicode import UnicodeString, UnicodeCharacter


class Stream(abc.ABC):
    def __init__(self) -> None:
        self.stream = None
        self.stream_size = 0

    @abc.abstractmethod
    def copy(self) -> Self:
        """ """

    @abc.abstractmethod
    def get_bytes_at_offset(self, offset: int, count: int) -> bytearray:
        """
        Retrieve a number of bytes in the stream at a given offset.
        """

    @abc.abstractmethod
    def write_bytes_at_offset(self, offset: int, value: bytearray) -> int:
        """
        Replace bytes in the stream at a given offset with the value provided.
        """

    @abc.abstractmethod
    def insert_into_stream(self, offset: int, data: bytearray):
        """
        Insert data to the stream at a given an offset while
        moving the data at offset + 1 to be at offset + len(data)
        """

    @abc.abstractmethod
    def delete_from_stream(self, offset: int, byte_count: int):
        """
        Delete a number of bytes at a given an offset while
        moving the data at offset + byte_count to be at offset + 1
        """

    def get_byte_at_offset(self, offset: int) -> int:
        """
        Retrieve a single byte at a given offset.
        This is short hand for get_bytes_at_offset(offset, 1)
        """
        return self.get_bytes_at_offset(offset, 1)[0]

    def get_int_at_offset(self, offset: int) -> int:
        """
        Retrieve a 4 bytes at a given offset and interpret it as an int.
        This converts the big endianness of the GC to the host's endianess.
        """
        stream_bytes = self.get_bytes_at_offset(offset, 4)
        return int.from_bytes(stream_bytes, "big")

    def get_string_at_offset(self, offset: int) -> UnicodeString:
        """
        Retrieve a Unicode string at a given offset.
        Warning: This reads bytes until it finds a null termination (i.e. 0)
        """
        string = UnicodeString()
        current_offset = offset
        char_byte = self.get_byte_at_offset(current_offset)

        while char_byte != 0:
            string.add_character(UnicodeCharacter(char_byte))

            current_offset += 1
            char_byte = self.get_byte_at_offset(current_offset)

        return string

    def write_byte_at_offset(self, offset: int, value: int):
        self.write_bytes_at_offset(offset, [value])

    def write_int_at_offset(self, offset: int, value: int) -> int:
        int_bytes = value.to_bytes(4, "big")
        self.write_bytes_at_offset(offset, int_bytes)

    def write_string_at_offset(self, offset: int, string: UnicodeString):
        self.write_bytes_at_offset(offset, string.to_bytes())
        return string

    def occurrence_of_bytes(self, marker: int) -> "list[int]":
        """
        Check for a specific int value anywhere in the stream.
        This returns all offsets where the marker is found.
        """
        marker_offsets = []
        for i in range(len(self.stream)):
            check_bytes = self.get_int_at_offset(i)
            if check_bytes == marker:
                marker_offsets.append(i)
                i += 4
        return marker_offsets

    @staticmethod
    def align_bytes(length: int, alignment=2048) -> int:
        """
        Get the number of padding bytes required to have an even multiple of the given alignment.
        """
        m = length % alignment
        return 0 if m == 0 else alignment - m

    def is_valid_range(self, offset: int, size: int) -> bool:
        """
        Check if the offset + size is within the stream boundaries.
        """
        return offset >= 0 and offset + size <= self.stream_size


class MMapStream(Stream):
    def __init__(self, stream: mmap) -> None:
        super().__init__()
        self.stream: mmap = stream
        self.stream_size = stream.size()

    def copy(self) -> Self:
        pass

    def get_bytes_at_offset(self, offset: int, count: int) -> bytearray:
        self.stream.seek(offset)
        return bytearray(self.stream.read(count))

    def write_bytes_at_offset(self, offset: int, value: bytearray) -> int:
        self.stream.seek(offset)
        self.stream.write(value)

    def insert_into_stream(self, offset: int, data: bytearray):
        byte_count = len(data)
        if self.stream_size < offset:
            byte_count += offset - self.stream_size

        self.stream.resize(self.stream_size + byte_count)
        self.stream_size += byte_count

        self.stream.move(offset + byte_count, offset, self.stream_size - offset)
        self.write_bytes_at_offset(offset, data)

    def delete_from_stream(self, offset: int, byte_count: int):
        end_offset = offset + byte_count
        self.stream.move(offset, end_offset, self.stream_size - end_offset)
        self.stream.resize(self.stream_size - byte_count)
        self.stream_size -= byte_count

    def close(self):
        if self.stream is not None:
            self.stream.close()


class MemoryStream(Stream):
    def __init__(self, stream: "list[int] | bytearray | bytes" = []) -> None:
        super().__init__()
        if not isinstance(stream, bytearray):
            stream = bytearray(stream)

        self.stream = stream
        self.stream_size = len(stream)

    def copy(self) -> Self:
        return bytearray(self.stream)

    def get_bytes_at_offset(self, offset: int, count: int) -> bytearray:
        return self.stream[offset : offset + count]

    def write_bytes_at_offset(self, offset: int, value: bytearray) -> int:
        byte_count = len(value)

        add_bytes = (offset + byte_count) - self.stream_size
        if add_bytes > 0:
            self.stream.extend([0] * add_bytes)

        self.stream[offset : offset + byte_count] = value

    def insert_into_stream(self, offset: int, data: bytearray):
        stream_size_change = len(data)
        if self.stream_size < offset:
            extend_bytes = offset - self.stream_size
            self.stream.extend([0] * extend_bytes)
            stream_size_change += extend_bytes

        self.stream = self.stream[:offset] + data + self.stream[offset:]
        self.stream_size += stream_size_change

    def delete_from_stream(self, offset: int, byte_count: int):
        self.stream[offset:] = self.stream[offset + byte_count :]
        self.stream_size -= byte_count
