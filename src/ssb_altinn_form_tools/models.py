from typing import Literal, Self
import datetime

from pydantic import BaseModel, ConfigDict, Field


class FormNode(BaseModel):
    feltsti: str
    feltnavn: str
    verdi: str | None
    dybde: int | None
    indeks: int | None
    alias: str | None = None

    def __str__(self):
        return (
            f"{self.__class__.__name__}(\n"
            + self.model_dump_json(indent=2)
            + "\n)"
        )


class FormData(FormNode):
    aar: int
    skjema: str
    ident: str
    refnr: str

    @staticmethod
    def from_form_data(node: FormNode, year: int, form: str, ident: str, refnr: str):
        return FormData(
            aar=year, skjema=form, ident=ident, refnr=refnr, **node.model_dump()
        )

    def __str__(self):
        return (
            f"{self.__class__.__name__}(\n"
            + self.model_dump_json(indent=2)
            + "\n)"
        )


class ContactInfo(BaseModel):
    aar: int
    skjema: str
    ident: str
    refnr: str
    kontaktperson: str = Field(validation_alias="kontaktPersonNavn")
    epost: str | None = Field(default=None, validation_alias="kontaktPersonEpost")
    telefon: str = Field(validation_alias="kontaktPersonTelefon")
    bekreftet_kontaktinfo: bool
    kommentar_kontaktinfo: str | None = Field(
        default=None, validation_alias="kontaktKommentar"
    )
    kommentar_krevende: str | None = Field(
        default=None, validation_alias="kontaktKrevende"
    )

    def __str__(self):
        return (
            f"{self.__class__.__name__}(\n"
            + self.model_dump_json(indent=2)
            + "\n)"
        )


class Unit(BaseModel):
    aar: int
    ident: str
    skjema: str

    def __str__(self):
        return (
            f"{self.__class__.__name__}(\n"
            + self.model_dump_json(indent=2)
            + "\n)"
        )


class UnitInfo(BaseModel):
    aar: int
    ident: str
    variabel: str
    verdi: str | None

    def __str__(self):
        return (
            f"{self.__class__.__name__}(\n"
            + self.model_dump_json(indent=2)
            + "\n)"
        )


class FormReception(BaseModel):
    aar: int = Field(validation_alias="periodeAAr")
    skjema: str = Field(validation_alias="raNummer")
    ident: str = Field(validation_alias="enhetsIdent")
    refnr: str = Field(validation_alias="altinnReferanse")
    dato_mottatt: datetime.datetime = Field(validation_alias="altinnTidspunktLevert")
    editert: Literal["ferdig editert", "under editering", "ikke editert"]
    kommentar: str
    aktiv: bool

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    def __str__(self):
        return (
            f"{self.__class__.__name__}(\n"
            + self.model_dump_json(indent=2)
            + "\n)"
        )


class FormJsonData(BaseModel):
    altinn_reference: str = Field(validation_alias="altinnReferanse")
    date_deliveres: datetime.datetime = Field(validation_alias="altinnTidspunktLevert")

    def __str__(self):
        return (
            f"{self.__class__.__name__}(\n"
            + self.model_dump_json(indent=2)
            + "\n)"
        )

class ExtractedForm(BaseModel):
    reception: FormReception
    contact_info: ContactInfo
    unit: Unit
    unit_info: list[UnitInfo]
    form_data: list[FormData]

    def __str__(self):
        return (
            f"{self.__class__.__name__}(\n"
            + self.model_dump_json(indent=2)
            + "\n)"
        )