from ....definitions.files import StreamReader


class ISOStreamReader(StreamReader):
    def decompress(self):
        return