from ..serializable_file import (
    EncodableFile,
)


class AppLoader(EncodableFile):
    def __init__(self, app_loader: bytearray) -> None:
        self.app_loader = app_loader

    def to_bytes(self) -> bytearray:
        return self.app_loader
