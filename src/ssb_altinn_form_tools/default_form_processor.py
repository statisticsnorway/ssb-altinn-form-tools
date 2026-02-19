import glob
import logging
from pathlib import Path

import xmltodict

from .meta_form_processor import MetaFormProcessor
from .meta_form_extractor import MetaFormExtractor
from .meta_storage_connector import MetaStorageConnector
from .models import ExtractedForm, FormJsonData

logger = logging.getLogger(__name__)


class DefaultFormProcessor(MetaFormProcessor):

    def __init__(
        self,
        form_name: str,
        form_base_path: str,
        extractor: MetaFormExtractor,
        connector: MetaStorageConnector,
        alias_mapping: dict[str, str] | None = None,
    ) -> None:
        self._extractor = extractor
        self._connector = connector
        self._form_base_path = form_base_path
        self._form_data_key = f"A3_{form_name}_M"
        self._alias_mapping = alias_mapping

    def _find_forms(self) -> list[str]:
        return glob.glob(f"{self._form_base_path}/**/**/**/**/*.xml")

    def _map_alias(self, mapping: dict[str, str], extracted_form: ExtractedForm):
        for idx, _ in enumerate(extracted_form.form_data):
            if extracted_form.form_data[idx].feltnavn in mapping:
                key = extracted_form.form_data[idx].feltnavn
                alias = mapping.get(key)
                if alias:
                    extracted_form.form_data[idx].alias = alias

    def _process_form(
        self, xml_path: Path, json_data: FormJsonData
    ) -> ExtractedForm | None:
        is_new = self._connector.validate_form_is_new(json_data.altinn_reference)

        if is_new:
            xml_string = xml_path.read_text()
            dictionary: dict = xmltodict.parse(xml_string)[self._form_data_key]
            extracted_form = self._extractor.extract_form(dictionary, json_data)

            if self._alias_mapping:
                self._map_alias(self._alias_mapping, extracted_form)

            self._connector.begin_transaction()
            try:
                self._connector.insert_contact_info(extracted_form.contact_info)
                self._connector.insert_form_data(extracted_form.form_data)
                self._connector.insert_form_reception(extracted_form.reception)
                self._connector.insert_unit(extracted_form.unit)
                self._connector.insert_unit_info(extracted_form.unit_info)
            except Exception as e:
                self._connector.rollback(json_data.altinn_reference)
                logger.error(e)
                logger.error("Due to the previous error the insert was rolled back")
            else:
                self._connector.commit()
                logger.info(
                    f"Form {json_data.altinn_reference} was inserted into the database"
                )
                logger.debug(f"Data: {extracted_form}")
        else:
            logger.info(
                f"Skipped inserting form with refernce {json_data.altinn_reference} since it already exists"
            )

    def _process_forms(self, forms: list[str]) -> None:
        for form in forms:
            file_path = Path(form)

            json_name = file_path.name.replace("xml", "json").replace("form", "meta")
            json_path = file_path.with_name(json_name)
            json_data = FormJsonData.model_validate_json(json_path.read_text())
            self._process_form(file_path, json_data)

    def process_new_forms(self) -> None:
        logger.debug(f"Begin processing {self._form_data_key} forms")
        forms = self._find_forms()
        if not forms:
            logger.warning("No forms found")
        self._connector.create_tables_if_not_exists()
        self._process_forms(forms)
