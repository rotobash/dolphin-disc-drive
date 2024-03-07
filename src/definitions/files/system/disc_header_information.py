from ..serializable_file import (
    EncodableFile,
)


class DiscHeaderInformation(EncodableFile):
    def __init__(self, bi2_bin: bytearray) -> None:
        self.bi2_bin = bi2_bin

    def to_bytes(self) -> bytearray:
        return self.bi2_bin
