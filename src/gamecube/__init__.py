from .. import NotImplementedFile, AbstractFile, Stream
from .dol import *
from .fst import *
from .toc import *
from .disc_header import DiscHeader
from .disc_header_information import DiscHeaderInformation
from .app_loader import AppLoader
from .rel import *

gamecube_file_types: "dict[str, type]" = {}

class GamecubeFileFactory:
    @staticmethod
    def register_file(extension: str, file_type: type):
        gamecube_file_types[extension] = file_type

    @staticmethod
    def read_file(filename: str, file_contents: Stream) -> AbstractFile:
        file_name = filename.lower()
        ext = f".{file_name.rsplit('.')[-1]}"

        if ext in gamecube_file_types:
            return gamecube_file_types[ext](file_name, file_contents)

        return NotImplementedFile(file_name, file_contents)

GamecubeFileFactory.register_file('.dol', DOL)
GamecubeFileFactory.register_file('.rel', REL)

from .iso import *