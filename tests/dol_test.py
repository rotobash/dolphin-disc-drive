import unittest
from typing_extensions import Literal
from src.definitions.files.system import DOL, DOLSection
from src.definitions import MemoryStream
from .constants import PATH_TO_TEST_SYSTEM_FILES


class DOLTest(unittest.TestCase):
    """
    This class contains tests for the DOL file wrapper class.
    """

    @classmethod
    def setUpClass(cls) -> None:
        with PATH_TO_TEST_SYSTEM_FILES.joinpath("main.dol").open("rb") as dol_file:
            cls._dol_bytes = MemoryStream(bytearray(dol_file.read()))
            dol_header = MemoryStream(cls._dol_bytes.get_bytes_at_offset(0, 0xFF))

            cls._dol_file = DOL(dol_header)
            cls._dol_file.load_section_contents(cls._dol_bytes)

    def test_init(self):
        """
        Test creating a DOL file from a known good one.
        Assert that all sections are loaded and valid.
        """
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
        """
        Assert that DOL's to_bytes method produces the same file we loaded.
        """
        encoded_dol = list(self._dol_file.to_bytes().stream)
        original_dol = list(self._dol_bytes.stream)
        self.assertListEqual(
            encoded_dol, original_dol, "Encoded DOL does not match orginal DOL"
        )

    def dol_section_assert(
        self, section_type: "Literal['text', 'data']", section: DOLSection
    ):
        """
        Assert that a DOL data/text section contains valid data.
        """
        self.assertIsNotNone(
            section.offset,
            f"Offset for {section_type}{section.section_number} wasn't loaded",
        )
        self.assertIsNotNone(
            section.size,
            f"Size for {section_type}{section.section_number} wasn't loaded",
        )
        self.assertIsNotNone(
            section.contents,
            f"Contents for {section_type}{section.section_number} weren't loaded",
        )

        self.assertLessEqual(
            section.offset + section.size, self._dol_file.get_dol_size()
        )
