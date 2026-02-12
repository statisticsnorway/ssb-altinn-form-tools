from ssb_altinn_form_tools.schema import kontaktinfo, skjemadata
from typing import Literal
from pydantic import BaseModel, Field
import xmltodict
import glob
import json
import datetime
from pathlib import Path

from .schema import skjemadata, enheter, enhetsinfo, kontaktinfo, skjemamottak


class Node(BaseModel):
    sti: str
    navn: str
    verdi: str | None
    er_attributt: bool
    dybde: int | None
    ordinal: int | None
    parent_path: str | None
    alias: str | None = None


class KontaktInfo(BaseModel):
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


class Enheter(BaseModel):
    aar: int
    ident: str
    skjema: str


class EnhetsInfo(BaseModel):
    aar: int
    ident: str
    variabel: str
    verdi: str | None


class SkjemaMottak(BaseModel):
    aar: int = Field(validation_alias="periodeAAr")
    skjema: str = Field(validation_alias="raNummer")
    ident: str = Field(validation_alias="enhetsIdent")
    refnr: str = Field(validation_alias="altinnReferanse")
    dato_mottatt: datetime.datetime = Field(validation_alias="altinnTidspunktLevert")
    editert: Literal["ferdig editert", "under editering", "ikke editert"]
    kommentar: str
    aktiv: bool


def parse_entries(data: dict | list, parent: None | str = None) -> list[Node]:
    fields = []

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
            try:
                ordinal = int(sti.split("/")[-2])
            except:
                ordinal = None

            if parent:
                dybde = len(parent.split("/"))
            else:
                dybde = None
            fields.append(
                Node(
                    sti=sti,
                    navn=str(key),
                    verdi=value,
                    er_attributt=True,
                    dybde=dybde,
                    ordinal=ordinal,
                    parent_path=parent,
                )
            )

    return fields


class AltinnFormProcessor:
    def __init__(self, form: str, alias_mapping: dict | None = None) -> None:
        form_data_key = f"A3_{form}_M"
        forms = glob.glob(
            f"/home/onyxia/work/ssb-altinn-form-tools/tests/testdata/{form}/**/**/**/**/*.xml"
        )
        for form in forms:
            file_path = Path(form)

            json_name = file_path.name.replace("xml", "json").replace("form", "meta")
            json_path = file_path.with_name(json_name)
            json_data = json.loads(json_path.read_text())
            dictionary: dict = xmltodict.parse(file_path.read_text())[form_data_key]

            base_form_info = self._parse_skjemamottak(dictionary, json_data)

            unit = self._parse_enheter(
                year=base_form_info.aar,
                form=base_form_info.skjema,
                ident=base_form_info.ident,
            )

            form_data = self._parse_skjemadata(
                dictionary,
            )

            form_data_models = self._convert_to_formdata(
                form_data,
                year=base_form_info.aar,
                form=base_form_info.skjema,
                ident=base_form_info.ident,
                refnr=base_form_info.refnr,
            )

            contact_info = self._parse_kontaktinfo(
                dictionary,
                year=base_form_info.aar,
                form=base_form_info.skjema,
                ident=base_form_info.ident,
                refnr=base_form_info.refnr,
            )

            conact_info_model = self._convert_to_sql_contact_data(
                contact_info,
                year=base_form_info.aar,
                form=base_form_info.skjema,
                ident=base_form_info.ident,
                refnr=base_form_info.refnr,
            )
            
            unit_info = self._parse_enhetsinfo(
                dictionary,
                year=base_form_info.aar,
                ident=base_form_info.ident,
            )
            print(contact_info)

    def _convert_to_sql_contact_data(
        self, contact_info: KontaktInfo, year: int, form: str, ident: str, refnr: str
    ) -> kontaktinfo:
        return kontaktinfo(
            aar=year,
            skjema=form,
            ident=ident,
            refnr=refnr,
            kontaktperson=contact_info.kontaktperson,
            epost=contact_info.epost,
            telefon=contact_info.telefon,
            bekreftet_kontaktinfo=contact_info.bekreftet_kontaktinfo,
            kommentar_kontaktinfo=contact_info.kommentar_kontaktinfo,
            kommentar_krevende=contact_info.kommentar_krevende,
        )

    def _convert_to_formdata(
        self, form_data: list[Node], year: int, form: str, ident: str, refnr: str
    ) -> list[skjemadata]:
        result: list[skjemadata] = []
        for item in form_data:
            model = skjemadata(
                aar=year,
                skjema=form,
                ident=ident,
                refnr=refnr,
                feltsti=item.sti,
                feltnavn=item.navn,
                verdi=item.verdi,
                is_attribute=item.er_attributt,
                dybde=item.dybde,
                ordinal=item.ordinal,
                parent_sti=item.parent_path,
            )
            result.append(model)
        return result

    def _parse_skjemadata(self, dictionary: dict) -> list[Node]:
        form_data = dictionary["SkjemaData"]
        parsed_form_data = parse_entries(form_data)
        return parsed_form_data

    def _parse_kontaktinfo(
        self, dictionary: dict, year: int, form: str, ident: str, refnr: str
    ):
        form_data: dict = dictionary["Kontakt"]

        contact_info = KontaktInfo(
            aar=year,
            skjema=form,
            ident=ident,
            refnr=refnr,
            bekreftet_kontaktinfo=form_data.get("kontaktInfoBekreftet") == "1",
            **form_data,
        )
        return contact_info

    def _parse_skjemamottak(self, dictionary: dict, json_data: dict) -> SkjemaMottak:
        form_data: dict = dictionary["InternInfo"]

        return SkjemaMottak(
            editert="ikke editert", kommentar="", aktiv=True, **form_data, **json_data
        )

    def _parse_enheter(self, year: int, form: str, ident: str) -> Enheter:
        return Enheter(aar=year, ident=ident, skjema=form)

    def _parse_enhetsinfo(
        self, dictionary: dict, year: int, ident: str
    ) -> list[EnhetsInfo]:
        form_data: dict[str, str] = dictionary["InternInfo"]
        info: list[EnhetsInfo] = []
        for key, value in form_data.items():
            if key.startswith("enhets"):
                data = EnhetsInfo(aar=year, ident=ident, variabel=key, verdi=value)
                info.append(data)
        return info


AltinnFormProcessor("RA0187")
AltinnFormProcessor("RA0297")
AltinnFormProcessor("RA0307")
AltinnFormProcessor("RA0366")
AltinnFormProcessor("RA0530")
AltinnFormProcessor("RA0689")
AltinnFormProcessor("RA0745")
