import abc
from ..serializable_file import SerializableFile, EncodableFile
from ...unicode import UnicodeString


class FSTEntry(SerializableFile, EncodableFile, abc.ABC):
    def __init__(self, name_offset: int, file_entry_index: int) -> None:
        self.name_offset = name_offset
        self.file_entry = file_entry_index
        self.filename = None

    def set_name(self, filename: UnicodeString):
        self.filename = filename

    def to_json_obj(self) -> dict:
        return {
            "file_entry_index": self.file_entry,
            "name_offset": self.name_offset,
            "filename": str(self.filename),
        }


class FSTFile(FSTEntry):
    def __init__(
        self, name_offset: int, file_entry_index: int, offset: int, size: int
    ) -> None:
        super().__init__(name_offset, file_entry_index)
        self.data_offset = offset
        self.data_size = size

        self.old_offset = offset
        self.old_size = size  # I don't think its necessary to track

    def to_json_obj(self) -> dict:
        return (
            super()
            .to_json_obj()
            .update(
                {
                    "is_directory": False,
                    "data_offset": self.data_offset,
                    "data_size": self.data_size,
                }
            )
        )

    def to_bytes(self) -> bytearray:
        file_entry = (
            [0]
            + self.name_offset.to_bytes(3, "big")
            + self.data_offset.to_bytes(4, "big")
            + self.data_size.to_bytes(4, "big")
        )
        return bytearray(file_entry)


class FSTDirectory(FSTEntry):
    def __init__(
        self,
        name_offset: int,
        file_entry_index: int,
        parent_entry: int,
        next_offset: int,
    ) -> None:
        super().__init__(name_offset, file_entry_index)
        self.parent_entry = parent_entry
        self.next_offset = next_offset
        self._children: "list[FSTEntry]" = []

    def add_child(self, entry: FSTEntry):
        self._children.append(entry)

    def get_end_entry(self):
        return self.file_entry + 1 + len(self._children)

    def search_file_by_index(self, file_entry: int) -> "FSTFile | None":
        for child in self._children:
            if isinstance(child, FSTDirectory):
                search = child.search_file_by_index(file_entry)
                if search != None:
                    return search
            elif child.file_entry == file_entry:
                return child
        return None

    def add_file(self, file_entry: FSTEntry):
        pass

    def remove_file(self, file_entry: FSTEntry):
        pass

    def to_json_obj(self) -> dict:
        return (
            super()
            .to_json_obj()
            .update(
                {
                    "is_directory": True,
                    "parent_entry": self.parent_entry,
                    "children": [c.to_json_obj() for c in self._children],
                }
            )
        )

    def to_bytes(self) -> bytearray:
        dir_entry = (
            [0]
            + self.name_offset.to_bytes(3, "big")
            + self.parent_entry.to_bytes(4, "big")
            + self.next_offset.to_bytes(4, "big")
        )
        return bytearray(dir_entry)


class FSTRootDirectory(FSTDirectory):
    def __init__(self, num_entries: int) -> None:
        super().__init__(0, 0, 0, num_entries)
        self.num_entries = num_entries
