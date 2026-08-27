import logging
from collections.abc import Iterable
from typing import Any

from .meta_form_extractor import InputFormType
from .meta_form_extractor import MetaFormExtractor
from .models import ContactInfo
from .models import FormData
from .models import FormJsonData
from .models import FormNode
from .models import FormReception
from .models import UnitInfo

logger = logging.getLogger(__name__)


def calc_depth(parent: str | None) -> int | None:
    """Calculates how deep the parent xml-path is in the hierarchy.

    Args:
        parent: XML field path.

    Returns:
        None or the depth value of the parent.

    """
    if parent:
        return len(parent.split("/"))
    else:
        return None


def parse_index(path: str | None) -> int | None:
    """Attempts to extract the index from a file path.

    Args:
        path: XML field path.

    Returns:
        None or the index value of the parent.

    """
    try:
        if path:
            return int(path.split("/")[-2])
        else:
            return None
    except ValueError:
        return None


def parse_entries(
    data: dict[str, Any] | list[Any], parent: str | None = None
) -> list[FormNode]:
    """Recursive function for flattening XML-like structures.

    Args:
        data: XML-data in list or dict form.
        parent: The path to the parent node.

    Returns:
        A flattened list of form nodes.

    """
    fields = []

    iterator: Iterable[tuple[int | str, Any]]

    if isinstance(data, list):
        iterator = enumerate(data)
    elif isinstance(data, dict):
        iterator = data.items()

    for key, value in iterator:
        sti = f"{parent if parent else ''}/{key}"
        if isinstance(value, list) or isinstance(value, dict):
            fields.extend(parse_entries(value, parent=sti))

        else:
            parent = str(parent) if parent else ""
            index = parse_index(sti)
            depth = calc_depth(parent)
            fields.append(
                FormNode(
                    feltsti=sti,
                    feltnavn=str(key),
                    verdi=str(value),
                    dybde=depth,
                    indeks=index,
                )
            )

    return fields


class DefaultFormExtractor(MetaFormExtractor):
    """A default extractor from XML-forms.

    The class is responsible for extracting data to
    the standard table schema. See `MetaFormExtractor` for implemenation details.

    """

    def __init__(self) -> None:
        """Initalizer for a default form extractor."""
        super().__init__()

    def extract_contact_info(
        self,
        form_dict_data: InputFormType,
        form: str,
        ident: str,
        refnr: str,
        iso_period: str,
    ) -> ContactInfo:
        """Function for extracting contact info from form data.

        Args:
            form_dict_data: XML-data in list or dict form.
            form: The name of the form (RA-number).
            ident: The id of the unit.
            refnr: The id number of the form.
            iso_period: Registered iso_period.

        Returns:
            list(ContactInfo): A pydantic model representing the contact info.

        """
        form_data = form_dict_data["Kontakt"]

        assert isinstance(form_data, dict)

        return ContactInfo(
            skjema=form,
            ident=ident,
            refnr=refnr,
            bekreftet_kontaktinfo=form_data.get("kontaktInfoBekreftet") == "1",
            iso_period=iso_period,
            **form_data,
        )

    def extract_form_data(
        self,
        form_dict_data: InputFormType,
        form: str,
        ident: str,
        refnr: str,
        iso_period: str,
    ) -> list[FormData]:
        """Extract structured form data from raw XML-derived input.

        This function processes the ``SkjemaData`` section of a form represented as
        a dictionary or list (typically parsed from XML). Each entry is normalized
        using ``parse_entries`` and then converted into a ``FormData`` Pydantic
        model, enriched with contextual metadata such as year, form number, unit
        identifier, and reference number.

        Args:
            form_dict_data: Raw form content in dictionary or list form, typically
                originating from XML parsing.
            form: The name or code of the form (e.g., RA-number).
            ident: The identifier for the reporting unit.
            refnr: The reference number for the submitted form instance.
            iso_period: Registered iso_period.

        Returns:
            list(FormData): A list of ``FormData`` objects, each representing a parsed and validated
            node from the form data.
        """
        form_data = form_dict_data["SkjemaData"]

        assert isinstance(form_data, dict) or isinstance(form_data, list)
        parsed_form_data = parse_entries(form_data)

        results: list[FormData] = []
        for node in parsed_form_data:
            node_data = FormData.from_form_data(
                node=node,
                form=form,
                ident=ident,
                refnr=refnr,
                iso_period=iso_period,
            )
            results.append(node_data)
        return results

    def extract_form_reception(
        self, form_dict_data: InputFormType, json_data: FormJsonData
    ) -> FormReception:
        """Extracts reception metadata for a form from internal XML data and JSON input.

        This function reads the ``InternInfo`` section of the XML-derived form
        structure and combines it with metadata delivered via the ``json_data``
        object. The combined values are used to construct a ``FormReception``
        model, including default values for edit status, comments, and activation.
        Logged JSON data is also emitted at debug level to assist with tracing.

        Args:
            form_dict_data: Raw form content containing an
                ``InternInfo`` dictionary with metadata fields.
            json_data: Supplementary form metadata received from
                JSON, including Altinn reference number and delivery date.

        Returns:
            FormReception: A fully constructed ``FormReception`` model combining
            XML-derived and JSON-derived metadata.
        """
        form_data = form_dict_data["InternInfo"]

        assert isinstance(form_data, dict)

        logger.debug(json_data)

        return FormReception(
            status="ikke editert",
            kommentar="",
            aktiv=True,
            refnr=json_data.altinn_reference,
            dato_mottatt=json_data.date_delivered,
            **form_data,
        )

    def extract_unit_info(
        self, form_dict_data: InputFormType, ident: str, iso_period: str
    ) -> list[UnitInfo]:
        """Extracts unit-related metadata from internal form information.

        This function iterates over the ``InternInfo`` section of the form structure
        (parsed from XML into a dictionary) and collects key-value pairs whose keys
        start with ``"enhets"``. Each matching entry is transformed into a
        ``UnitInfo`` model, annotated with the reporting year and unit identifier.

        Args:
            form_dict_data: Raw form content containing an
                ``InternInfo`` dictionary with internal metadata.
            ident: Identifier for the reporting unit.
            iso_period: Registered iso_period.

        Returns:
            list[UnitInfo]: A list of ``UnitInfo`` objects built from keys in
            ``InternInfo`` that start with ``"enhets"``.

        Raises:
            TypeError: If form_dict_data["InternInfo"] is not a dict.
        """
        form_data = form_dict_data["InternInfo"]

        if not isinstance(form_data, dict):
            raise TypeError(f"form_data must be type dict. Is type '{type(form_data)}'")

        info: list[UnitInfo] = []
        for key, value in form_data.items():
            if not isinstance(key, str):
                raise TypeError(f"Key must be type str. Is type '{type(key)}'")
            if key.startswith("enhets"):
                data = UnitInfo(
                    ident=ident, variable=key, verdi=value, iso_period=iso_period
                )
                info.append(data)
        return info
