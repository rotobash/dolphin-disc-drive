from pathlib import Path
from typing import Literal
import unittest
from src.definitions.files.system import DOL, DOLSection
from src.definitions.files import MemoryStream
from . import PATH_TO_TEST_SYSTEM_FILES

class DOLTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with PATH_TO_TEST_SYSTEM_FILES.joinpath("main.dol").open("rb") as dol_file:
            cls._dol_bytes = MemoryStream(bytearray(dol_file.read()))
            dol_header = MemoryStream(cls._dol_bytes.get_bytes_at_offset(0, 0xFF))

            cls._dol_file = DOL(dol_header)
            cls._dol_file.load_section_contents(cls._dol_bytes)

    def test_init(self):
        self.assertEqual(
            len(self._dol_bytes.stream),
            self._dol_file.get_dol_size(),
            "Reported DOL size does not match original file.",
        )

        for section in self._dol_file.text_sections:
            self.assertLess(
                section.section_number,
                7,
                "Section number is to large for text section.",
            )
            self.dol_section_assert("text", section)

        for section in self._dol_file.data_sections:
            self.assertLess(
                section.section_number,
                11,
                "Section number is to large for data section.",
            )
            self.dol_section_assert("data", section)

    def test_to_bytes(self):
        encoded_dol = list(self._dol_file.to_bytes().stream)
        original_dol = list(self._dol_bytes.stream)
        self.assertListEqual(encoded_dol, original_dol, "Encoded DOL does not match orginal DOL")

    def dol_section_assert(self, type: "Literal['text', 'data']", section: DOLSection):
        self.assertIsNotNone(
            section.offset, f"Offset for {type}{section.section_number} wasn't loaded"
        )
        self.assertIsNotNone(
            section.size, f"Size for {type}{section.section_number} wasn't loaded"
        )
        self.assertIsNotNone(
            section.contents,
            f"Contents for {type}{section.section_number} weren't loaded",
        )

        self.assertLessEqual(
            section.offset + section.size, self._dol_file.get_dol_size()
        )
