import logging
from pathlib import Path

import pendulum
import xmltodict

from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.meta_form_extractor import MetaFormExtractor
from ssb_altinn_form_tools.meta_storage_connector import MetaStorageConnector
from ssb_altinn_form_tools.models import ExtractedForm
from ssb_altinn_form_tools.models import FormJsonData

logger = logging.getLogger(__name__)


class BatchFormProcessor(DefaultFormProcessor):
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
        super().__init__(
            form_name=form_name,
            form_base_path=form_base_path,
            extractor=extractor,
            connector=connector,
            alias_mapping=alias_mapping,
            checkbox_mapping=checkbox_mapping,
            ra_version=ra_version,
            alternative_glob_path=alternative_glob_path,
        )

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
            xml_string = xml_path.read_text()
            dictionary: dict = xmltodict.parse(
                xml_string, force_list=self.array_fields
            )[self._form_data_key]
            extracted_form = self._extractor.extract_form(dictionary, json_data)

            if self._alias_mapping:
                self._map_alias(self._alias_mapping, extracted_form)

            return extracted_form
        else:
            logger.info(
                f"Skipped inserting form with refernce {json_data.altinn_reference} since it already exists"
            )
            return None

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

        for form in forms:
            file_path = Path(form)
            # tests/testdata/RA0187/2026/2/2/0055608a311b_c4a9567a-8378-4eea-8971-dab4145ab09d
            reference = file_path.name.split("_")[0]  # 0055608a311b
            if self._connector.validate_form_is_new(reference):
                json_name = file_path.name.replace("xml", "json").replace(
                    "form", "meta"
                )
                json_path = file_path.with_name(json_name)
                json_data = FormJsonData.model_validate_json(json_path.read_text())
                if start_dt and end_dt:
                    delivered_date = pendulum.instance(json_data.date_delivered)
                    if start_dt < delivered_date < end_dt:
                        extracted_form = self._process_form(file_path, json_data)
                        if extracted_form:
                            forms_list.append(extracted_form)

                else:
                    extracted_form = self._process_form(file_path, json_data)
                    if extracted_form:
                        forms_list.append(extracted_form)

        self._connector.begin_transaction()
        try:
            contact_info = [form.contact_info for form in forms_list]
            self._connector.insert_contact_info(contact_info)

            form_data = []
            unit_info = []
            all_periods = []
            for form in forms_list:
                form_data.extend(form.form_data)
                unit_info.extend(form.unit_info)
                all_periods.append(form.reception.iso_period)

            self._connector.insert_form_data(form_data)
            self._connector.insert_form_data_unedited(form_data)
            self._connector.insert_form_reception(
                [form.reception for form in forms_list]
            )
            self._connector.insert_unit([form.unit for form in forms_list])
            self._connector.insert_unit_info(unit_info)

            for period in set(all_periods):
                options_exists = self._connector.validate_options_exists(
                    self._form_name, period
                )
                if options_exists is False:
                    logger.error(
                        f"Options for period {period} does not exists. Inserting now."
                    )
                    option_list = self._metadata_helper.extract_options_list(
                        self._form_name, period
                    )
                    option_nodes = self._metadata_helper.extract_options_nodes(
                        self._form_name, period
                    )
                    self._connector.insert_option_list(option_list)
                    self._connector.insert_option_node(option_nodes)

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
