from src.definitions import AbstractFile, NotImplementedFile, Stream
from src.definitions.files.common import REL, ISO


class AbstractFileFactory:
    @staticmethod
    def read_file(filename: str, file_contents: Stream) -> AbstractFile:
        file_name = filename.lower()

        if ".rel" in file_name:
            return REL(file_name, file_contents)
        if ".iso" in file_name:
            return ISO(file_name, file_contents)

        return NotImplementedFile(file_name, file_contents)
