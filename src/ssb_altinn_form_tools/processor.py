
from typing import Literal
from pydantic import BaseModel, Field
from sqlalchemy import Engine, create_engine, insert
from sqlalchemy.orm import Session, session, sessionmaker
import xmltodict
import glob
import json
import datetime
from pathlib import Path

from schema import skjemadata, enheter, enhetsinfo, kontaktinfo, skjemamottak, Base


class Node(BaseModel):
    sti: str
    navn: str
    verdi: str | None
    dybde: int | None
    indeks: int | None
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
                    dybde=dybde,
                    indeks=ordinal,
                )
            )

    return fields


class AltinnFormProcessor:
    def __init__(self, form: str, engine: Engine, alias_mapping: dict | None = None) -> None:
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

            session = Session(bind=engine)
            
            (base_form_info, base_form_info_model) = self._parse_skjemamottak(
                dictionary, json_data
            )
            session.add(base_form_info_model)

            unit = self._parse_enheter(
                year=base_form_info.aar,
                form=base_form_info.skjema,
                ident=base_form_info.ident,
            )
            session.add(unit)

            form_data = self._parse_skjemadata(
                dictionary,
                year=base_form_info.aar,
                form=base_form_info.skjema,
                ident=base_form_info.ident,
                refnr=base_form_info.refnr,
            )
            session.add_all(form_data)

            contact_info = self._parse_kontaktinfo(
                dictionary,
                year=base_form_info.aar,
                form=base_form_info.skjema,
                ident=base_form_info.ident,
                refnr=base_form_info.refnr,
            )
            session.add(contact_info)

            unit_info = self._parse_enhetsinfo(
                dictionary,
                year=base_form_info.aar,
                ident=base_form_info.ident,
            )
            session.add_all(unit_info)

            session.commit()

    def _parse_skjemadata(
        self, dictionary: dict, year: int, form: str, ident: str, refnr: str
    ) -> list[skjemadata]:
        form_data = dictionary["SkjemaData"]
        parsed_form_data = parse_entries(form_data)

        results = []
        for node in parsed_form_data:
            node_data = skjemadata(
                aar=year,
                skjema=form,
                ident=ident,
                refnr=refnr,
                feltsti=node.sti,
                feltnavn=node.navn,
                verdi=node.verdi,
                dybde=node.dybde,
                indeks=node.indeks,
            )
            results.append(node_data)
        return results

    def _parse_kontaktinfo(
        self, dictionary: dict, year: int, form: str, ident: str, refnr: str
    ) -> kontaktinfo:
        form_data: dict = dictionary["Kontakt"]

        contact_info = KontaktInfo(
            aar=year,
            skjema=form,
            ident=ident,
            refnr=refnr,
            bekreftet_kontaktinfo=form_data.get("kontaktInfoBekreftet") == "1",
            **form_data,
        )

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

    def _parse_skjemamottak(
        self, dictionary: dict, json_data: dict
    ) -> tuple[SkjemaMottak, skjemamottak]:
        form_data: dict = dictionary["InternInfo"]

        data = SkjemaMottak(
            editert="ikke editert", kommentar="", aktiv=True, **form_data, **json_data
        )

        return data, skjemamottak(
            aar=data.aar,
            skjema=data.skjema,
            ident=data.ident,
            refnr=data.refnr,
            kommentar=data.kommentar,
            dato_mottatt=data.dato_mottatt,
            editert=data.editert,
            aktiv=data.aktiv,
        )

    def _parse_enheter(self, year: int, form: str, ident: str) -> enheter:
        unit = Enheter(aar=year, ident=ident, skjema=form)
        return enheter(aar=unit.aar, ident=unit.ident, skjema=unit.skjema)

    def _parse_enhetsinfo(
        self, dictionary: dict, year: int, ident: str
    ) -> list[enhetsinfo]:
        form_data: dict[str, str] = dictionary["InternInfo"]
        info: list[enhetsinfo] = []
        for key, value in form_data.items():
            if key.startswith("enhets"):
                data = EnhetsInfo(aar=year, ident=ident, variabel=key, verdi=value)
                model = enhetsinfo(
                    aar=year, ident=ident, variabel=data.variabel, verdi=data.verdi
                )
                info.append(model)
        return info

engine = create_engine("sqlite:///./db.db", echo=False)
# Create tables
Base.metadata.create_all(engine)

AltinnFormProcessor("RA0187", engine = engine)
AltinnFormProcessor("RA0297", engine = engine)
AltinnFormProcessor("RA0307", engine = engine)
AltinnFormProcessor("RA0366", engine = engine)
AltinnFormProcessor("RA0530", engine = engine)
AltinnFormProcessor("RA0689", engine = engine)
AltinnFormProcessor("RA0745", engine = engine)
