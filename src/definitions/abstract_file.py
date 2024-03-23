import abc
from enum import Enum
import json
from typing import Iterable, Union

from . import Serializable, Stream


class FileChangeType(Enum):
    REPLACE = 0
    INSERT = 1
    DELETE = 2


class FileChange:
    def __init__(
        self,
        change_type: FileChangeType,
        offset: int,
        value: "Union[Iterable[int], int]" = 0,
    ) -> None:
        self.change_type = change_type
        self.offset = offset
        self.value = value


class AbstractFile(Serializable, abc.ABC):
    """
    Abstract class for reading files. This provides a wrapper around reading
    byte streams and abstracting away different file types.
    """

    def __init__(
        self,
        file_name: str,
        file_contents: Stream,
        compression_method: str = "none",
        encryption_method: str = "none",
    ) -> None:
        self.file_name = file_name
        self.compression_method = compression_method
        self.encryption_method = encryption_method
        self.file_contents: Stream = file_contents

        self.changes: list[FileChange] = []

    def read_bytes(self, offset: int, count: int) -> bytearray:
        return self.file_contents.get_bytes_at_offset(offset, count)

    def replace_bytes(self, offset: int, value: bytearray):
        self.changes.append(FileChange(FileChangeType.REPLACE, offset, value))

    def insert_bytes(self, offset: int, value: bytearray):
        self.changes.append(FileChange(FileChangeType.INSERT, offset, value))

    def delete_bytes(self, offset: int, count: int):
        self.changes.append(FileChange(FileChangeType.DELETE, offset, count))

    def undo_change(self):
        self.changes.pop()

    def to_bytes(self) -> bytearray:
        """
        Serialize this file into bytes.
        If we have pending changes, return a new stream copy with the changes applied.
        """
        byte_stream = self.file_contents.copy()
        if len(self.changes) > 0:
            for change in self.changes:
                if change.change_type == FileChangeType.INSERT:
                    byte_stream.insert_into_stream(change.offset, change.value)
                elif change.change_type == FileChangeType.REPLACE:
                    byte_stream.write_bytes_at_offset(change.offset, change.value)
                elif change.change_type == FileChangeType.DELETE:
                    byte_stream.delete_from_stream(change.offset, change.value)

        return byte_stream

    def to_json_obj(self) -> dict:
        """
        Serialize this file into a JSON representation that easy for humans to parse.
        """
        return {"NotImplemented": self.file_name}

    def __str__(self) -> str:
        return json.dumps(self.to_json_obj())

    def get_file_type(self) -> str:
        return self.file_name.rsplit(".")[-1]


class NotImplementedFile(AbstractFile):
    pass
