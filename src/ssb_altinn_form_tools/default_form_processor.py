import glob
import json
import logging
from pathlib import Path

import xmltodict

from ssb_altinn_form_tools.meta_form_extractor import MetaFormExtractor
from ssb_altinn_form_tools.meta_form_processor import MetaFormProcessor
from ssb_altinn_form_tools.meta_storage_connector import MetaStorageConnector
from ssb_altinn_form_tools.models import CheckboxConfig
from ssb_altinn_form_tools.models import ExtractedForm
from ssb_altinn_form_tools.models import FormJsonData
from ssb_altinn_form_tools.utils.form_metadata import FormMetadata

logger = logging.getLogger(__name__)


def extract_xml_to_dict(xml_path: Path, array_fields: list[str] | None = None) -> dict:
    """Function for reading an xml file and transforming it to a dictionary.

    Function is separated to enable testing.
    """
    xml_string = xml_path.read_text()
    dictionary: dict = xmltodict.parse(
        xml_string, force_list=array_fields, xml_attribs=False
    )
    return dictionary


class DefaultFormProcessor(MetaFormProcessor):
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
        self._form_name = form_name
        self._alias_mapping = alias_mapping
        self._glob_path = (
            alternative_glob_path
            if alternative_glob_path
            else f"{self._form_base_path}/**/**/**/**/*.xml"
        )

        self._metadata_helper = FormMetadata(form_name, ra_version)
        if checkbox_mapping:
            self._checkbox_mapping = [
                CheckboxConfig.model_validate(x) for x in checkbox_mapping
            ]
        else:
            self._checkbox_mapping = None

        self.array_fields = self._metadata_helper.get_array_fields()
        print(self.array_fields)

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

    def _process_form(
        self, xml_path: Path, json_data: FormJsonData
    ) -> ExtractedForm | None:
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
            print(self.array_fields)
            dictionary: dict = extract_xml_to_dict(
                xml_path, array_fields=self.array_fields
            )[self._form_data_key]
            extracted_form = self._extractor.extract_form(dictionary, json_data)
            # print(extracted_form.klass_info)
            # raise ValueError("he")
            if self._alias_mapping:
                self._map_alias(self._alias_mapping, extracted_form)
            return extracted_form

        else:
            logger.info(
                f"Skipped inserting form with refernce {json_data.altinn_reference} since it already exists"
            )
        return None

    def _process_forms(self, forms: list[str]) -> None:
        """Processes a collection of form file paths.

        For each XML path, this method derives the corresponding JSON metadata
        file (by replacing suffixes), validates the JSON, and then processes
        the form via `_process_form`.

        Args:
            forms (list[str]): List of XML file paths to process.

        Raises:
            FileNotFoundError: If the derived JSON metadata file does not exist.
            pydantic.ValidationError: If `FormJsonData` validation fails.
        """
        new_forms: list[ExtractedForm] = []
        for form in forms:
            file_path = Path(form)

            json_name = file_path.name.replace("xml", "json").replace("form", "meta")
            json_path = file_path.with_name(json_name)
            json_data = FormJsonData.model_validate_json(json_path.read_text())
            extracted_form = self._process_form(file_path, json_data)
            if extracted_form:
                new_forms.append(extracted_form)

        self._connector.begin_transaction()
        try:
            self._connector.insert_contact_info(
                [form.contact_info for form in new_forms]
            )
            form_data = []
            unit_info = []
            periods = []
            for form in new_forms:
                form_data.extend(form.form_data)
                unit_info.extend(form.unit_info)
                periods.append(form.reception.iso_period)
            self._connector.insert_form_data(form_data)
            self._connector.insert_form_data_unedited(form_data)
            self._connector.insert_form_reception(
                [form.reception for form in new_forms]
            )
            self._connector.insert_unit([form.unit for form in new_forms])
            self._connector.insert_unit_info(unit_info)

            for period in set(periods):
                options_exists = self._connector.validate_options_exists(
                    self._form_name, period
                )
                if options_exists is False:
                    options_list = self._metadata_helper.extract_options_list(
                        self._form_name, period
                    )
                    option_nodes = self._metadata_helper.extract_options_nodes(
                        self._form_name, period
                    )
                    self._connector.insert_option_node(option_nodes)
                    self._connector.insert_option_list(options_list)

        except Exception as e:
            self._connector.rollback()
            logger.error(e)
            logger.error("Due to the previous error the insert was rolled back")
        else:
            self._connector.commit()
            inserted_form_ids = [form.reception.refnr for form in new_forms]
            logger.info(f"Form {inserted_form_ids} was inserted into the database")
            # logger.debug(f"Data: {extracted_form}")

    def process_new_forms(self) -> None:
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
        self._process_forms(forms)
