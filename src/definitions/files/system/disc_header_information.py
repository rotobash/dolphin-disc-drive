from ... import MemoryStream, AbstractFile


class DiscHeaderInformation(AbstractFile):
    def __init__(self, bi2_bin: MemoryStream) -> None:
        super().__init__("bi2.bin", bi2_bin)
