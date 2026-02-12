from typing import Literal
from pydantic import BaseModel
import xmltodict
import glob
import json
import datetime
from pathlib import Path


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
    kontaktperson: str
    epost: str
    telefon: str
    bekreftet_kontaktinfo: bool
    kommentar_kontaktinfo: str | None
    kommentar_krevende: str | None


class Enheter(BaseModel):
    aar: int
    ident: str
    skjema: str


class EnhetsInfo(BaseModel):
    aar: int
    ident: str
    variabel: str
    verdi: str


class SkjemaMottak(BaseModel):
    aar: int
    skjema: str
    ident: str
    refnr: str
    dato_mottatt: datetime.datetime
    editert: Literal["ferdig editert", "under editering", "ikke editert"]
    kommentar: str
    aktiv: bool


forms = glob.glob(
    "/home/onyxia/work/ssb-altinn-form-tools/tests/testdata/**/**/**/**/**/*.xml"
)


def parse_entries(data: dict | list, parent: None | str = None) -> list[Node]:
    fields = []

    if isinstance(data, list):
        iterator = enumerate(data)
    elif isinstance(data, dict):
        iterator = data.items()

    for key, value in iterator:

        sti = f"{parent if parent else ''}/{key}"
        if isinstance(value, list):
            fields.extend(parse_entries(value, parent=sti))
        elif isinstance(value, dict):
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

            skjemamottak = self._parse_skjemamottak(dictionary, json_data)
            self._parse_skjemadata(
                dictionary,
                year=skjemamottak.aar,
                form=skjemamottak.skjema,
                ident=skjemamottak.ident,
                refnr=skjemamottak.refnr,
            )
            self._parse_kontaktinfo(
                dictionary,
                year=skjemamottak.aar,
                form=skjemamottak.skjema,
                ident=skjemamottak.ident,
                refnr=skjemamottak.refnr,
            )

    def _parse_skjemadata(
        self, dictionary: dict, year: int, form: str, ident: str, refnr: str
    ):
        form_data = dictionary["SkjemaData"]
        parsed_form_data = parse_entries(form_data)
        print(parsed_form_data)

    def _parse_kontaktinfo(
        self, dictionary: dict, year: int, form: str, ident: str, refnr: str
    ):
        form_data: dict = dictionary["Kontakt"]
        epost: str | None = form_data.get("kontaktPersonEpost", "")
        if epost is None:
            epost = ""
            
        contact_info = KontaktInfo(
            aar=year,
            skjema=form,
            ident=ident,
            refnr=refnr,
            kontaktperson=form_data.get("kontaktPersonNavn", ""),
            epost=epost,
            telefon=form_data.get("kontaktPersonTelefon", ""),
            kommentar_kontaktinfo=form_data.get("kontaktPersonTelefon"),
            kommentar_krevende=form_data.get("kontaktKrevende"),
            bekreftet_kontaktinfo=form_data.get("kontaktInfoBekreftet") == "1",
        )
        return contact_info

    def _parse_skjemamottak(self, dictionary: dict, json_data: dict):
        form_data: dict = dictionary["InternInfo"]
        delivered_date = json_data.get("altinnTidspunktLevert")
        if delivered_date is None:
            raise RuntimeError(
                "Delivered date is not in form and should be. There might be something wrong with the form"
            )
        dt = datetime.datetime.fromisoformat(delivered_date)

        refnr = json_data.get("altinnReferanse")
        if refnr is None:
            raise RuntimeError(
                "Reference number is not in form and should be. There might be something wrong with the form. Eg. the json file is not present"
            )

        year: str = form_data.get("periodeAAr", "")

        try:
            aar = int(year)
        except:
            raise RuntimeError("Year could not be parsed")

        return SkjemaMottak(
            aar=aar,
            skjema=form_data.get("raNummer", ""),
            ident=form_data.get("enhetsIdent", ""),
            refnr=refnr,
            dato_mottatt=dt,
            editert="ikke editert",
            kommentar="",
            aktiv=True,
        )

    def _parse_enheter(
        self, dictionary: dict, year: int, form: str, ident: str, refnr: str
    ):
        pass

    def _parse_enhetsinfo(
        self, dictionary: dict, year: int, form: str, ident: str, refnr: str
    ):
        pass


AltinnFormProcessor("RA0187")
AltinnFormProcessor("RA0297")
AltinnFormProcessor("RA0307")
AltinnFormProcessor("RA0366")
AltinnFormProcessor("RA0530")
AltinnFormProcessor("RA0689")
AltinnFormProcessor("RA0745")
