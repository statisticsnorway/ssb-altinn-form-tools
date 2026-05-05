from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


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
        aar (int): Reporting year.
        skjema (str): Form name or code (e.g., RA-number).
        ident (str): Identifier of the reporting unit.
        refnr (str): Reference number of the submitted form instance.
    """

    aar: str
    skjema: str
    ident: str
    refnr: str

    @staticmethod
    def from_form_data(
        node: FormNode, year: str, form: str, ident: str, refnr: str
    ) -> FormData:
        """Constructs a :class:`FormData` from a :class:`FormNode` and context.

        Args:
            node (FormNode): The base node carrying path/name/value metadata.
            year (int): Reporting year to attach.
            form (str): Form code/name to attach.
            ident (str): Unit identifier to attach.
            refnr (str): Form instance reference to attach.

        Returns:
            FormData: The composed form data entry with context.
        """
        return FormData(
            aar=year, skjema=form, ident=ident, refnr=refnr, **node.model_dump()
        )

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class ContactInfo(BaseModel):
    """Contact information associated with a submitted form.

    Field values are mapped from upstream aliases using Pydantic's `Field(validation_alias=...)`.

    Attributes:
        aar (int): Reporting year.
        skjema (str): Form name or code (e.g., RA-number).
        ident (str): Identifier of the reporting unit.
        refnr (str): Reference number for the submitted form.
        kontaktperson (str): Name of the contact person. Alias: ``kontaktPersonNavn``.
        epost (str | None): Email address. Alias: ``kontaktPersonEpost``.
        telefon (str): Phone number. Alias: ``kontaktPersonTelefon``.
        bekreftet_kontaktinfo (bool): Whether contact info is confirmed.
        kommentar_kontaktinfo (str | None): Free-text comment. Alias: ``kontaktKommentar``.
        kommentar_krevende (str | None): Notes about demanding/complex contact cases.
            Alias: ``kontaktKrevende``.
    """

    aar: str
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
        aar (int): Reporting year.
        ident (str): Unique identifier of the reporting unit.
        skjema (str): Form name or code (e.g., RA-number).
    """

    aar: str
    ident: str
    skjema: str

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class UnitInfo(BaseModel):
    """Represents an additional key-value attribute for a unit.

    Attributes:
        aar (int): Reporting year.
        ident (str): Identifier of the reporting unit.
        variabel (str): Name of the metadata variable.
        verdi (str | None): Value of the metadata variable.
    """

    aar: str
    ident: str
    variabel: str
    verdi: str | None = Field(default=None)

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class FormReception(BaseModel):
    """Reception/submission metadata for a specific form instance.

    This model is configured to **validate by field aliases** to match upstream
    keys from external sources (e.g., Altinn). See `model_config`.

    Attributes:
        aar (int): Reporting year. Alias: ``periodeAAr``.
        skjema (str): Form name/code. Alias: ``raNummer``.
        ident (str): Reporting unit identifier. Alias: ``enhetsIdent``.
        refnr (str): Reference number. Alias: ``altinnReferanse``.
        dato_mottatt (datetime.datetime): Submission timestamp.
            Alias: ``altinnTidspunktLevert``.
        editert (Literal["ferdig editert", "under editering", "ikke editert"]):
            Edit status of the form.
        kommentar (str): Free-text comment associated with reception.
        aktiv (bool): Whether the form instance is considered active.

    Notes:
        ``model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)``
        enables population/validation using both the alias and the field name.
    """

    aar: str = Field(validation_alias="periodeAAr")
    skjema: str = Field(validation_alias="raNummer")
    ident: str = Field(validation_alias="enhetsIdent")
    refnr: str = Field(validation_alias="altinnReferanse")
    delreg: str = Field(validation_alias="delregNr")
    dato_mottatt: datetime.datetime = Field(validation_alias="altinnTidspunktLevert")
    editert: Literal["ferdig editert", "under editering", "ikke editert"]
    kommentar: str
    aktiv: bool

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class FormJsonData(BaseModel):
    """Lightweight JSON metadata accompanying a form file.

    Attributes:
        altinn_reference (str): Reference number for the form instance.
            Alias: ``altinnReferanse``.
        date_deliveres (datetime.datetime): Submission timestamp.
            Alias: ``altinnTidspunktLevert``.
    """

    altinn_reference: str = Field(validation_alias="altinnReferanse")
    date_deliveres: datetime.datetime = Field(validation_alias="altinnTidspunktLevert")

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


class CheckboxConfig(BaseModel):
    """Model for representing checkbox options."""

    field_name: str
    options: list[str]

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"


class Checkboxmodel(BaseModel):
    """Model for representing checkboxes."""

    aar: str
    skjema: str
    ident: str
    refnr: str

    field_name: str
    option: str
    checked: bool
    field_path: str

    def __str__(self) -> str:
        """Returns a pretty-printed JSON representation for debugging."""
        return f"{self.__class__.__name__}(\n" + self.model_dump_json(indent=2) + "\n)"
