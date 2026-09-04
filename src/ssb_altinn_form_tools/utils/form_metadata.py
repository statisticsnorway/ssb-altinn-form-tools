import logging
import time
from collections import defaultdict
from itertools import cycle
from typing import Any

import requests

from ..models import OptionMetadataModel
from ..models import OptionModel
from ..models import OptionNodes


def _fetch_with_retry(
    urls: list[str],
    form_key: str,
    resource: str,
    max_retries: int = 3,
    delay: int | float = 2,
    timeout: int = 5,
) -> Any | dict[Any, Any]:
    """Attempt to fetch data from a list of URLs with retries.

    Args:
        urls: List of URL strings to try in sequence (rotates on retries).
        form_key: The form to fetch for. Used in logging.
        resource: Jsonschema or optionsmetadata. Used in logging.
        max_retries: Maximum number of retry attempts.
        delay: Delay between retries in seconds.
        timeout: Timeout for each request in seconds.

    Returns:
        dict | Any: Successful json response object.

    Raises:
        ValueError: if 'urls' is empty or not a list.
    """
    if not urls or not isinstance(urls, list):
        raise ValueError("urls must be a non-empty list of URL strings.")

    url_cycle = cycle(urls)  # Rotate through URLs

    for attempt in range(1, (max_retries + 1) * len(urls)):
        current_url = next(url_cycle)
        response = requests.get(current_url, timeout=timeout)
        if response.status_code not in [404, 200, 418]:
            response.raise_for_status()
            continue
        elif response.status_code == 418:
            if attempt < max_retries:
                logger.warning(
                    f"{resource} for schema {form_key} could not be found. Retrying next version"
                )
                continue
        elif response.status_code == 404:
            logger.warning(f"{resource} for schema {form_key} could not be found.")
            continue
        elif not response.text.strip():
            # Json response might be empty, checking for that
            logger.warning(f"{resource} response for schema {form_key} was empty.")
            continue
        else:
            return response.json()

        logger.warning(
            f"No urls for {resource} worked. Retrying in {delay} seconds. Attempt {attempt // (max_retries + 1)} of {max_retries + 1}"
        )
        time.sleep(delay)
    # If we reach here, all retries failed
    logger.warning(f"All {max_retries + 1} attempts failed to fetch {resource} failed.")
    return {}


def _process_options(
    options: list[OptionMetadataModel],
) -> tuple[dict[str, set[OptionModel]], dict[str, set[str]]]:
    unique_option: dict[str, set[OptionModel]] = defaultdict(set)
    nodes_options: dict[str, set[str]] = defaultdict(set)
    for option in options:
        unique_option[option.options_id].update(option.options)
        nodes_options[option.options_id].update([option.node_name])

    return unique_option, nodes_options


def _node_filter(
    data: str | dict[str, Any] | list[str | dict[str, Any]], contained_key: str
) -> list[Any]:
    """Recursive function to extract key-value pairs from an object tree. The key to search for is provided by the "contained_key" argument."""
    results: list[Any] = []
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
                    res = _node_filter(v, contained_key=contained_key)
                    if res:
                        results.extend(res)
    if isinstance(data, list):
        for v in data:
            res = _node_filter(v, contained_key=contained_key)
            if res:
                results.extend(res)

    return results


logger = logging.getLogger(__name__)


