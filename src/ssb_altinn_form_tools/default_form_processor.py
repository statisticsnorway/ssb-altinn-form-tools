from .meta_form_processor import MetaFormProcessor
from .meta_form_extractor import MetaFormExtractor
from .meta_storage_connector import MetaStorageConnector


class DefaultFormProcessor(MetaFormProcessor):

    def __init__(
        self, extractor: MetaFormExtractor, connector: MetaStorageConnector
    ) -> None:
        self._extractor = extractor
        self._connector = connector

    def _process_form(self):
        return None

    def _process_forms(self):
        return None

    def process_new_forms(self):
        return None