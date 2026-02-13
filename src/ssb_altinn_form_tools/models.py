from typing import Literal, Self
import datetime

from pydantic import BaseModel, Field


class FormNode(BaseModel):
    feltsti: str
    feltnavn: str
    verdi: str | None
    dybde: int | None
    indeks: int | None
    alias: str | None = None


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


class Unit(BaseModel):
    aar: int
    ident: str
    skjema: str


class UnitInfo(BaseModel):
    aar: int
    ident: str
    variabel: str
    verdi: str | None


class FormReception(BaseModel):
    aar: int = Field(validation_alias="periodeAAr")
    skjema: str = Field(validation_alias="raNummer")
    ident: str = Field(validation_alias="enhetsIdent")
    refnr: str = Field(validation_alias="altinnReferanse")
    dato_mottatt: datetime.datetime = Field(validation_alias="altinnTidspunktLevert")
    editert: Literal["ferdig editert", "under editering", "ikke editert"]
    kommentar: str
    aktiv: bool
