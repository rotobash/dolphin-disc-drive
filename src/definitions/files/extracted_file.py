import abc

from ..unicode import UnicodeString
from .stream import Stream
from .system import FSTEntry

class ExtractedFile(abc.ABC):
    def __init__(self, fst_entry: FSTEntry, file_contents: Stream) -> None:
        self.filename: UnicodeString = UnicodeString("")
        self.fst: FSTEntry = fst_entry
        self.filetype: str = ""
        self.contents = file_contents

class UnknownExtractedFile(ExtractedFile):
    pass