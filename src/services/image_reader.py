from mmap import ACCESS_WRITE, mmap, ACCESS_READ
from pathlib import Path
from tqdm import tqdm

from src.definitions.files.system import (
    DiscHeader,
    DiscHeaderInformation,
    AppLoader,
    TableOfContents,
    DOL,
    FSTFile,
    FSTDirectory,
)
from src.definitions import MemoryStream, MMapStream, Stream, AbstractFile
from src.definitions.unicode import UnicodeString

from .factories import AbstractFileFactory


class GamecubeImageReader:
    DiscHeaderSize = 0x0440
    DiscHeaderInformationSize = 0x2000
    AppLoaderStartOffset = 0x2440

    def __init__(self, path: "Path | str"):
        path = Path(path)
        self.opened_files: "dict[str, AbstractFile]" = {}

        with path.open("rb") as file:
            contents = mmap(file.fileno(), 0, access=ACCESS_READ)

        self.image_stream = AbstractFileFactory.read_file(
            path.suffix, MMapStream(contents)
        )

        disc_header = self.image_stream.read_bytes(0, self.DiscHeaderSize)
        self.disc_header = DiscHeader(MemoryStream(disc_header))

        disc_header_information = self.image_stream.read_bytes(
            self.DiscHeaderSize, self.DiscHeaderInformationSize
        )
        self.disc_header_information = DiscHeaderInformation(
            MemoryStream(disc_header_information)
        )

        app_loader = self.image_stream.read_bytes(
            self.AppLoaderStartOffset,
            self.disc_header.fst_offset - self.AppLoaderStartOffset,
        )
        self.app_loader = AppLoader(MemoryStream(app_loader))

        fst_bin = self.image_stream.read_bytes(
            self.disc_header.fst_offset, self.disc_header.fst_size
        )
        self.table_of_contents = TableOfContents(MemoryStream(fst_bin))

        dol_header = self.image_stream.read_bytes(self.disc_header.dol_offset, 0xFF)
        self.dol = DOL(MemoryStream(dol_header))
        dol_payload = self.image_stream.read_bytes(
            self.disc_header.dol_offset, self.dol.get_dol_size()
        )
        self.dol.load_section_contents(MemoryStream(dol_payload))

    def extract_file_by_name(self, filename: str) -> AbstractFile:
        file = self.table_of_contents.search_file_by_name(filename)
        return self.extract_file(file)

    def extract_file(self, file: FSTFile) -> AbstractFile:
        if file is not None:
            stream = MemoryStream(
                self.image_stream.read_bytes(file.old_offset, file.old_size)
            )
        else:
            stream = MemoryStream(bytearray())

        extracted_file = AbstractFileFactory.read_file(str(file.filename), stream)

        self.opened_files[extracted_file.file_name] = extracted_file
        return extracted_file

    def add_new_file(self, file: AbstractFile, parent_directory: FSTDirectory = None):
        # update FST
        # add file to list of pending files
        self.table_of_contents.add_file(
            UnicodeString(file.file_name),
            file.byte_stream.stream_size,
            parent_directory,
        )
        self.opened_files[file.file_name] = file

    def replace_file(self, file):
        pass

    def delete_file(self):
        pass

    def get_system_size(self):
        image_size = 0
        image_size += self.disc_header.byte_stream.stream_size
        image_size += self.disc_header_information.byte_stream.stream_size
        image_size += self.app_loader.byte_stream.stream_size
        image_size += self.table_of_contents.file_size
        image_size += self.dol.get_dol_size()
        return image_size + Stream.align_bytes(image_size)

    def get_image_size(self):
        fst_list = self.table_of_contents.get_fst_file_list()
        fst_list.sort(key=lambda f: f.data_offset)
        file_size = fst_list[-1].data_offset + fst_list[-1].data_size
        return file_size + Stream.align_bytes(file_size)

    def build_image(self, write_stream: Stream):

        # write system files
        print("Serializing system files")
        with tqdm(total=5) as pbar:
            disc_header_bytes = self.disc_header.to_bytes()
            write_stream.write_bytes_at_offset(0, disc_header_bytes)
            pbar.update(1)

            disc_header_info_bytes = self.disc_header_information.to_bytes()
            write_stream.write_bytes_at_offset(
                len(disc_header_bytes), disc_header_info_bytes
            )
            pbar.update(1)

            app_loader_bytes = self.app_loader.to_bytes()
            write_stream.write_bytes_at_offset(
                self.AppLoaderStartOffset, app_loader_bytes
            )
            pbar.update(1)

            fst_bytes = self.table_of_contents.to_bytes()
            fst_bytes.extend([0] * Stream.align_bytes(len(fst_bytes)))
            write_stream.write_bytes_at_offset(self.disc_header.fst_offset, fst_bytes)
            pbar.update(1)

            dol_bytes = self.dol.to_bytes()
            write_stream.write_bytes_at_offset(self.disc_header.dol_offset, dol_bytes)
            pbar.update(1)

        fst_list = list(self.table_of_contents.get_fst_file_list())
        fst_list.sort(key=lambda fst: fst.data_offset)

        print("Serializing game files")
        for child in tqdm(fst_list):
            if isinstance(child, FSTFile):
                file_name = str(child.filename)
                file_contents = (
                    self.opened_files[file_name]
                    if file_name in self.opened_files
                    else self.extract_file(child)
                )
                write_stream.write_bytes_at_offset(
                    child.data_offset, file_contents.to_bytes()
                )

    def save_to_disk(self, path):
        with Path(path).open("wb+") as image_file:
            # allocate space
            buffer = bytes([0] * 2048)
            file_size = self.get_image_size()
            for i in range((file_size // 2048) + 1):
                image_file.write(buffer)

            with mmap(image_file.fileno(), 0, access=ACCESS_WRITE) as mmap_stream:
                output_stream = MMapStream(mmap_stream)
                self.build_image(output_stream)

            