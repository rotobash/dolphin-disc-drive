import unittest
from src.definitions import MemoryStream


class MemoryStreamTest(unittest.TestCase):
    """
    This class contains tests for the MemoryStream class.
    A MemoryStream is an in memory buffer of the file we're referencing.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._stream = MemoryStream(bytearray(range(0xF)))

    def test_init(self):
        """
        Test that the memory stream was created succesfully.
        This means that the stream is saved, the size is updated,
        and the stream data is what we expect (i.e. stream[i] = i)
        """
        self.assertIsNotNone(self._stream.stream)
        self.assertGreater(self._stream.stream_size, 0)
        self.assertEqual(self._stream.stream_size, 0xF)
        self.assertListEqual(list(range(0xF)), list(self._stream.stream))

    def test_get_byte(self):
        """
        Test getting a single byte from the test stream.
        """
        self.assertEqual(self._stream.stream[0x8], self._stream.get_byte_at_offset(0x8))

    def test_get_bytes(self):
        """
        Test getting multiple bytes from the test stream.
        """
        for byte in self._stream.get_bytes_at_offset(0x8, 3):
            self.assertEqual(self._stream.stream[byte], byte)

    def test_write_byte(self):
        """
        Test writing a byte to the test stream.
        """
        self._stream.write_byte_at_offset(0x8, 0xF)
        self.assertEqual(self._stream.stream[0x8], 0xF)

    def test_write_bytes(self):
        """
        Test writing multiple bytes to the test stream.
        """
        self._stream.write_bytes_at_offset(0x8, [0xF, 0xF, 0xF])
        self.assertEqual(self._stream.stream[0x8], 0xF)
        self.assertEqual(self._stream.stream[0x9], 0xF)
        self.assertEqual(self._stream.stream[0xA], 0xF)
