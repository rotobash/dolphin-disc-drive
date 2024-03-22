from ... import AbstractFile, Stream

GamecodeOffset = 0x0001
CountyCodeOffset = 0x0003
MakerOffset = 0x0004
DiskIDOffset = 0x0006
VersionOffset = 0x0007
GameNameOffset = 0x0020
DOLOffset = 0x0420
FSTOffset = 0x0424
SizeOfFSTOffset = 0x0428
MaxSizeOfFSTOffset = 0x042C


class DiscHeader(AbstractFile):
    def __init__(self, app_header: Stream) -> None:
        super().__init__("boot.bin", app_header)
        self.game_code = app_header.get_bytes_at_offset(GamecodeOffset, 2)
        self.country_code = app_header.get_byte_at_offset(CountyCodeOffset)
        self.maker_id = app_header.get_bytes_at_offset(MakerOffset, 2)
        self.disk_id = app_header.get_byte_at_offset(DiskIDOffset)
        self.version = app_header.get_byte_at_offset(VersionOffset)
        self.game_name = app_header.get_string_at_offset(GameNameOffset)

        self.dol_offset = app_header.get_int_at_offset(DOLOffset)
        self.fst_offset = app_header.get_int_at_offset(FSTOffset)
        self.fst_size = app_header.get_int_at_offset(SizeOfFSTOffset)
        self.fst_max_size = app_header.get_int_at_offset(MaxSizeOfFSTOffset)

    def to_json_obj(self) -> dict:
        return {
            "game_code": bytes(self.game_code).hex(),
            "country_code": self.country_code,
            "maker_id": self.maker_id.hex(),
            "disk_id": self.disk_id,
            "version": self.version,
            "game_name": str(self.game_name),
            "dol_offset": self.dol_offset.to_bytes(4, "big").hex(),
            "fst_offset": self.fst_offset.to_bytes(4, "big").hex(),
            "fst_size": self.fst_size,
            "fst_max_size": self.fst_max_size,
        }
