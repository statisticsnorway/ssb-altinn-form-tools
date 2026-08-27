from __future__ import annotations

import datetime
from typing import Any
from typing import Literal

import pendulum
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_core import PydanticCustomError


class FormNode(BaseModel):
    """Represents a generic node extracted from a form (XML/JSON).

    This is a reusable base model for a single field/value pair with contextual
    metadata (e.g., path, depth, index). It can be specialized or embedded in
    higher-order models.

    Attributes:
        feltsti (str): Full path of the field (e.g., XML path).
        feltnavn (str): Field/variable name.
        verdi (str | None): Extracted value as a string, if any.
        dybde (int | None): Nesting depth in the original structure.
        indeks (int | None): Index within a repeated/array structure.
        alias (str | None): Optional user-friendly name/alias for the field.
    """

    feltsti: str
    feltnavn: str
    verdi: str | None = Field(default=None)
    dybde: int | None = Field(default=None)
    indeks: int | None = Field(default=None)
    alias: str | None = Field(default=None)

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class FormData(FormNode):
    """Represents a single form data entry with contextual identifiers.

    Extends :class:`FormNode` by adding form scoping information such as
    year, form code, unit identifier, and reference number.

    Attributes:
        iso_period: Reporting year.
        skjema: Form name or code (e.g., RA-number).
        ident: Identifier of the reporting unit.
        refnr: Reference number of the submitted form instance.
    """

    iso_period: str
    skjema: str
    ident: str
    refnr: str

    @staticmethod
    def from_form_data(
        node: FormNode, form: str, ident: str, refnr: str, iso_period: str
    ) -> FormData:
        """Constructs a :class:`FormData` from a :class:`FormNode` and context.

        Args:
            node: The base node carrying path/name/value metadata.
            form: Form code/name to attach.
            ident: Unit identifier to attach.
            refnr: Form instance reference to attach.
            iso_period: Registered iso_period.

        Returns:
            FormData: The composed form data entry with context.
        """
        return FormData(
            skjema=form,
            ident=ident,
            refnr=refnr,
            iso_period=iso_period,
            **node.model_dump(),
        )

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class ContactInfo(BaseModel):
    """Contact information associated with a submitted form.

    Field values are mapped from upstream aliases using Pydantic's `Field(validation_alias=...)`.

    Attributes:
        iso_period: Reporting year.
        skjema: Form name or code (e.g., RA-number).
        ident: Identifier of the reporting unit.
        refnr: Reference number for the submitted form.
        kontaktperson: Name of the contact person. Alias: ``kontaktPersonNavn``.
        epost: Email address. Alias: ``kontaktPersonEpost``.
        telefon: Phone number. Alias: ``kontaktPersonTelefon``.
        bekreftet_kontaktinfo: Whether contact info is confirmed.
        kommentar_kontaktinfo: Free-text comment. Alias: ``kontaktKommentar``.
        kommentar_krevende: Notes about demanding/complex contact cases.
            Alias: ``kontaktKrevende``.
    """

    iso_period: str
    skjema: str
    ident: str
    refnr: str
    kontaktperson: str | None = Field(
        default=None, validation_alias="kontaktPersonNavn"
    )
    epost: str | None = Field(default=None, validation_alias="kontaktPersonEpost")
    telefon: str | None = Field(default=None, validation_alias="kontaktPersonTelefon")
    bekreftet_kontaktinfo: bool = Field(default=False)
    kommentar_kontaktinfo: str | None = Field(
        default=None, validation_alias="kontaktKommentar"
    )
    kommentar_krevende: str | None = Field(
        default=None, validation_alias="kontaktKrevende"
    )

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class Unit(BaseModel):
    """Represents a reporting unit (entity submitting the form).

    Attributes:
        iso_period: Reporting year.
        ident: Unique identifier of the reporting unit.
        skjema: Form name or code (e.g., RA-number).
    """

    iso_period: str
    ident: str
    skjema: str

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class UnitInfo(BaseModel):
    """Represents an additional key-value attribute for a unit.

    Attributes:
        iso_period: Reporting year.
        ident: Identifier of the reporting unit.
        variable: Name of the metadata variable.
        verdi: Value of the metadata variable.
    """

    iso_period: str
    ident: str
    variable: str
    verdi: str | None = Field(default=None)

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class FormReception(BaseModel):
    """Reception and submission metadata for a specific form instance.

    Configured to validate input using both field names and aliases to support
    keys from external sources such as Altinn.

    Attributes:
        start_date: Start date of the reporting period.
        end_date: End date of the reporting period.
        iso_period: ISO period associated with the form.
        skjema_versjon: Version of the submitted form, if available.
        skjema: Form name or code. Alias: ``raNummer``.
        ident: Reporting unit identifier. Alias: ``enhetsIdent``.
        refnr: Reference number of the submitted form. Alias: ``altinnReferanse``.
        dato_mottatt: Timestamp when the form was received.
            Alias: ``altinnTidspunktLevert``.
        status: Edit status of the form.
        kommentar: Free-text comment associated with the reception.
        aktiv: Indicates whether the form instance is active.

    Notes:
        ``model_config`` enables validation using both field aliases and field
        names.
    """

    start_date: datetime.datetime = Field()
    end_date: datetime.datetime = Field()
    iso_period: str = Field()
    skjema_versjon: str | None = Field(default=None, validation_alias="skjemaVersjon")
    skjema: str = Field(validation_alias="raNummer")
    ident: str = Field(validation_alias="enhetsIdent")
    refnr: str = Field(validation_alias="altinnReferanse")
    dato_mottatt: datetime.datetime = Field(validation_alias="altinnTidspunktLevert")
    status: Literal["ferdig editert", "under editering", "ikke editert"]
    kommentar: str
    aktiv: bool

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def validator(cls, data: Any) -> Any:
        """Custom validator to parse periods from xml-forms."""
        # The validation is mostly deriving variables. Can skip that if they already exists
        if all(var in data for var in ["start_date", "end_date", "iso_period"]):
            return data

        try:
            period_type = data.get("periodeType")
        except Exception as e:
            raise PydanticCustomError(
                "",
                "periodeType could not be validated. Expected str instead recieved {number}",
                {"number": e},
            ) from e
        try:
            _period = data.get("periodeNummer")
            if _period is None:
                period_number = 1
            else:
                period_number = int(_period)

        except Exception as e:
            raise PydanticCustomError(
                "",
                "periodeNummer could not be validated. Expected int instead recieved {number}",
                {"number": e},
            ) from e
        try:
            period_year = int(data.get("periodeAAr"))
        except Exception as e:
            raise PydanticCustomError(
                "",
                "periodeAar could not be validated. Expected int instead recieved {number}",
                {"number": e},
            ) from e

        data["aar"] = period_year

        if period_type == "MND":
            start = pendulum.datetime(period_year, month=period_number, day=1)
            end = start.end_of("month")
            iso_format = start.format("YYYY-MM")

        elif period_type == "AAR":
            start = pendulum.datetime(period_year, month=1, day=1)
            end = start.end_of("year")
            iso_format = start.format("YYYY")

        elif period_type == "UKE":
            d = datetime.date.fromisocalendar(period_year, period_number, day=1)
            start = pendulum.datetime(d.year, d.month, d.day)
            end = start.end_of("week")
            iso_format = start.strftime("%G-W%V")

        elif period_type == "KVRT":
            start = pendulum.datetime(period_year, month=period_number * 3, day=1)
            end = start.end_of("month")
            iso_format = start.format("YYYY-MM")

        else:
            raise PydanticCustomError(
                "",
                "period_type could not be validated: {period}",
                {"period": period_type},
            )

        data["start_date"] = start
        data["end_date"] = end
        data["iso_period"] = iso_format

        return data

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class FormJsonData(BaseModel):
    """Lightweight JSON metadata accompanying a form file.

    Attributes:
        altinn_reference (str): Reference number for the form instance.
            Alias: ``altinnReferanse``.
        date_delivered (datetime.datetime): Submission timestamp.
            Alias: ``altinnTidspunktLevert``.
    """

    altinn_reference: str = Field(validation_alias="altinnReferanse")
    date_delivered: datetime.datetime = Field(validation_alias="altinnTidspunktLevert")

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class ExtractedForm(BaseModel):
    """Aggregates all structured sections extracted for a form instance.

    Attributes:
        reception (FormReception): Reception/submission metadata.
        contact_info (ContactInfo): Contact information of the submitter.
        unit (Unit): Basic unit identity.
        unit_info (list[UnitInfo]): Additional unit attributes.
        form_data (list[FormData]): Field-level data extracted from the form.
    """

    reception: FormReception
    contact_info: ContactInfo
    unit: Unit
    unit_info: list[UnitInfo]
    form_data: list[FormData]

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class OptionNodes(BaseModel):
    """Model for represention what options_id nodes should map to."""

    iso_period: str
    skjema: str
    option_id: str
    node_list: set[str]


