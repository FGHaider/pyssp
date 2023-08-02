import os
import tempfile
from pathlib import Path, PosixPath
from abc import ABC, abstractmethod

import xmlschema
from lxml import etree as ET


def register_namespaces():
    ssp_standards = SSPStandard
    for name, url in ssp_standards.namespaces.items():
        ET.register_namespace(name, url)


class SSPStandard:
    namespaces = {'ssc': 'http://ssp-standard.org/SSP1/SystemStructureCommon',
                  'ssv': 'http://ssp-standard.org/SSP1/SystemStructureParameterValues',
                  'ssb': 'http://ssp-standard.org/SSP1/SystemStructureSignalDictionary',
                  'ssm': 'http://ssp-standard.org/SSP1/SystemStructureParameterMapping',
                  'ssd': 'http://ssp-standard.org/SSP1/SystemStructureDescription'}

    __resource_path = Path(__file__).parent / 'resources'
    schemas = {'ssc': __resource_path / 'SystemStructureCommon.xsd',
               'ssd': __resource_path / 'SystemStructureDescription.xsd',
               'ssd11': __resource_path / 'SystemStructureDescription11.xsd',
               'ssm': __resource_path / 'SystemStructureParameterMapping.xsd',
               'ssv': __resource_path / 'SystemStructureParameterValues.xsd',
               'ssb': __resource_path / 'SystemStructureSignalDictionary.xsd'}


class SSPFile(ABC, SSPStandard):

    @abstractmethod
    def __read__(self):
        pass

    @abstractmethod
    def __write__(self):
        pass

    def __check_compliance__(self):
        if self.__mode in ['a', 'w']:  # Temporary file creation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = temp_dir + 'tmp.xml'
                self.__write__()
                xml_string = ET.tostring(self.root, pretty_print=True, encoding='utf-8', xml_declaration=True)
                with open(temp_file_path, 'wb') as file:
                    file.write(xml_string)
                xmlschema.validate(temp_file_path, self.schemas[self.identifier], namespaces=self.namespaces)
        else:
            xmlschema.validate(self.file_path, self.schemas[self.identifier], namespaces=self.namespaces)

    @property
    def file_path(self):
        return self.__file_path

    @property
    def identifier(self):
        return self.__identifier

    def __init__(self, file_path, mode='r', identifier='unknown'):
        self.__mode = mode
        if type(file_path) is not PosixPath:
            file_path = Path(file_path)
        self.__file_path = file_path
        self.__identifier = identifier

        self.__tree = None
        self.root = None

        if mode == 'r' or mode == 'a':
            self.__read__()

    def __save__(self):
        xml_string = ET.tostring(self.root, pretty_print=True, encoding='utf-8', xml_declaration=True)
        with open(self.__file_path, 'wb') as file:
            file.write(xml_string)

    def __enter__(self):
        register_namespaces()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__mode in ['w', 'a']:
            self.__write__()
            self.__save__()

class SSPElement(ABC):

    @abstractmethod
    def to_element(self) -> ET.Element:
        pass

    @abstractmethod
    def from_element(self, element: ET.Element):
        pass


class EmptyElement(ET.ElementBase):

    def __init__(self, tag, attrib=None, **kwargs):
        super().__init__(tag, attrib, **kwargs)

    def __repr__(self):
        return ET.tostring(self, encoding='utf-8')
