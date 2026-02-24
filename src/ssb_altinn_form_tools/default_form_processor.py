import glob
import logging
import json
import requests

from pathlib import Path

import xmltodict

from .meta_form_processor import MetaFormProcessor
from .meta_form_extractor import MetaFormExtractor
from .meta_storage_connector import MetaStorageConnector
from .models import ExtractedForm, FormJsonData, CheckboxConfig, Checkboxmodel

logger = logging.getLogger(__name__)

def extract_arr_fields(json_data: dict, parent: str | None = None) -> list:
    array_items = []
    for key, value in json_data.items():
        if isinstance(value, dict):
            array_items.extend(extract_arr_fields(value, key))
        else:
            if value == "array":
                array_items.append(parent)
    return array_items

class DefaultFormProcessor(MetaFormProcessor):

    def __init__(
        self,
        form_name: str,
        form_base_path: str,
        extractor: MetaFormExtractor,
        connector: MetaStorageConnector,
        alias_mapping: dict[str, str] | None = None,
        checkbox_mapping: list[dict] | None = None,
        ra_version: None | int = None,
    ) -> None:
        self._extractor = extractor
        self._connector = connector
        self._form_base_path = form_base_path
        self._form_data_key = f"A3_{form_name}_M"
        self._alias_mapping = alias_mapping
        
        if checkbox_mapping:
            self._checkbox_mapping = [CheckboxConfig.model_validate(x) for x in checkbox_mapping]
        else:
            self._checkbox_mapping = checkbox_mapping
        
        ra_nummer = f"{form_name[:2]}-{form_name[2:]}A3"   # Eksempel: "RA-1234A3"
        version = ra_version if ra_version else 1          # Eksempel: 1 (numerisk)
        
        
        ra_base = ra_nummer.split("A3")[0]       # "RA-0848"
        ra_id = ra_base.replace("-", "").lower() # "ra0848"
        version_str = f"{version:02d}"           # "01"
        
        url = f"https://ssb.apps.altinn.no/ssb/{ra_id}-{version_str}/api/jsonschema/A3_{ra_base}_M"
        prod_res = requests.get(url)
        
        try:
            self.form_json = prod_res.json()
            self.array_fields = extract_arr_fields(self.form_json)
        except Exception as e:
            logger.warning("Fetching metadata for the form resulted in the following error. Possibly because metadata does not exist. Error: \n{e}")
            # Some forms does not have metadata in Altinn
            self.array_fields = None
            
    def _find_forms(self) -> list[str]:
        return glob.glob(f"{self._form_base_path}/**/**/**/**/*.xml")

    def _map_alias(self, mapping: dict[str, str], extracted_form: ExtractedForm):
        for idx, _ in enumerate(extracted_form.form_data):
            if extracted_form.form_data[idx].feltnavn in mapping:
                key = extracted_form.form_data[idx].feltnavn
                alias = mapping.get(key)
                if alias:
                    extracted_form.form_data[idx].alias = alias

    def _map_checkboxed(self, mapping: list[str], extracted_form: ExtractedForm):
        for idx, item in enumerate(extracted_form.form_data):
            if (item.feltnavn in mapping) and (item.verdi is not None):
                values = item.verdi.split(",")
                extracted_form.form_data[idx].verdi = json.dumps(values)

        return extracted_form

    def _postprocess_checkboxes(self, boxes: ExtractedForm, checkbox_mapping: list[CheckboxConfig]) -> list[Checkboxmodel]:
        results = []
        for checkbox in checkbox_mapping:
            for box in boxes.form_data:
                if checkbox.field_name == box.feltnavn.replace("/", ""):
                    checked = box.verdi.split(",")
                    for option in checkbox.options:
                        option_str = str(option)
                        results.append(Checkboxmodel(
                            field_name=checkbox.field_name,
                            option=option_str,
                            checked=option_str in checked,
                            field_path=box.feltsti,
                            aar=boxes.reception.aar,
                            skjema=boxes.reception.skjema,
                            ident=boxes.reception.ident,
                            refnr=boxes.reception.refnr,
                        ))
                
        return results
    
    def _process_form(
        self, xml_path: Path, json_data: FormJsonData
    ) -> ExtractedForm | None:
        is_new = self._connector.validate_form_is_new(json_data.altinn_reference)

        if is_new:
            xml_string = xml_path.read_text()
            dictionary: dict = xmltodict.parse(xml_string, force_list=self.array_fields)[self._form_data_key]
            extracted_form = self._extractor.extract_form(dictionary, json_data)

            if self._alias_mapping:
                self._map_alias(self._alias_mapping, extracted_form)

            if self._checkbox_mapping:
                checkboxes = self._postprocess_checkboxes(extracted_form, self._checkbox_mapping)
            else:
                checkboxes = []
                
            self._connector.begin_transaction()
            try:
                self._connector.insert_contact_info(extracted_form.contact_info)
                self._connector.insert_form_data(extracted_form.form_data)
                self._connector.insert_form_reception(extracted_form.reception)
                self._connector.insert_unit(extracted_form.unit)
                self._connector.insert_unit_info(extracted_form.unit_info)
                if self._checkbox_mapping:
                    self._connector.insert_checkboxes(checkboxes)
                    
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
