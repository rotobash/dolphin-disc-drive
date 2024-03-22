class UnicodeCharacter:
    def __init__(self, character_byte: int) -> None:
        self.char_byte = character_byte


class UnicodeString:
    def __init__(self, initial_string: "UnicodeString | str" = None) -> None:
        self.chars: "list[UnicodeCharacter]" = []
        if initial_string is not None:
            if isinstance(initial_string, UnicodeString):
                self.chars = [c for c in initial_string.chars]
            else:
                self.chars = [c.encode("unicode") for c in initial_string]

    def add_character(self, char: UnicodeCharacter):
        self.chars.append(char)

    def __str__(self) -> str:
        chars = []
        for c in self.chars:
            byte = c.char_byte.to_bytes(1, "big")
            try:
                chars.append(byte.decode())
            except UnicodeDecodeError:
                chars.append(byte.hex())
        return "".join(chars)

    def to_bytes(self):
        return bytearray([c.char_byte for c in self.chars] + [0])
