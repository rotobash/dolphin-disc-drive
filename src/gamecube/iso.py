import bsdiff4
from mmap import ACCESS_READ, ACCESS_WRITE, mmap
from pathlib import Path
from typing_extensions import Self
from zipfile import ZipFile
from io import BytesIO

from . import GamecubeFileFactory, DiscHeader, DiscHeaderInformation, DOL, AppLoader, TableOfContents, FSTFile, SYSTEM_CODES
from .. import AbstractFileArchive, AbstractFile, NotImplementedFile, Stream, MemoryStream, MMapStream
from tqdm import tqdm


class GamecubeISO(AbstractFileArchive):
    """
    ISO files are game images burnt on to a disc. 
    """
    DiscHeaderSize = 0x0440
    DiscHeaderInformationSize = 0x2000
    AppLoaderStartOffset = 0x2440

    def __init__(self, filename: str, file_contents: Stream):

        super().__init__(filename, file_contents)
        self.load_system_header(file_contents)

    def load_system_header(self, header_contents: Stream):
        disc_header = header_contents.get_bytes_at_offset(0, self.DiscHeaderSize)
        self.disc_header = DiscHeader(MemoryStream(disc_header))

        disc_header_information = header_contents.get_bytes_at_offset(
            self.DiscHeaderSize, self.DiscHeaderInformationSize
        )
        self.disc_header_information = DiscHeaderInformation(
            MemoryStream(disc_header_information)
        )

        app_loader = header_contents.get_bytes_at_offset(
            self.AppLoaderStartOffset,
            self.disc_header.fst_offset - self.AppLoaderStartOffset,
        )
        self.app_loader = AppLoader(MemoryStream(app_loader))

        fst_bin = header_contents.get_bytes_at_offset(
            self.disc_header.fst_offset, self.disc_header.fst_size
        )
        self.table_of_contents = TableOfContents(MemoryStream(fst_bin))

        dol_header = header_contents.get_bytes_at_offset(self.disc_header.dol_offset, 0xFF)
        self.dol = DOL(MemoryStream(dol_header))
        dol_payload = header_contents.get_bytes_at_offset(
            self.disc_header.dol_offset, self.dol.get_dol_size()
        )
        self.dol.load_section_contents(MemoryStream(dol_payload))

    
    def get_file_list(self) -> "list[str]":
        files = self.table_of_contents.get_fst_file_list()
        return [f.filename for f in files]

    def _extract_file_by_entry(self, file: FSTFile) -> AbstractFile:
        if file is not None:
            stream = MemoryStream(
                self.file_contents.get_bytes_at_offset(file.old_offset, file.old_size)
            )
        else:
            stream = MemoryStream(bytearray())

        extracted_file = GamecubeFileFactory.read_file(str(file.filename), stream)
        return extracted_file

    def _extract_file(self, filename: str) -> AbstractFile:
        if filename == "system.bin":
            header_file = MemoryStream()
            self.write_system_files(header_file)
            return NotImplementedFile(filename, header_file)
        file = self.table_of_contents.search_file_by_name(filename)
        return self._extract_file_by_entry(file)
    
    
    def extract_files(self) -> "dict[str, AbstractFile]":
        files = self.table_of_contents.get_fst_file_list()
        return dict(*[(f.filename, self._extract_file_by_entry(f)) for f in files])


    def add_new_file(self, file: AbstractFile, parent_directory: str = None):
        # update FST
        # add file to list of pending files

        fst_directory = self.table_of_contents.root_directory
        if parent_directory is not None:
            fst_directories = self.table_of_contents.get_fst_directory_list()
            for dir in fst_directories:
                if dir.filename == parent_directory:
                    fst_directory = dir
                    break

        self.table_of_contents.add_file(
            file.file_name,
            file.file_contents.stream_size,
            fst_directory,
        )
        super().add_new_file(file, parent_directory)

    def replace_file(self, file: AbstractFile):
        if file.file_name == "system.bin":
            self.load_system_header(file.file_contents)
        else:            
            existing_fst = self.table_of_contents.search_file_by_name(file.file_name)
            if existing_fst is not None:
                existing_fst.data_size = file.file_contents.stream_size
                self.table_of_contents.update_fst_offsets()
                super().replace_file(file)

    def delete_file(self, file: AbstractFile):
        self.table_of_contents.remove_file(file)
        super().delete_file(file)

    def get_system_size(self):
        image_size = 0
        image_size += self.disc_header.file_contents.stream_size
        image_size += self.disc_header_information.file_contents.stream_size
        image_size += self.app_loader.file_contents.stream_size
        image_size += self.table_of_contents.file_size
        image_size += self.dol.get_dol_size()
        return image_size + Stream.align_bytes(image_size)

    def get_archive_size(self):
        fst_list = self.table_of_contents.get_fst_file_list()
        fst_list.sort(key=lambda f: f.data_offset)
        file_size = fst_list[-1].data_offset + fst_list[-1].data_size
        return file_size + Stream.align_bytes(file_size)
    
    def write_system_files(self, write_stream: Stream):
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

            dol_bytes = self.dol.to_bytes()
            write_stream.write_bytes_at_offset(self.disc_header.dol_offset, dol_bytes)
            pbar.update(1)


    def build_archive(self, write_stream: Stream):
        fst_list = self.table_of_contents.get_fst_file_list()
        fst_list.sort(key=lambda fst: fst.data_offset)

        # write system files
        print("Serializing system files")
        self.write_system_files(write_stream)

        print("Scanning extracted files for changes.")
        changed_size = False
        for file in fst_list:
            file_name = str(file.filename)
            if file_name in self.extracted_archive_files:
                new_file = self.extracted_archive_files[str(file.filename)]
                size = new_file.file_contents.stream_size
                if size > file.data_size:
                    file.data_size = size + Stream.align_bytes(size)
                    changed_size = True
        
        if changed_size:
            print("Files were altered. Defragmenting to ensure we can fit the changes into the image.")
            self.table_of_contents.defragment(self.get_system_size())
            self.table_of_contents.update_fst_offsets()

        
        # write FST last incase we just updated the offsets
        fst_bytes = self.table_of_contents.to_bytes()
        fst_bytes.extend([0] * Stream.align_bytes(len(fst_bytes)))
        write_stream.write_bytes_at_offset(self.disc_header.fst_offset, fst_bytes)


        print("Serializing game files")
        for child in tqdm(fst_list):
            file_name = str(child.filename)
            file_contents = self.extracted_archive_files[file_name] if file_name in self.extracted_archive_files else self._extract_file_by_entry(child)

            write_stream.write_bytes_at_offset(
                child.data_offset, file_contents.to_bytes()
            )

    def save_to_disk(self, path: "Path | str"):
        with Path(path).open("wb+") as image_file:
            # allocate space
            buffer = bytes([0] * 2048)
            file_size = self.get_archive_size()
            for i in range((file_size // 2048)):
                image_file.write(buffer)

            image_file.flush()
            with mmap(image_file.fileno(), 0, access=ACCESS_WRITE) as mmap_stream:
                output_stream = MMapStream(mmap_stream)
                self.build_archive(output_stream)

    def build_patch_file(self) -> "dict[str, bytes]":
        zipfile = BytesIO()
        with ZipFile(zipfile, 'w') as out_file:
            out_file.writestr("SYSCODE", [SYSTEM_CODES["gamecube"]])
            for file_name, file in self.extracted_archive_files.items():
                patch_file = file.build_patch_file()
                if patch_file is not None:
                    out_file.writestr(f"{file_name}.patch", patch_file)

            new_header_file = MemoryStream()
            self.write_system_files(new_header_file)

            old_header_file = MemoryStream()
            disc_header_bytes = self.disc_header.file_contents
            old_header_file.write_bytes_at_offset(0, disc_header_bytes)

            disc_header_info_bytes = self.disc_header_information.file_contents
            old_header_file.write_bytes_at_offset(
                len(disc_header_bytes), disc_header_info_bytes
            )

            app_loader_bytes = self.app_loader.file_contents
            old_header_file.write_bytes_at_offset(
                self.AppLoaderStartOffset, app_loader_bytes
            )

            dol_bytes = self.dol.file_contents
            old_header_file.write_bytes_at_offset(
                self.disc_header.dol_offset, dol_bytes
            )

            patch_header = bsdiff4.diff(old_header_file, new_header_file)
            out_file.writestr("system.bin.patch", patch_header)


        return zipfile.getvalue()

    @staticmethod
    def open_image_file(path: "Path | str") -> Self:
        with path.open("rb") as in_file:
            mmap_stream = mmap(in_file.fileno(), 0, access=ACCESS_READ)
            return GamecubeISO(path.name, MMapStream(mmap_stream))