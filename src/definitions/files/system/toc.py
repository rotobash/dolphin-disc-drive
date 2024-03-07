from . import FSTDirectory, FSTRootDirectory, FSTFile, FSTEntry
from .. import EncodableFile, SerializableFile, Stream
from ...unicode import UnicodeString

class TableOfContents(SerializableFile, EncodableFile):
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
        self.fst_bin = fst_bin

        self.number_of_entries = self.fst_bin.get_int_at_offset(
            self.TOCNumberEntriesOffset
        )
        self.root_directory = FSTRootDirectory(self.number_of_entries)
        self._load_fst(self.root_directory)

    def _load_fst(self, root: FSTDirectory, first_entry_index: int = 1):
        """
        Walk the table of contents and load the directory tree.
        This function recursively calls itself to load sub-directories.
        """
        index = first_entry_index
        while index < root.next_offset:
            entryOffset = index * self.TOCEntrySize
            is_directory = self.fst_bin.get_byte_at_offset(entryOffset) != 0

            name_offset = self.fst_bin.get_int_at_offset(
                entryOffset
            ) & 0x00FFFFFF

            if is_directory:
                parent_entry = self.fst_bin.get_int_at_offset(entryOffset + 4)
                end_dir_entry = self.fst_bin.get_int_at_offset(entryOffset + 8)
                file_entry = FSTDirectory(name_offset, index, parent_entry, end_dir_entry)

                if index != 1:
                    file_entry.set_name(
                        self.fst_bin.get_string_at_offset(name_offset)
                    )
                else:
                    file_entry.set_name(UnicodeString("Root"))
                self._load_fst(file_entry, index + 1)
                index = end_dir_entry
            else:
                file_offset = self.fst_bin.get_int_at_offset(entryOffset + 4)
                file_size = self.fst_bin.get_int_at_offset(entryOffset + 8)

                file_entry = FSTFile(name_offset, index, file_offset, file_size)
                file_entry.set_name(
                    self.fst_bin.get_string_at_offset(name_offset)
                )
                index += 1

            root.add_child(file_entry)

    def get_file_name(self, fst_entry: FSTEntry) -> UnicodeString:
        """
        Given an FST entry, get it's file name.
        """
        return self.fst_bin.get_string_at_offset(
            fst_entry.name_offset
        )

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
                if self.get_file_name(child) == dir_name:
                    return child
                else:
                    candidate = self.search_directory_by_name(dir_name, child)
                    if candidate is not None:    
                        return candidate

    def add_file(self, fst_entry: FSTEntry, directory: FSTDirectory = None):
        self.update_fst_offsets()

    def remove_file(self, fst_entry: FSTEntry):
        self.update_fst_offsets()

    def update_fst_offsets(self):
        pass

    def to_json_obj(self) -> dict:
        return self.root_directory.to_json_obj()

    def to_bytes(self) -> bytearray:
        return super().to_bytes()
