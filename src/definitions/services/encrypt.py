import abc
from .. import AbstractFile, Stream


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


class EncryptionFactory:
    def __init__(self, encryption_services: "list[EncryptionService]") -> None:
        self.encryption_services: "dict[str, EncryptionService]" = {}
        for service in encryption_services:
            service_method = service.get_method_name()
            self.encryption_services[service_method] = service

    def encrypt_file(self, file: AbstractFile):
        write_stream = file.to_bytes()

        return_stream = write_stream
        if file.encryption_method in self.encryption_services:
            return_stream = self.encryption_services[file.encryption_method].encrypt(
                write_stream
            )

        return return_stream

    def decrypt_file(self, file: AbstractFile):
        read_stream = file.to_bytes()

        return_stream = read_stream
        if file.encryption_method in self.encryption_services:
            return_stream = self.encryption_services[file.encryption_method].decrypt(
                read_stream
            )

        return return_stream
