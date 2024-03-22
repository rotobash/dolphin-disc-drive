from functools import reduce
from ... import (
    FSTDirectory,
    FSTRootDirectory,
    FSTFile,
    FSTEntry,
    AbstractFile,
    MemoryStream,
    Stream,
)
from ...unicode import UnicodeString


class TableOfContents(AbstractFile):
    TOCNumberEntriesOffset = 0x8
    TOCEntrySize = 0xC

    def __init__(self, fst_bin: Stream):
        """
        The TableOfContents (TOC or fst.bin) is a file that contains information of where files are stored on the disk.
        Each entry is 12 bytes and is either information about a file or a directory.

        Directories specify their parent directory and how many entries are contained in the folder.
        Files specify their disk offset and how big the file is.
        Both will have a name and a unique index.
        """
        super().__init__("fst.bin", fst_bin)
        number_of_entries = fst_bin.get_int_at_offset(self.TOCNumberEntriesOffset)
        self.root_directory = FSTRootDirectory(number_of_entries)
        self.string_table_offset = self.root_directory.next_offset * self.TOCEntrySize
        self.file_size = fst_bin.stream_size
        self._made_space = False

        self._load_fst(fst_bin, self.root_directory)

    def _load_fst(self, fst_bin: Stream, root: FSTDirectory, start_index=1):
        """
        Walk the table of contents and load the directory tree.
        This function recursively calls itself to load sub-directories.
        """
        index = start_index
        while index < root.next_offset:
            entry_offset = index * self.TOCEntrySize
            is_directory = fst_bin.get_byte_at_offset(entry_offset) != 0

            name_offset = fst_bin.get_int_at_offset(entry_offset) & 0x00FFFFFF

            if is_directory:
                parent_entry = fst_bin.get_int_at_offset(entry_offset + 4)
                end_dir_entry = fst_bin.get_int_at_offset(entry_offset + 8)
                file_entry = FSTDirectory(
                    index, name_offset, parent_entry, end_dir_entry
                )

                self._load_fst(fst_bin, file_entry, index + 1)
                index = end_dir_entry
            else:
                file_offset = fst_bin.get_int_at_offset(entry_offset + 4)
                file_size = fst_bin.get_int_at_offset(entry_offset + 8)

                file_entry = FSTFile(index, name_offset, file_offset, file_size)
                index += 1

            file_name_string = fst_bin.get_string_at_offset(
                self.string_table_offset + name_offset
            )
            file_entry.set_name(file_name_string)

            root.add_child(file_entry)

    def get_game_file_size(self):
        fst_list = self.get_fst_file_list()
        return sum([f.data_size for f in fst_list])

    def search_file_by_name(
        self, file_name: str, root: FSTDirectory = None
    ) -> "FSTFile | None":
        """
        Walk the filesystem to search for a file with a given name.
        """
        if root == None:
            root = self.root_directory
        for child in root._children:
            if isinstance(child, FSTDirectory):
                candidate = self.search_file_by_name(file_name, child)
                if candidate is not None:
                    return candidate
            elif str(child.filename) == file_name:
                return child

        return None

    def search_directory_by_name(
        self, dir_name: str, root: FSTDirectory = None
    ) -> "FSTDirectory | None":
        """
        Walk the filesystem to search for a directory with a given name.
        """
        if root == None:
            root = self.root_directory
        for child in root._children:
            if isinstance(child, FSTDirectory):
                if str(child.filename) == dir_name:
                    return child
                else:
                    candidate = self.search_directory_by_name(dir_name, child)
                    if candidate is not None:
                        return candidate

    def add_file(
        self,
        file_name: "UnicodeString | str",
        file_size: int,
        parent_directory: FSTDirectory = None,
    ):
        """
        Given a filename and its size, find available space for in the FST and create an entry for it.
        """
        filename = UnicodeString(file_name)
        if parent_directory is None:
            parent_directory = self.root_directory

        # overrun_bytes = file_size + self.total_image_size - 0x33333333333
        # if overrun_bytes > 0:
        #     print("WARNING: This file will make the image bigger than a standard ISO. This *may* work in an emulator but is likely to cause a crash.")
        #     print("Either remove the file, compress the file, or reduce the quality until it'll fit.")
        #     print(f"File overran by {overrun_bytes} bytes")

        fst_list = self.get_fst_list()
        # for entry in fst_list:
        #     if

        # fst_entry = FSTFile(, last_entry., file_size)

        self.update_fst_offsets()

    def remove_file(self, fst_entry: FSTEntry):
        self.update_fst_offsets()

    def update_fst_offsets(self):
        """
        Traverse the FST file list and fix any overlapping data offsets detected.
        """
        fst_list = self.get_fst_list()
        self.string_table_offset = len(self.root_directory) * self.TOCEntrySize

        fst_list: "list[FSTFile]" = list(self.get_fst_file_list())
        fst_list.sort(key=lambda fst: fst.data_offset)

        for i in range(len(fst_list) - 1):
            current_file = fst_list[i]
            next_file = fst_list[i + 1]

            if (
                current_file.data_offset + current_file.data_size
                != next_file.data_offset
            ):
                shift_amount = (
                    current_file.data_offset
                    + current_file.data_size
                    - next_file.data_offset
                )
                next_file.data_offset += shift_amount

    def defragment(self, start_offset=-1):
        """
        Repack the filesystem to move all files directly adjacent to each other and free space at the end of the file.
        """
        fst_file_list: "list[FSTFile]" = self.get_fst_file_list()
        fst_file_list.sort(key=lambda fst: fst.data_offset)
        data_offset = fst_file_list[0].data_offset

        for entry in fst_file_list:
            entry.data_offset = data_offset
            data_offset += entry.data_size

    def get_fst_list(self, start_directory: FSTDirectory = None) -> "list[FSTEntry]":
        """
        Get an in order list containing each file and directory
        """
        if start_directory is None:
            start_directory = self.root_directory

        fst_list = [start_directory]
        for child in start_directory.get_file_entries():
            if isinstance(child, FSTDirectory):
                fst_list = fst_list + self.get_fst_list(child)
            else:
                fst_list.append(child)
        return fst_list

    def get_fst_file_list(
        self, start_directory: FSTDirectory = None
    ) -> "list[FSTFile]":
        return list(
            filter(
                lambda fst: isinstance(fst, FSTFile), self.get_fst_list(start_directory)
            )
        )

    def get_fst_directory_list(self, start_directory: FSTDirectory = None):
        return filter(
            lambda fst: isinstance(fst, FSTDirectory),
            self.get_fst_list(start_directory),
        )

    def to_json_obj(self) -> dict:
        return self.root_directory.to_json_obj()

    def to_bytes(self) -> bytearray:
        fst_list = self.get_fst_list()

        # current name offset is now the total size of the string table
        fst_bin = MemoryStream()

        fst_list = self.get_fst_list()
        current_offset = 0
        for entry in fst_list:
            entry_bytes = entry.to_bytes()
            fst_bin.insert_into_stream(current_offset, entry_bytes)
            current_offset += self.TOCEntrySize

        for entry in fst_list:
            if isinstance(entry, FSTRootDirectory):
                continue
            fst_bin.insert_into_stream(current_offset, entry.filename.to_bytes())
            current_offset += len(entry.filename.to_bytes())

        return fst_bin.stream