def extract_arr_fields(
    json_data: dict[str, dict[str, Any] | Any], parent: str | None = None
) -> list[str]:
    """Extract names of fields that are arrays.

    A function that traverses a dictionary recursivly to extract the name of fields that are arrays.
    """
    array_items = []
    for key, value in json_data.items():
        if isinstance(value, dict):
            array_items.extend(extract_arr_fields(value, key))
        else:
            if (value == "array") and (parent is not None):
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
        ra_version: int | None = None,
        max_retries: int = 3,
    ) -> None:
        """Initializes the default form processor.

        Args:
            form_name: Canonical form name used to build the top-level XML key.
            ra_version: An optional argument denoting which data-version
                of the form to use. This is automatically set to 1 if no argument is
                provided.
            max_retries: Number of retries if a metadata request fails.
        """
        self._form_data_key = f"A3_{form_name}_M"
        self._max_retries = max_retries
        self._form_name = form_name
        self._filtered_data: list[dict[str, Any]] | None = None
        self.array_fields: list[str] | None = None
        self._jsonschema_url = self._create_json_schema_url(form_name, ra_version)
        self._metadata_url = self._create_metadata_url(form_name, ra_version)

    def _create_json_schema_url(
        self,
        form_name: str,
        ra_version: int | None = None,
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
        ra_version: int | None = None,
    ) -> str:
        self._form_name = form_name
        ra_nummer = f"{form_name[:2]}-{form_name[2:]}A3"  # Eksempel: "RA-1234A3"
        version = ra_version if ra_version else 1  # Eksempel: 1 (numerisk)

        ra_base = ra_nummer.split("A3")[0]  # "RA-0848"
        ra_id = ra_base.replace("-", "").lower()  # "ra0848"
        version_str = f"{version:02d}"  # "01"

        return f"https://ssb.apps.tt02.altinn.no/ssb/{ra_id}-{version_str}/api/getskjemakonfig"

    def _get_metadata(self, ra_version: int | None = None) -> list[dict[str, Any]]:
        if self._filtered_data is None:
            if ra_version:
                url = self._create_metadata_url(self._form_name, ra_version)
                urls = []
                for i in range(ra_version, 5):
                    url = self._create_json_schema_url(self._form_name, ra_version + i)
                    urls.append(url)
            else:
                url = self._jsonschema_url
                urls = []
                for i in range(1, 5):
                    url = self._create_metadata_url(self._form_name, i)
                    urls.append(url)

            response_json = _fetch_with_retry(
                urls, self._form_data_key, "Metadata", max_retries=self._max_retries
            )

            if response_json and len(response_json.keys()):
                self._filtered_data = _node_filter(
                    response_json, contained_key="options"
                )
                return self._filtered_data

            return []

        else:
            return self._filtered_data

    def extract_options_list(
        self, skjema: str, iso_period: str, ra_version: int | None = None
    ) -> list[OptionMetadataModel]:
        """Extract metadata related for all defined options lists and their options."""
        processed: list[OptionMetadataModel] = []
        data = self._get_metadata()
        for res in data:
            if res.get("options"):
                model_data = OptionMetadataModel.model_validate(
                    {"skjema": skjema, "iso_period": iso_period, **res}
                )
                processed.append(model_data)
        return processed

    def extract_options_nodes(
        self, skjema: str, iso_period: str, ra_version: int | None = None
    ) -> list[OptionNodes]:
        """Extract metadata related to which nodes has defined options."""
        processed = self.extract_options_list(skjema, iso_period, ra_version)
        unique_option, nodes_options = _process_options(processed)
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

    def get_array_fields(self, ra_version: int | None = None) -> list[str] | None:
        """Method for getting array fields.

        Will use existings list if method already has been called.
        """
        if self.array_fields is not None:
            return self.array_fields

        try:
            if ra_version:
                url = self._create_json_schema_url(self._form_name, ra_version)
                urls = []
                for i in range(ra_version, 5):
                    url = self._create_json_schema_url(self._form_name, ra_version + i)
                    urls.append(url)
            else:
                url = self._jsonschema_url
                urls = []
                for i in range(1, 5):
                    url = self._create_json_schema_url(self._form_name, i)
                    urls.append(url)

            response_json = _fetch_with_retry(
                urls, self._form_data_key, "Jsonschema", max_retries=self._max_retries
            )

            if response_json and len(response_json.keys()):
                self.array_fields = extract_arr_fields(response_json)
            else:
                self.array_fields = []
            return self.array_fields

        except Exception as e:
            logger.warning(
                f"Fetching metadata for the form resulted in the following error. Possibly because metadata does not exist. Error: \n{e}"
            )
            # Some forms does not have metadata in Altinn
            return None
