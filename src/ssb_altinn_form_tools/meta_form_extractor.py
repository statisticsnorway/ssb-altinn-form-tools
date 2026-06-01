from abc import ABC
from abc import abstractmethod

from .models import ContactInfo
from .models import ExtractedForm
from .models import FormData
from .models import FormJsonData
from .models import FormReception
from .models import Unit
from .models import UnitInfo

InputFormType = dict[str, list | dict | str | int | None]


class MetaFormExtractor(ABC):
    """Abstract base class defining the interface for form extraction.

    Concrete implementations of this class are responsible for transforming raw
    XML-derived data structures into strongly typed domain models such as
    ``ContactInfo``, ``FormReception``, ``Unit``, ``UnitInfo``, and
    ``FormData``. The extraction process is typically orchestrated by a form
    processor that delegates parsing tasks to an implementation of this class.
    """

    @abstractmethod
    def extract_contact_info(
        self,
        form_dict_data: InputFormType,
        form: str,
        ident: str,
        refnr: str,
        iso_period: str,
    ) -> ContactInfo:
        """Extracts contact information from parsed form data.

        Args:
            form_dict_data (InputFormType): Raw form content derived from XML.
            form (str): Form code or type identifier.
            ident (str): Identifier of the reporting unit.
            refnr (str): Reference number associated with the form instance.
            iso_period (str): Registered iso_period.

        Returns:
            ContactInfo: Structured contact metadata extracted from the form.
        """
        ...

    @abstractmethod
    def extract_form_data(
        self,
        form_dict_data: InputFormType,
        form: str,
        ident: str,
        refnr: str,
        iso_period: str,
    ) -> list[FormData]:
        """Extracts detailed field-level form data.

        Args:
            form_dict_data (InputFormType): Parsed form content containing field values.
            form (str): Form name or identifier.
            ident (str): Identifier of the reporting unit.
            refnr (str): Reference number for the submitted form.
            iso_period (str): Registered iso_period.

        Returns:
            list[FormData]: A list of validated form data entries.
        """
        ...

    @abstractmethod
    def extract_form_reception(
        self, form_dict_data: InputFormType, json_data: FormJsonData
    ) -> FormReception:
        """Extracts reception and submission metadata for the form.

        Args:
            form_dict_data (InputFormType): XML-derived internal metadata section.
            json_data (FormJsonData): Supplemental metadata from JSON.

        Returns:
            FormReception: Structured information about form reception.
        """
        ...

    def extract_unit(self, form: str, ident: str, iso_period: str) -> Unit:
        """Constructs a basic ``Unit`` model from form metadata.

        This default implementation requires no override unless additional
        fields or lookup logic are necessary.

        Args:
            form (str): Form name or code.
            ident (str): Identifier of the reporting unit.
            iso_period (str): Registered iso_period.

        Returns:
            Unit: A ``Unit`` model representing the reporting entity.
        """
        return Unit(ident=ident, skjema=form, iso_period=iso_period)

    @abstractmethod
    def extract_unit_info(
        self, form_dict_data: InputFormType, ident: str, iso_period: str
    ) -> list[UnitInfo]:
        """Extracts additional unit-level metadata from the form.

        Args:
            form_dict_data (InputFormType): Parsed XML content containing internal metadata.
            ident (str): Identifier of the reporting unit.
            iso_period (str): Registered iso_period.

        Returns:
            list[UnitInfo]: Structured metadata entries describing unit attributes.
        """
        ...

    def extract_form(
        self, form_dict_data: InputFormType, json_data: FormJsonData
    ) -> ExtractedForm:
        """Extracts all structured models required to represent a complete form.

        This method coordinates the extraction workflow by delegating to the
        concrete implementations of the extraction methods defined in this
        abstract class.

        Workflow:
            1. Extract form reception metadata.
            2. Use that metadata (year, form code, ident, refnr) to extract:
               - Contact information
               - Unit information
               - Form data entries
            3. Construct and return an ``ExtractedForm`` model containing all components.

        Args:
            form_dict_data (InputFormType): XML-derived form content.
            json_data (FormJsonData): Supplemental metadata associated with the form.

        Returns:
            ExtractedForm: A fully aggregated model containing all parsed form sections.
        """
        form_info = self.extract_form_reception(form_dict_data, json_data)

        return ExtractedForm(
            reception=form_info,
            contact_info=self.extract_contact_info(
                form_dict_data,
                form=form_info.skjema,
                ident=form_info.ident,
                refnr=form_info.refnr,
                iso_period=form_info.iso_period,
            ),
            unit=self.extract_unit(
                form=form_info.skjema,
                ident=form_info.ident,
                iso_period=form_info.iso_period,
            ),
            unit_info=self.extract_unit_info(
                form_dict_data,
                ident=form_info.ident,
                iso_period=form_info.iso_period,
            ),
            form_data=self.extract_form_data(
                form_dict_data,
                form=form_info.skjema,
                ident=form_info.ident,
                refnr=form_info.refnr,
                iso_period=form_info.iso_period,
            ),
        )
