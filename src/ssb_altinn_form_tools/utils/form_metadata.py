import logging
from collections import defaultdict

import requests

from ..models import FormattingMetadataModel
from ..models import OptionMetadataModel
from ..models import OptionModel
from ..models import OptionNodes


def process_options(options: list[OptionMetadataModel]):
    unique_option: dict[str, set[OptionModel]] = defaultdict(set)
    nodes_options: dict[str, set[str]] = defaultdict(set)
    for option in options:
        unique_option[option.options_id].update(option.options)
        nodes_options[option.options_id].update([option.node_name])

    return unique_option, nodes_options


def node_filter(data: dict, contained_key: str) -> list[dict]:
    results = []
    if isinstance(data, str):
        return results

    if isinstance(data, dict):
        if contained_key in data:
            results.append(data)
        else:
            for _k, v in data.items():
                if contained_key in v:
                    results.append(v)
                else:
                    res = node_filter(v, contained_key=contained_key)
                    if res:
                        results.extend(res)
    if isinstance(data, list):
        for v in data:
            res = node_filter(v, contained_key=contained_key)
            if res:
                results.extend(res)

    return results


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


class FormMetadata:
    """Default processor for scanning, extracting, and persisting forms.

    This processor locates XML form files on disk, parses them into dictionaries,
    extracts structured models via a `MetaFormExtractor`, optionally applies
    alias and checkbox mapping, and persists the results through a
    `MetaStorageConnector` using transactional semantics.
    """

    def __init__(
        self,
        form_name: str,
        ra_version: None | int = None,
    ) -> None:
        """Initializes the default form processor.

        Args:
            form_name (str): Canonical form name used to build the top-level XML key.
            ra_version (str | None): An optional argument denoting which data-version
                of the form to use. This is automatically set to 1 if no argument is
                provided.
        """
        self._form_data_key = f"A3_{form_name}_M"
        self._jsonschema_url = self._create_json_schema_url(form_name, ra_version)
        self._metadata_url = self._create_metadata_url(form_name, ra_version)

    def _create_json_schema_url(
        self,
        form_name: str,
        ra_version: None | int = None,
    ) -> str:
        ra_nummer = f"{form_name[:2]}-{form_name[2:]}A3"  # Eksempel: "RA-1234A3"
        version = ra_version if ra_version else 1  # Eksempel: 1 (numerisk)

        ra_base = ra_nummer.split("A3")[0]  # "RA-0848"
        ra_id = ra_base.replace("-", "").lower()  # "ra0848"
        version_str = f"{version:02d}"  # "01"

        return f"https://ssb.apps.altinn.no/ssb/{ra_id}-{version_str}/api/jsonschema/A3_{ra_base}_M"

    def _create_metadata_url(
        self,
        form_name: str,
        ra_version: None | int = None,
    ) -> str:
        self._form_name = form_name
        ra_nummer = f"{form_name[:2]}-{form_name[2:]}A3"  # Eksempel: "RA-1234A3"
        version = ra_version if ra_version else 1  # Eksempel: 1 (numerisk)

        ra_base = ra_nummer.split("A3")[0]  # "RA-0848"
        ra_id = ra_base.replace("-", "").lower()  # "ra0848"
        version_str = f"{version:02d}"  # "01"

        return f"https://ssb.apps.tt02.altinn.no/ssb/{ra_id}-{version_str}/api/getskjemakonfig"

    def _get_metadata(self, ra_version: int | None = None) -> list[dict]:
        if hasattr(self, "_filtered_data") is False:
            if ra_version:
                url = self._create_json_schema_url(self._form_name, ra_version)
            else:
                url = self._metadata_url
            response = requests.get(url)

            if response.status_code not in [404, 200]:
                response.raise_for_status()
                return []
            elif response.status_code == 404:
                logger.warning(
                    f"Metadata for schema {self._form_data_key} could not be found."
                )
                return []
            elif not response.text.strip():
                # Json response might be empty, checking for that
                logger.warning(
                    f"Metadata response for schema {self._form_data_key} was empty."
                )
                return []
            else:
                _response_json = response.json()
                self._filtered_data = node_filter(
                    _response_json, contained_key="options"
                )
                return self._filtered_data
        else:
            return self._filtered_data

    def extract_options_list(
        self, skjema: str, iso_period: str, ra_version: int | None = None
    ) -> list[OptionMetadataModel]:
        """Extract metadata related for all defined options lists and their options."""
        processed = []
        data = self._get_metadata()
        for res in data:
            if res.get("options"):
                data = OptionMetadataModel.model_validate(
                    {"skjema": skjema, "iso_period": iso_period, **res}
                )
                processed.append(data)
        return processed

    def extract_options_nodes(
        self, skjema: str, iso_period: str, ra_version: int | None = None
    ) -> list[OptionNodes]:
        """Extract metadata related to which nodes has defined options."""
        processed = self.extract_options_list(skjema, iso_period, ra_version)
        unique_option, nodes_options = process_options(processed)
        options = []
        for key in unique_option.keys():
            res = nodes_options.get(key, set())
            model = OptionNodes(
                skjema=skjema,
                iso_period=iso_period,
                option_id=key,
                node_list=res,
            )
            options.append(model)
        return options

    def _extract_formatting(
        self, form_metadata: list[dict], skjema: str, iso_period: str
    ):
        pass
        formatting = []
        for res in self._filtered_data:
            if res.get("formatting"):
                data = FormattingMetadataModel.model_validate(
                    {"skjema": "test", "iso_period": "test", **res}
                )
                formatting.append(data)

    def get_array_fields(self, ra_version: int | None = None) -> list[str] | None:
        """Method for getting array fields.

        Will use existings list if method already has been called.
        """
        if hasattr(self, "array_fields"):
            return self.array_fields

        try:
            if ra_version:
                url = self._create_json_schema_url(self._form_name, ra_version)
            else:
                url = self._jsonschema_url
            prod_res = requests.get(url)
            if prod_res.status_code not in [404, 200]:
                prod_res.raise_for_status()
            elif prod_res.status_code == 404:
                logger.warning(
                    f"Jsonschema for schema {self._form_data_key} could not be found."
                )
                self.array_fields = None
            elif not prod_res.text.strip():
                # Json response might be empty, checking for that
                logger.warning(
                    f"Json response for schema {self._form_data_key} was empty."
                )
                self.array_fields = None
            else:
                self.form_json = prod_res.json()
                self.array_fields = extract_arr_fields(self.form_json)

            return self.array_fields
        except Exception as e:
            logger.warning(
                f"Fetching metadata for the form resulted in the following error. Possibly because metadata does not exist. Error: \n{e}"
            )
            # Some forms does not have metadata in Altinn
            self.array_fields = None
            return self.array_fields
