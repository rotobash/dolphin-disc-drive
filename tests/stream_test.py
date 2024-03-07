from pathlib import Path
from typing import Literal
import unittest
from src.definitions.files.system import DOL, DOLSection
from src.definitions.files import MemoryStream
from . import PATH_TO_TEST_SYSTEM_FILES

class MemoryStreamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._stream = MemoryStream(bytearray(range(0xF)))

    def test_init(self):
        self.assertIsNotNone(self._stream.stream)
        self.assertGreater(self._stream.stream_size, 0)
        self.assertEqual(self._stream.stream_size, 0xF)
        self.assertListEqual(list(range(0xF)), list(self._stream.stream))

    def test_get_byte(self):
        self.assertEqual(self._stream.stream[0x8], self._stream.get_byte_at_offset(0x8))

    def test_get_bytes(self):        
        for byte in self._stream.get_bytes_at_offset(0x8, 3):
            self.assertEqual(self._stream.stream[byte], byte)

    def test_write_byte(self):
        self._stream.write_byte_at_offset(0x8, 0xF)
        self.assertEqual(self._stream.stream[0x8], 0xF)

    def test_write_bytes(self):
        self._stream.write_bytes_at_offset(0x8, [0xF, 0XF, 0XF])
        self.assertEqual(self._stream.stream[0x8], 0xF)
        self.assertEqual(self._stream.stream[0x9], 0xF)
        self.assertEqual(self._stream.stream[0xA], 0xF)