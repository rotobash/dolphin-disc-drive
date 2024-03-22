import abc

from .. import AbstractFile, Stream


class CompressionService(abc.ABC):
    """
    This class a defintion for services that provide compression.

    """

    @abc.abstractmethod
    def compress(self, input_stream: Stream) -> Stream:
        """
        Apply a compression algorithm to the input stream. Returns a new
        stream that represents the compressed file.
        """

    @abc.abstractmethod
    def decompress(self, input_stream: Stream) -> Stream:
        """
        Apply a decompression algorithm to the input stream. Returns a new
        stream that represents the compressed file.
        """

    @abc.abstractmethod
    def get_method_name(self) -> str:
        """ """


class CompressionFactory:
    def __init__(self, compression_services: "list[CompressionService]") -> None:
        self.compression_services: "dict[str, CompressionService]" = {}
        for service in compression_services:
            service_method = service.get_method_name()
            self.compression_services[service_method] = service

    def compress_file(self, file: AbstractFile):
        write_stream = file.to_bytes()

        return_stream = write_stream
        if file.compression_method in self.compression_services:
            return_stream = self.compression_services[file.compression_method].compress(
                write_stream
            )

        return return_stream

    def decompress_file(self, file: AbstractFile):
        read_stream = file.to_bytes()

        return_stream = read_stream
        if file.compression_method in self.compression_services:
            return_stream = self.compression_services[
                file.compression_method
            ].decompress(read_stream)

        return return_stream
