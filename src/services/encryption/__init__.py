import abc
from ... import AbstractFile, Stream


class EncryptionService(abc.ABC):
    """
    This class a defintion for services that provide encryption.

    """

    @abc.abstractmethod
    def encrypt(self, input_stream: Stream) -> Stream:
        """
        Apply an encryption algorithm to the input stream. Returns a new
        stream that represents the encrypted file.
        """

    @abc.abstractmethod
    def decrypt(self, input_stream: Stream) -> Stream:
        """
        Apply a decryption algorithm to the input stream. Returns a new
        stream that represents the decrypted file.
        """

    @abc.abstractmethod
    def get_method_name(self) -> str:
        """ """

encryption_services: "dict[str, EncryptionService]" = {}

class EncryptionServiceFactory:
    @staticmethod
    def register_encryption_method(service: EncryptionService):
        service_method = service.get_method_name()
        encryption_services[service_method] = service

    @staticmethod
    def encrypt_file(file: AbstractFile):
        write_stream = file.to_bytes()

        return_stream = write_stream
        if file.encryption_method in encryption_services:
            return_stream = encryption_services[file.encryption_method].encrypt(
                write_stream
            )

        return return_stream

    @staticmethod
    def decrypt_file(file: AbstractFile):
        read_stream = file.to_bytes()

        return_stream = read_stream
        if file.encryption_method in encryption_services:
            return_stream = encryption_services[file.encryption_method].decrypt(
                read_stream
            )

        return return_stream
