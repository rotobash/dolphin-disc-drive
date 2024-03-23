from .. import NotImplementedFile, AbstractFile, Stream
from .dol import *
from .fst import *
from .toc import *
from .disc_header import DiscHeader
from .disc_header_information import DiscHeaderInformation
from .app_loader import AppLoader
from .rel import *


class GamecubeFileFactory:
    @staticmethod
    def read_file(filename: str, file_contents: Stream) -> AbstractFile:
        file_name = filename.lower()

        if ".rel" in file_name:
            return REL(file_name, file_contents)

        return NotImplementedFile(file_name, file_contents)


from .iso import *