class OptionModel(BaseModel):
    """Model representing an option."""

    value: str
    label: str

    def __hash__(self) -> int:
        """Make class hashable."""
        return self.value.__hash__()


class OptionMetadataModel(BaseModel):
    """Model representing options metadata collected from Altinn api."""

    iso_period: str
    skjema: str
    options: list[OptionModel] = Field(validation_alias="options")
    options_id: str = Field(validation_alias="optionsId")
    options_url: str | None = Field(default=None, validation_alias="optionsUrl")
    node_name: str = Field(validation_alias="dataModelField")

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
    )

    @field_validator("node_name", mode="before")
    @classmethod
    def create_node_name(cls, val: str) -> str:
        """Validator for nodenames."""
        return val.split(".")[-1]


class StringFormatModel(BaseModel):
    """Model representing string formatting in Altinn-metadata api."""

    min_length: int | None = Field(default=None, validation_alias="minLength")
    max_length: int | None = Field(default=None, validation_alias="maxLength")


class DateFormatModel(BaseModel):
    """Model representing date formatting in Altinn-metadata api."""

    min_date: str | None = Field(default=None, validation_alias="minDate")
    max_date: str | None = Field(default=None, validation_alias="maxDate")


class NumberFormatSpecifierModel(BaseModel):
    """Model representing number formatting in Altinn-metadata api."""

    allow_negative: bool = Field(validation_alias="allowNegative")
    decimal_scale: int = Field(validation_alias="decimalScale")
    decimal_separator: str = Field(validation_alias="decimalSeparator")
    thousand_separator: str = Field(validation_alias="thousandSeparator")


class NumberFormatModel(BaseModel):
    """Model representing number formatting in Altinn-metadata api."""

    unit: str
    number: NumberFormatSpecifierModel


class FormattingMetadataModel(BaseModel):
    """Parent model for deserializing all formatting variants."""

    formatting: NumberFormatModel | StringFormatModel | DateFormatModel
