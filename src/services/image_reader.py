from pathlib import Path

from ..definitions.files.system import (
    DiscHeader,
    DiscHeaderInformation,
    AppLoader,
    TableOfContents,
    DOL,
)
from .streams.iso import ISOStreamReader
from ..definitions.files import MemoryStream, ExtractedFile, UnknownExtractedFile

DiscHeaderSize = 0x0440
DiscHeaderInformationSize = 0x2000
AppLoaderStartOffset = 0x2440


class GamecubeImageReader():
    def __init__(self, path: "Path | str"):
        self.iso_stream = ISOStreamReader(path)

        disc_header = self.iso_stream.read_bytes(0, DiscHeaderSize)
        self.disc_header = DiscHeader(MemoryStream(disc_header))

        disc_header_information = self.iso_stream.read_bytes(
            DiscHeaderSize, DiscHeaderInformationSize
        )
        self.disc_header_information = DiscHeaderInformation(MemoryStream(disc_header_information))

        app_loader = self.iso_stream.read_bytes(
            AppLoaderStartOffset, self.disc_header.fst_offset - AppLoaderStartOffset
        )
        self.app_loader = AppLoader(MemoryStream(app_loader))

        fst_bin = self.iso_stream.read_bytes(
            self.disc_header.fst_offset, self.disc_header.fst_size
        )
        self.table_of_contents = TableOfContents(MemoryStream(fst_bin))

        dol_header = self.iso_stream.read_bytes(self.disc_header.dol_offset, 0xFF)
        self.dol = DOL(MemoryStream(dol_header))
        dol_payload = self.iso_stream.read_bytes(
            self.disc_header.dol_offset, self.dol.get_dol_size()
        )
        self.dol.load_section_contents(MemoryStream(dol_payload))

    def _align_bytes(self, value, alignment=2048):
        m = value % alignment
        return 0 if m == 0 else alignment - m

    def extract_file(self, filename: str) -> ExtractedFile:
        file = self.table_of_contents.search_file_by_name(filename)
        if file is not None:
            stream = MemoryStream(self.iso_stream.read_bytes(file.data_offset, file.data_size))
        else:
            stream = MemoryStream(bytearray())
        return UnknownExtractedFile(file, stream)

    def add_new_file(self, file):
        pass

    def replace_file(self, file):
        pass

    def delete_file(self):
        pass
