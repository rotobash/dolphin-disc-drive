import abc

from ... import AbstractFile, Stream

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


compression_services: "dict[str, CompressionService]" = {}

class CompressionServiceFactory:
    @staticmethod
    def register_compression_method(service: CompressionService):
        service_method = service.get_method_name()
        compression_services[service_method] = service

    @staticmethod
    def compress_file(file: AbstractFile):
        write_stream = file.to_bytes()

        return_stream = write_stream
        if file.compression_method in compression_services:
            return_stream = compression_services[file.compression_method].compress(
                write_stream
            )

        return return_stream

    @staticmethod
    def decompress_file(file: AbstractFile):
        read_stream = file.to_bytes()

        return_stream = read_stream
        if file.compression_method in compression_services:
            return_stream = compression_services[
                file.compression_method
            ].decompress(read_stream)

        return return_stream
    
# register methods