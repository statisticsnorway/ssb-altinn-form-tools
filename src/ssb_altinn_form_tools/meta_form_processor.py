from abc import ABC
from abc import abstractmethod
from pathlib import Path

from .models import ExtractedForm, FormJsonData, CheckboxConfig, Checkboxmodel
from .meta_form_extractor import MetaFormExtractor
from .meta_storage_connector import MetaStorageConnector


class MetaFormProcessor(ABC):

    @abstractmethod
    def __init__(
        self, extractor: MetaFormExtractor, connector: MetaStorageConnector
    ) -> None:
        super().__init__()

    @abstractmethod
    def _find_forms(self): ...

    @abstractmethod
    def _process_form(
        self,
        xml_path: Path,
        json_data: FormJsonData,
    ) -> None: ...

    @abstractmethod
    def _process_forms(self, forms: list[str]) -> None: ...

    @abstractmethod
    def _postprocess_checkboxes(self, boxes: ExtractedForm, checkbox_mapping: list[CheckboxConfig]) -> list[Checkboxmodel]:
        raise NotImplementedError(f"{self} does not implement the '_postprocess_checkboxes' method and does not support custom handling of checkboxes")

    @abstractmethod
    def process_new_forms(self) -> None: ...
