import abc
from mmap import mmap
from ..unicode import UnicodeString, UnicodeCharacter


class Stream(abc.ABC):
    def __init__(self) -> None:
        self.stream = None
        self.stream_size = 0

    @abc.abstractmethod
    def get_bytes_at_offset(
        self, offset: int, count: int
    ) -> bytearray:
        """
        Retrieve a number of bytes in the stream at a given offset.
        """

    @abc.abstractmethod
    def write_bytes_at_offset(
        self, offset: int, value: bytearray
    ) -> int:
        """
        Replace bytes in the stream at a given offset with the value provided. 
        """

    @abc.abstractmethod
    def insert_into_stream(
        self, offset: int, data: bytearray
    ):
        """
        Insert data to the stream at a given an offset while moving the data at offset + 1 to be at offset + len(data)
        """

    @abc.abstractmethod
    def delete_from_stream(
        self, offset: int, byte_count: int
    ):
        """
        Delete a number of bytes at a given an offset while moving the data at offset + byte_count to be at offset + 1
        """

    def get_byte_at_offset(self, offset: int) -> int:
        return self.get_bytes_at_offset(offset, 1)[0]

    def get_int_at_offset(self, offset: int) -> int:
        stream_bytes = self.get_bytes_at_offset(offset, 4)
        return int.from_bytes(stream_bytes, "big")

    def get_string_at_offset(
        self, offset: int
    ) -> UnicodeString:
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

    def write_int_at_offset(
        self, offset: int, value: int
    ) -> int:
        int_bytes = value.to_bytes(4, "big")
        self.write_bytes_at_offset(offset, int_bytes)

    def write_string_at_offset(
        self, offset: int, string: UnicodeString
    ):
        data = bytearray([c.char_byte for c in string.chars])
        self.write_bytes_at_offset(offset, data)
        return string

    def occurrence_of_bytes(self, marker: int):
        marker_offsets = []
        for i in range(len(self.stream)):
            check_bytes = self.get_int_at_offset(i)
            if check_bytes == marker:
                marker_offsets.append(i)
                i += 4
        return marker_offsets
    
    def is_valid_range(self, offset: int, size: int):
        return offset >= 0 and offset + size <= self.stream_size

class MMapStream(Stream):
    def __init__(self, stream: mmap) -> None:
        self.stream = stream
        self.stream_size = stream.size()

    def get_bytes_at_offset(self, offset: int, count: int) -> bytearray:
        self.stream.seek(offset)
        return bytearray(self.stream.read(count))

    def write_bytes_at_offset(self, offset: int, value: bytearray) -> int:
        self.stream.seek(offset)
        self.stream.write(value)

    def insert_into_stream(self, offset: int, data: bytearray):
        self.stream.move(offset + len(data), offset, len(self.stream) - offset)
        self.write_bytes_at_offset(offset, data)
        
    def delete_from_stream(self, offset: int, byte_count: int):
        end_offset = offset + byte_count
        self.stream.move(offset, end_offset, len(self.stream) - end_offset)
        self.stream.resize(len(self.stream) - byte_count)

    def close(self):
        if self.stream is not None:
            self.stream.close()

class MemoryStream(Stream):
    def __init__(self, stream: bytearray) -> None:
        self.stream = stream
        self.stream_size = len(stream)

    def get_bytes_at_offset(self, offset: int, count: int) -> bytearray:
        return self.stream[offset : offset + count]

    def write_bytes_at_offset(self, offset: int, value: bytearray) -> int:
        for i in range(len(value)):
            self.stream[offset + i] = value[i]

    def insert_into_stream(self, offset: int, data: bytearray):
        for i in len(data):
            self.stream.insert(offset + i, data[i])
    
    def delete_from_stream(self, offset: int, byte_count: int):
        for i in range(byte_count):
            self.stream.pop(offset + i)