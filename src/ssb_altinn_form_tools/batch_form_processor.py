import glob
import json
import logging
from pathlib import Path

import pendulum
import requests
import xmltodict

from ssb_altinn_form_tools.meta_form_extractor import MetaFormExtractor
from ssb_altinn_form_tools.meta_form_processor import MetaFormProcessor
from ssb_altinn_form_tools.meta_storage_connector import MetaStorageConnector
from ssb_altinn_form_tools.models import CheckboxConfig
from ssb_altinn_form_tools.models import Checkboxmodel
from ssb_altinn_form_tools.models import ExtractedForm
from ssb_altinn_form_tools.models import FormJsonData

logger = logging.getLogger(__name__)


def extract_arr_fields(json_data: dict, parent: str | None = None) -> list:
    """Extract names of fields that are arrays.

    A function that traverses a dictionary recursivly to extract the name of fields that are arrays.
    """
    array_items = []
    for key, value in json_data.items():
        if isinstance(value, dict):
            array_items.extend(extract_arr_fields(value, key))
        else:
            if value == "array":
                array_items.append(parent)
    return array_items


class BatchFormProcessor(MetaFormProcessor):
    """Default processor for scanning, extracting, and persisting forms.

    This processor locates XML form files on disk, parses them into dictionaries,
    extracts structured models via a `MetaFormExtractor`, optionally applies
    alias and checkbox mapping, and persists the results through a
    `MetaStorageConnector` using transactional semantics.
    """

    def __init__(
        self,
        form_name: str,
        form_base_path: str,
        extractor: MetaFormExtractor,
        connector: MetaStorageConnector,
        alias_mapping: dict[str, str] | None = None,
        checkbox_mapping: list[dict] | None = None,
        ra_version: None | int = None,
        alternative_glob_path: None | str = None,
    ) -> None:
        """Initializes the default form processor.

        Args:
            form_name (str): Canonical form name used to build the top-level XML key.
            form_base_path (str): Base directory where XML form files reside.
            extractor (MetaFormExtractor): Extractor that converts parsed XML
                dictionaries to domain models.
            connector (MetaStorageConnector): Storage connector for validating and
                inserting extracted data.
            alias_mapping (dict[str, str] | None): Optional mapping from field
                names (``feltnavn``) to user-friendly aliases to be set on each
                corresponding `FormData` entry.
            checkbox_mapping (list[str] | None): Optional list of field names that
                represent multi-select values encoded as comma-separated strings.
                These will be normalized to JSON arrays.
            ra_version (str | None): An optional argument denoting which data-version
                of the form to use. This is automatically set to 1 if no argument is
                provided.
            alternative_glob_path (str | None): Globbable path to all forms. Eg. '/**/*.xml'.
                We try to automatically discover forms based on the standard directory structure
                provided by team suv. If you another directory structure, this argument can be set.
        """
        self._extractor = extractor
        self._connector = connector
        self._form_base_path = form_base_path
        self._form_data_key = f"A3_{form_name}_M"
        self._alias_mapping = alias_mapping
        self._glob_path = (
            alternative_glob_path
            if alternative_glob_path
            else f"{self._form_base_path}/**/**/**/**/*.xml"
        )

        if checkbox_mapping:
            self._checkbox_mapping = [
                CheckboxConfig.model_validate(x) for x in checkbox_mapping
            ]
        else:
            self._checkbox_mapping = None

        ra_nummer = f"{form_name[:2]}-{form_name[2:]}A3"  # Eksempel: "RA-1234A3"
        version = ra_version if ra_version else 1  # Eksempel: 1 (numerisk)

        ra_base = ra_nummer.split("A3")[0]  # "RA-0848"
        ra_id = ra_base.replace("-", "").lower()  # "ra0848"
        version_str = f"{version:02d}"  # "01"

        url = f"https://ssb.apps.altinn.no/ssb/{ra_id}-{version_str}/api/jsonschema/A3_{ra_base}_M"
        prod_res = requests.get(url)

        try:
            self.form_json = prod_res.json()
            self.array_fields = extract_arr_fields(self.form_json)
        except Exception as e:
            logger.warning(
                f"Fetching metadata for the form resulted in the following error. Possibly because metadata does not exist. Error: \n{e}"
            )
            # Some forms does not have metadata in Altinn
            self.array_fields = None

    def _find_forms(self) -> list[str]:
        """Finds XML forms recursively under the configured base path.

        Returns:
            list[str]: A list of file paths to XML form files discovered
            within the base directory (searched recursively).
        """
        return glob.glob(self._glob_path)

    def _map_alias(self, mapping: dict[str, str], extracted_form: ExtractedForm):
        """Applies alias mapping to `ExtractedForm.form_data` in place.

        Each `FormData` entry whose ``feltnavn`` matches a key in `mapping` will
        have its `alias` set to the corresponding mapped string.

        Args:
            mapping (dict[str, str]): Mapping from original field names to aliases.
            extracted_form (ExtractedForm): The extracted form whose `form_data`
                list will be updated.

        Side Effects:
            Mutates `extracted_form.form_data` by setting the `alias` field where
            applicable.
        """
        for idx, _ in enumerate(extracted_form.form_data):
            if extracted_form.form_data[idx].feltnavn in mapping:
                key = extracted_form.form_data[idx].feltnavn
                alias = mapping.get(key)
                if alias:
                    extracted_form.form_data[idx].alias = alias

    def _map_checkboxed(self, mapping: list[str], extracted_form: ExtractedForm):
        """Normalizes checkbox-like fields to JSON arrays.

        For each `FormData` entry where ``feltnavn`` appears in `mapping` and
        ``verdi`` is non-empty, the comma-separated string is split into a list and
        serialized to JSON (i.e., `["a", "b", ...]`), which replaces the original
        `verdi`.

        Args:
            mapping (list[str]): Field names (``feltnavn``) to treat as multi-select.
            extracted_form (ExtractedForm): The extracted form to transform.

        Returns:
            ExtractedForm: The same `extracted_form` instance, returned for chaining.

        Side Effects:
            Mutates `extracted_form.form_data[idx].verdi` for matched fields by
            converting comma-separated strings to JSON arrays.
        """
        for idx, item in enumerate(extracted_form.form_data):
            if (item.feltnavn in mapping) and (item.verdi is not None):
                values = item.verdi.split(",")
                extracted_form.form_data[idx].verdi = json.dumps(values)

        return extracted_form

    def _postprocess_checkboxes(
        self, boxes: ExtractedForm, checkbox_mapping: list[CheckboxConfig]
    ) -> list[Checkboxmodel]:
        results = []
        for checkbox in checkbox_mapping:
            for box in boxes.form_data:
                if checkbox.field_name == box.feltnavn.replace("/", ""):
                    checked = box.verdi.split(",") if box.verdi else []
                    for option in checkbox.options:
                        option_str = str(option)
                        results.append(
                            Checkboxmodel(
                                field_name=checkbox.field_name,
                                option=option_str,
                                checked=option_str in checked,
                                field_path=box.feltsti,
                                aar=boxes.reception.aar,
                                skjema=boxes.reception.skjema,
                                ident=boxes.reception.ident,
                                refnr=boxes.reception.refnr,
                                delreg=boxes.reception.delreg,
                            )
                        )

        return results

    def _process_form(
        self, xml_path: Path, json_data: FormJsonData
    ) -> tuple[ExtractedForm | None, list[Checkboxmodel] | None]:
        """Parses, extracts, transforms, and persists a single form if it is new.

        The method checks if a form (by `altinn_reference`) is new via the
        connector. If new, it:
          1. Reads and parses the XML.
          2. Extracts domain models using the configured extractor.
          3. Applies alias and checkbox mappings, if configured.
          4. Inserts data using a transaction (contact info, form data, reception,
             unit, unit info). On failure, the transaction is rolled back.

        Args:
            xml_path (Path): Path to the XML form file.
            json_data (FormJsonData): Supplemental JSON metadata for the form.

        Returns:
            ExtractedForm | None: The extracted form if it was processed and
            inserted; otherwise `None` when the form is not new.

        Raises:
            xmltodict.expat.ExpatError: If the XML is malformed and cannot be parsed.
            KeyError: If the expected top-level key (e.g., `_form_data_key`) is
                missing from the parsed XML dictionary.

        Logging:
            - Logs an info message when the form is inserted or skipped.
            - Logs debug details of the extracted data upon successful commit.
            - Logs errors and emits a rollback notice if an exception occurs.
        """
        is_new = self._connector.validate_form_is_new(json_data.altinn_reference)

        if is_new:
            xml_string = xml_path.read_text()
            dictionary: dict = xmltodict.parse(
                xml_string, force_list=self.array_fields
            )[self._form_data_key]
            extracted_form = self._extractor.extract_form(dictionary, json_data)

            if self._alias_mapping:
                self._map_alias(self._alias_mapping, extracted_form)

            if self._checkbox_mapping:
                checkboxes = self._postprocess_checkboxes(
                    extracted_form, self._checkbox_mapping
                )
            else:
                checkboxes = []

            return extracted_form, checkboxes
        else:
            logger.info(
                f"Skipped inserting form with refernce {json_data.altinn_reference} since it already exists"
            )
            return None, None

    def _process_forms(
        self,
        forms: list[str],
        start_dt: pendulum.DateTime | None = None,
        end_dt: pendulum.DateTime | None = None,
    ) -> None:
        """Processes a collection of form file paths.

        For each XML path, this method derives the corresponding JSON metadata
        file (by replacing suffixes), validates the JSON, and then processes
        the form via `_process_form`.

        Args:
            forms (list[str]): List of XML file paths to process.
            start_dt (pendulum.DateTime | None): Start for processing.
            end_dt (pendulum.DateTime | None): End for processing.

        Raises:
            FileNotFoundError: If the derived JSON metadata file does not exist.
            pydantic.ValidationError: If `FormJsonData` validation fails.
        """
        forms_list: list[ExtractedForm] = []
        checkboxes_list = []
        for form in forms:
            file_path = Path(form)

            json_name = file_path.name.replace("xml", "json").replace("form", "meta")
            json_path = file_path.with_name(json_name)
            json_data = FormJsonData.model_validate_json(json_path.read_text())
            if start_dt and end_dt:
                delivered_date = pendulum.instance(json_data.date_deliveres)
                if start_dt < delivered_date < end_dt:
                    extracted_form, checkboxes = self._process_form(
                        file_path, json_data
                    )
                    if extracted_form:
                        forms_list.append(extracted_form)
                    if checkboxes:
                        checkboxes_list.append(checkboxes)

            else:
                extracted_form, checkboxes = self._process_form(file_path, json_data)
                if extracted_form:
                    forms_list.append(extracted_form)
                if checkboxes:
                    checkboxes_list.append(checkboxes)

        self._connector.begin_transaction()
        try:
            contact_info = [form.contact_info for form in forms_list]
            self._connector.insert_contact_info(contact_info)

            form_data = []
            for form in forms_list:
                form_data.extend(form.form_data)

            self._connector.insert_form_data(form_data)

            reception = [form.reception for form in forms_list]
            self._connector.insert_form_reception(reception)

            # internal_info = []
            # for form in forms_list:
            #    internal_info.extend(form.internal_info)

            # self._connector.insert_internal_info(internal_info)

            unit = [form.unit for form in forms_list]
            self._connector.insert_unit(unit)

            unit_info = []
            for form in forms_list:
                unit_info.extend(form.unit_info)
            self._connector.insert_unit_info(unit_info)

            self._connector.insert_checkboxes(checkboxes_list)
        except Exception as e:
            self._connector.rollback()
            logger.error(e)
            logger.error("Due to the previous error the insert was rolled back")

        self._connector.commit()

    def process_new_forms(
        self,
        start_dt: pendulum.DateTime | None = None,
        end_dt: pendulum.DateTime | None = None,
    ) -> None:
        """Finds and processes all new forms discovered under the base path.

        Workflow:
          1. Logs the start of processing for the configured form key.
          2. Finds all XML forms recursively.
          3. Ensures storage tables exist (idempotent).
          4. Processes each form and persists new entries.

        Side Effects:
            - Creates storage tables if they do not already exist.
            - Writes log messages at debug/info/warning levels.

        Logging:
            - Debug: start of processing and possibly downstream details.
            - Warning: if no forms are found.
        """
        logger.debug(f"Begin processing {self._form_data_key} forms")
        forms = self._find_forms()
        if not forms:
            logger.warning("No forms found")
        self._connector.begin_transaction()
        try:
            self._connector.create_tables_if_not_exists()
        except Exception as e:
            self._connector.rollback()
            logger.error("Create table was rolled back due to an error")
            raise e
        self._connector.commit()
        self._process_forms(forms, start_dt, end_dt)
