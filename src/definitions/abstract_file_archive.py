import abc
from enum import Enum
import json
from pathlib import Path
from typing import Iterable, Union

from src.definitions.stream import Stream

from . import AbstractFile


class AbstractFileArchive(abc.ABC):
    """
    Abstract class for reading files that are composed of other files (an archive).

    """

    def __init__(self, file_name: str, file_contents: Stream, compression_method: str = "none", encryption_method: str = "none") -> None:
        self.file_name = file_name
        self.file_contents = file_contents
        self.compression_method = compression_method
        self.encryption_method = encryption_method
        self.extracted_archive_files: "dict[str, AbstractFile]" = {}

    @abc.abstractmethod
    def get_file_list(self) -> "list[str]":
        """
        
        """

    @abc.abstractmethod
    def _extract_file(self, file_name: str) -> "AbstractFile":
        """
        
        """


    @abc.abstractmethod
    def get_archive_size(self):
        """
        
        """

    @abc.abstractmethod
    def build_archive(self, write_stream: Stream):
        """
        
        """

    @abc.abstractmethod
    def add_new_file(self, file: AbstractFile, parent_directory: str = None):
        if file.file_name not in self.extracted_archive_files:
            self.extracted_archive_files[file.file_name] = file

    @abc.abstractmethod
    def replace_file(self, file: AbstractFile):
        self.extracted_archive_files[file.file_name] = file

    @abc.abstractmethod
    def delete_file(self, file: AbstractFile):
        if file.file_name in self.extracted_archive_files:
            del self.extracted_archive_files[file.file_name]

    def open_file(self, file_name: str) -> AbstractFile:
        if file_name not in self.extracted_archive_files:
            self.extracted_archive_files[file_name] = self._extract_file(file_name)        
        
        return self.extracted_archive_files[file_name] 
    
    def open_files(self): 
        file_list = self.get_file_list()
        self.extracted_archive_files = dict(*[(f, self._extract_file(f)) for f in file_list])
        return self.extracted_archive_files

    def to_json_obj(self) -> dict:
        """
        Serialize this file into a JSON representation that easy for humans to parse.
        """
        return {"NotImplemented": self.file_name}

    def __str__(self) -> str:
        return json.dumps(self.to_json_obj())

    def get_file_type(self) -> str:
        return self.file_name.rsplit(".")[-1]