from ... import AbstractFile, Serializable, Stream, MemoryStream


class DOLSection(Serializable):
    def __init__(
        self, section_number: int, offset: int, load_address: int, size: int
    ) -> None:
        self.section_number = section_number
        self.offset = offset
        self.load_address = load_address
        self.size = size
        self.contents = None

    def load_contents(self, section_bytes: bytearray):
        self.contents = section_bytes

    def to_json_obj(self) -> dict:
        return {
            "section_number": self.section_number,
            "offset": self.offset.to_bytes(4, "big").hex(),
            "load_address": self.load_address.to_bytes(4, "big").hex(),
            "contents": self.contents.hex(),
        }


class DOLDataSection(DOLSection):
    pass


class DOLTextSection(DOLSection):
    pass


TextSectionStartOffset = 0x00
DataSectionStartOffset = 0x1C
TextAddressStartOffset = 0x48
DataAddressStartOffset = 0x64
TextSizeStartOffset = 0x90
DataSizeStartOffset = 0xAC
BSSAddressOffset = 0xD8
BSSSizeOffset = 0xDC
EntryPointOffset = 0xE0


class DOL(AbstractFile):
    """
    A DOL is an executable file used by the Gamecube.
    The app loader that executes when a disc is booted loads main.dol into memory given
    the offsets and jumps to the entry point stated by the DOL.
    """

    def __init__(self, header_bytes: Stream) -> None:
        super().__init__("main.dol", header_bytes)
        self.text_sections: "list[DOLTextSection]" = []
        self.data_sections: "list[DOLDataSection]" = []

        self.bss_address = header_bytes.get_int_at_offset(BSSAddressOffset)
        self.bss_size = header_bytes.get_int_at_offset(BSSSizeOffset)
        self.entry_point = header_bytes.get_int_at_offset(EntryPointOffset)

        for i in range(7):
            offset = header_bytes.get_int_at_offset(TextSectionStartOffset + (i * 4))
            load_address = header_bytes.get_int_at_offset(
                TextAddressStartOffset + (i * 4)
            )
            size = header_bytes.get_int_at_offset(TextSizeStartOffset + (i * 4))
            section = DOLTextSection(i, offset, load_address, size)
            self.text_sections.append(section)

        for i in range(11):
            offset = header_bytes.get_int_at_offset(DataSectionStartOffset + (i * 4))
            load_address = header_bytes.get_int_at_offset(
                DataAddressStartOffset + (i * 4)
            )
            size = header_bytes.get_int_at_offset(DataSizeStartOffset + (i * 4))
            section = DOLDataSection(i, offset, load_address, size)
            self.data_sections.append(section)

    def get_dol_size(self):
        size = 0xFF
        for section in self.text_sections:
            size += section.size

        for section in self.data_sections:
            size += section.size

        return size + 1

    def load_section_contents(self, dol_bytes: Stream):
        for section in self.text_sections:
            section.load_contents(
                dol_bytes.get_bytes_at_offset(section.offset, section.size)
            )

        for section in self.data_sections:
            section.load_contents(
                dol_bytes.get_bytes_at_offset(section.offset, section.size)
            )

    def to_json_obj(self) -> dict:
        return {
            "text_sections": [section.to_json_obj() for section in self.text_sections],
            "data_sections": [section.to_json_obj() for section in self.data_sections],
            "bss_offset": self.bss_address.to_bytes(4, "big").hex(),
            "bss_size": self.bss_size,
            "entry_point": self.entry_point.to_bytes(4, "big").hex(),
        }

    def to_bytes(self) -> bytearray:
        dol_file = MemoryStream(bytearray([0] * self.get_dol_size()))
        for i in range(7):
            section = self.text_sections[i]
            dol_file.write_int_at_offset(
                TextSectionStartOffset + (i * 4), section.offset
            )
            dol_file.write_int_at_offset(
                TextAddressStartOffset + (i * 4), section.load_address
            )
            dol_file.write_int_at_offset(TextSizeStartOffset + (i * 4), section.size)
            dol_file.write_bytes_at_offset(section.offset, section.contents)

        for i in range(11):
            section = self.data_sections[i]
            dol_file.write_int_at_offset(
                DataSectionStartOffset + (i * 4), section.offset
            )
            dol_file.write_int_at_offset(
                DataAddressStartOffset + (i * 4), section.load_address
            )
            dol_file.write_int_at_offset(DataSizeStartOffset + (i * 4), section.size)
            dol_file.write_bytes_at_offset(section.offset, section.contents)

        dol_file.write_int_at_offset(BSSAddressOffset, self.bss_address)
        dol_file.write_int_at_offset(BSSSizeOffset, self.bss_size)
        dol_file.write_int_at_offset(EntryPointOffset, self.entry_point)

        return dol_file.stream

    def _adjust_layout(self):
        """
        Goes through each DOL section and makes sure the offset + size < the next section's offset.
        If this is not the case, adjust it (and all others). Not implemented, unsure how useful adding/deleting bytes
        to any section is.
        """
        pass
