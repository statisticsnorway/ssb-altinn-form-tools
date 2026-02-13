from abc import ABC
from abc import abstractmethod

from .meta_form_extractor import MetaFormExtractor
from .meta_storage_connector import MetaStorageConnector

class MetaFormProcessor(ABC):

    @abstractmethod
    def __init__(self, extractor: MetaFormExtractor, connector: MetaStorageConnector) -> None:
        super().__init__()

    @abstractmethod
    def _process_form(self):
        ...

    @abstractmethod
    def _process_forms(self):
        ...
    
    @abstractmethod
    def process_new_forms(self):
        ...