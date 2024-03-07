import abc
import json


class SerializableFile(abc.ABC):
    def to_json_obj(self) -> dict:
        """
        Serialize this file into a JSON representation that easy for humans to parse.
        """

    def __str__(self) -> str:
        return json.dumps(self.to_json_obj())


class EncodableFile(abc.ABC):
    def to_bytes(self) -> bytearray:
        """
        Serialize this file into bytes. This is to repack the file into the ISO.
        """
