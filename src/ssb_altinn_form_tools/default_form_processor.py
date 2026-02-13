import glob
import logging

from pathlib import Path

import xmltodict

from .meta_form_processor import MetaFormProcessor
from .meta_form_extractor import MetaFormExtractor
from .meta_storage_connector import MetaStorageConnector
from .models import FormJsonData

logger = logging.getLogger(__name__)

class DefaultFormProcessor(MetaFormProcessor):

    def __init__(
        self,
        form_name: str,
        form_base_path: str,
        extractor: MetaFormExtractor,
        connector: MetaStorageConnector,
    ) -> None:
        self._extractor = extractor
        self._connector = connector
        self._form_base_path = form_base_path
        self._form_data_key = f"A3_{form_name}_M"

    def _find_forms(self) -> list[str]:
        return glob.glob(f"{self._form_base_path}/**/**/**/**/*.xml")

    def _process_form(self, xml_path: Path, json_data: FormJsonData):
        is_new = self._connector.validate_form_is_new(json_data.altinn_reference)

        if is_new:
            xml_string = xml_path.read_text()
            dictionary: dict = xmltodict.parse(xml_string)[self._form_data_key]
            (form_reception, contact_info, unit, unit_info, form_data) = (
                self._extractor.extract_form(dictionary, json_data)
            )
            self._connector.begin_transaction()
            try:
                self._connector.insert_contact_info(contact_info)
                self._connector.insert_form_data(form_data)
                self._connector.insert_form_reception(form_reception)
                self._connector.insert_unit(unit)
                self._connector.insert_unit_info(unit_info)
            except Exception as e:
                self._connector.rollback(json_data.altinn_reference)
                logger.error(e)
                logger.error("Due to the previous error the insert was rolled back")
            finally:
                self._connector.commit()
                logger.info(f"Form {json_data.altinn_reference} was inserted into the database")
                
    def _process_forms(self, forms: list[str]):
        for form in forms:
            file_path = Path(form)

            json_name = file_path.name.replace("xml", "json").replace("form", "meta")
            json_path = file_path.with_name(json_name)
            json_data = FormJsonData.model_validate_json(json_path.read_text())
            self._process_form(file_path, json_data)

    def process_new_forms(self):
        forms = self._find_forms()
        self._connector.create_tables_if_not_exists()
        self._process_forms(forms)
