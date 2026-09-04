from typing import Any

import pytest

from ssb_altinn_form_tools.default_form_extractor import calc_depth
from ssb_altinn_form_tools.default_form_extractor import parse_entries
from ssb_altinn_form_tools.default_form_extractor import parse_index
from ssb_altinn_form_tools.models import FormNode


def test_index_calculations() -> None:
    index = parse_index("parent/1/child")
    assert index == 1

    index = parse_index("parent/1/child/2/child")
    assert index == 2

    index = parse_index("parent/child/child")
    assert index is None

    with pytest.raises(IndexError, match="list index out of range"):
        index = parse_index("parent")
        assert index is None

    index = parse_index(None)
    assert index is None


def test_depth_calulations() -> None:
    depth = calc_depth("parent/child")
    assert depth == 2

    depth = calc_depth("parent")
    assert depth == 1

    depth = calc_depth(None)
    assert depth is None

    depth = calc_depth("parent/child/child")
    assert depth == 3


def test_entry_parsing_checkbox() -> None:
    data = {"Checkbox": {"hvilkeFylker": "56,03,15,50,31"}}
    result = parse_entries(data)
    assert result == [
        FormNode(
            feltsti="/Checkbox/hvilkeFylker",
            feltnavn="hvilkeFylker",
            verdi="56,03,15,50,31",
            dybde=2,
            indeks=None,
            alias=None,
        )
    ]


def test_entry_parsing_list() -> None:
    data = {
        "List": {
            "SkjemaData": {
                "driftStatus": "1",
                "RepGruppe": [
                    {"ubruktKodeGnuPrefill": "G", "ubruktKodeBasPrisPrefill": "391.48"},
                    {"ubruktKodeGnuPrefill": "G", "komplNeiSolgtForrPerJaNei": "0"},
                    {"ubruktKodeGnuPrefill": "G", "ubruktKodeBasPrisPrefill": "293.7"},
                ],
            }
        }
    }
    result = parse_entries(data)
    assert result == [
        FormNode(
            feltsti="/List/SkjemaData/driftStatus",
            feltnavn="driftStatus",
            verdi="1",
            dybde=3,
            indeks=None,
            alias=None,
        ),
        FormNode(
            feltsti="/List/SkjemaData/RepGruppe/0/ubruktKodeGnuPrefill",
            feltnavn="ubruktKodeGnuPrefill",
            verdi="G",
            dybde=5,
            indeks=0,
            alias=None,
        ),
        FormNode(
            feltsti="/List/SkjemaData/RepGruppe/0/ubruktKodeBasPrisPrefill",
            feltnavn="ubruktKodeBasPrisPrefill",
            verdi="391.48",
            dybde=5,
            indeks=0,
            alias=None,
        ),
        FormNode(
            feltsti="/List/SkjemaData/RepGruppe/1/ubruktKodeGnuPrefill",
            feltnavn="ubruktKodeGnuPrefill",
            verdi="G",
            dybde=5,
            indeks=1,
            alias=None,
        ),
        FormNode(
            feltsti="/List/SkjemaData/RepGruppe/1/komplNeiSolgtForrPerJaNei",
            feltnavn="komplNeiSolgtForrPerJaNei",
            verdi="0",
            dybde=5,
            indeks=1,
            alias=None,
        ),
        FormNode(
            feltsti="/List/SkjemaData/RepGruppe/2/ubruktKodeGnuPrefill",
            feltnavn="ubruktKodeGnuPrefill",
            verdi="G",
            dybde=5,
            indeks=2,
            alias=None,
        ),
        FormNode(
            feltsti="/List/SkjemaData/RepGruppe/2/ubruktKodeBasPrisPrefill",
            feltnavn="ubruktKodeBasPrisPrefill",
            verdi="293.7",
            dybde=5,
            indeks=2,
            alias=None,
        ),
    ]


def test_entry_parsing_nested_list() -> None:
    data = {
        "NestedList": {
            "SkjemaData": {
                "NyEngHusdyrGjodsGroup": [
                    {
                        "NyEngHusdyrGjodsNavn": "Gris, fastgjødsel",
                        "NyEngHusdyrAntallGjods": "2",
                        "NyEngHusdyrGjodslinger": [
                            {
                                "NyEngHGjodslingAarstid": "0",
                                "NyEngHGjodslingMengde": "3333",
                            },
                            {
                                "NyEngHGjodslingAreal": "32",
                                "NyEngHGjodslingMengde": "32",
                            },
                        ],
                    },
                    {
                        "NyEngHusdyrGjodsID": "080",
                        "NyEngHusdyrGjodsNavn": "Gris, talle",
                        "NyEngHusdyrGjodslinger": {
                            "NyEngHGjodslingAarstid": "1",
                            "NyEngHGjodslingAreal": "32",
                        },
                    },
                ]
            }
        }
    }
    result = parse_entries(data)
    assert result == [
        FormNode(
            feltsti="/NestedList/SkjemaData/NyEngHusdyrGjodsGroup/0/NyEngHusdyrGjodsNavn",
            feltnavn="NyEngHusdyrGjodsNavn",
            verdi="Gris, fastgjødsel",
            dybde=5,
            indeks=0,
            alias=None,
        ),
        FormNode(
            feltsti="/NestedList/SkjemaData/NyEngHusdyrGjodsGroup/0/NyEngHusdyrAntallGjods",
            feltnavn="NyEngHusdyrAntallGjods",
            verdi="2",
            dybde=5,
            indeks=0,
            alias=None,
        ),
        FormNode(
            feltsti="/NestedList/SkjemaData/NyEngHusdyrGjodsGroup/0/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAarstid",
            feltnavn="NyEngHGjodslingAarstid",
            verdi="0",
            dybde=7,
            indeks=0,
            alias=None,
        ),
        FormNode(
            feltsti="/NestedList/SkjemaData/NyEngHusdyrGjodsGroup/0/NyEngHusdyrGjodslinger/0/NyEngHGjodslingMengde",
            feltnavn="NyEngHGjodslingMengde",
            verdi="3333",
            dybde=7,
            indeks=0,
            alias=None,
        ),
        FormNode(
            feltsti="/NestedList/SkjemaData/NyEngHusdyrGjodsGroup/0/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAreal",
            feltnavn="NyEngHGjodslingAreal",
            verdi="32",
            dybde=7,
            indeks=1,
            alias=None,
        ),
        FormNode(
            feltsti="/NestedList/SkjemaData/NyEngHusdyrGjodsGroup/0/NyEngHusdyrGjodslinger/1/NyEngHGjodslingMengde",
            feltnavn="NyEngHGjodslingMengde",
            verdi="32",
            dybde=7,
            indeks=1,
            alias=None,
        ),
        FormNode(
            feltsti="/NestedList/SkjemaData/NyEngHusdyrGjodsGroup/1/NyEngHusdyrGjodsID",
            feltnavn="NyEngHusdyrGjodsID",
            verdi="080",
            dybde=5,
            indeks=1,
            alias=None,
        ),
        FormNode(
            feltsti="/NestedList/SkjemaData/NyEngHusdyrGjodsGroup/1/NyEngHusdyrGjodsNavn",
            feltnavn="NyEngHusdyrGjodsNavn",
            verdi="Gris, talle",
            dybde=5,
            indeks=1,
            alias=None,
        ),
        FormNode(
            feltsti="/NestedList/SkjemaData/NyEngHusdyrGjodsGroup/1/NyEngHusdyrGjodslinger/NyEngHGjodslingAarstid",
            feltnavn="NyEngHGjodslingAarstid",
            verdi="1",
            dybde=6,
            indeks=None,
            alias=None,
        ),
        FormNode(
            feltsti="/NestedList/SkjemaData/NyEngHusdyrGjodsGroup/1/NyEngHusdyrGjodslinger/NyEngHGjodslingAreal",
            feltnavn="NyEngHGjodslingAreal",
            verdi="32",
            dybde=6,
            indeks=None,
            alias=None,
        ),
    ]


def test_entry_parsing_regular_field() -> None:
    data = {
        "Regular": {
            "SkjemaData": {
                "omsForrigePerPrefill": "4545",
                "omsVirksomhetPerioden": "6661",
            }
        }
    }
    result = parse_entries(data)
    assert result == [
        FormNode(
            feltsti="/Regular/SkjemaData/omsForrigePerPrefill",
            feltnavn="omsForrigePerPrefill",
            verdi="4545",
            dybde=3,
            indeks=None,
            alias=None,
        ),
        FormNode(
            feltsti="/Regular/SkjemaData/omsVirksomhetPerioden",
            feltnavn="omsVirksomhetPerioden",
            verdi="6661",
            dybde=3,
            indeks=None,
            alias=None,
        ),
    ]


def test_parse_entries_invalid_type() -> None:
    with pytest.raises(UnboundLocalError):
        parse_entries(123)  # type: ignore[arg-type]


def test_default_extractor_extract_unit_info_invalid_types() -> None:
    from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor

    extractor = DefaultFormExtractor()

    with pytest.raises(TypeError, match="form_data must be type dict"):
        extractor.extract_unit_info({"InternInfo": "not-a-dict"}, ident="123", iso_period="2026")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Key must be type str"):
        extractor.extract_unit_info({"InternInfo": {123: "value"}}, ident="123", iso_period="2026")  # type: ignore[arg-type]


def test_models_str_methods() -> None:
    import datetime

    from ssb_altinn_form_tools.models import ContactInfo
    from ssb_altinn_form_tools.models import ExtractedForm
    from ssb_altinn_form_tools.models import FormData
    from ssb_altinn_form_tools.models import FormJsonData
    from ssb_altinn_form_tools.models import FormNode
    from ssb_altinn_form_tools.models import FormReception
    from ssb_altinn_form_tools.models import Unit
    from ssb_altinn_form_tools.models import UnitInfo

    # 1. FormNode
    node = FormNode(feltsti="/path", feltnavn="name", verdi="val", dybde=2)
    assert "FormNode" in str(node)

    # 2. FormData
    form_data = FormData(
        feltsti="/path",
        feltnavn="name",
        verdi="val",
        dybde=2,
        iso_period="2026-01",
        skjema="RA0187",
        ident="123",
        refnr="ref123",
    )
    assert "FormData" in str(form_data)

    # 3. ContactInfo
    contact = ContactInfo(
        iso_period="2026-01", skjema="RA0187", ident="123", refnr="ref123"
    )
    assert "ContactInfo" in str(contact)

    # 4. Unit
    unit = Unit(iso_period="2026-01", ident="123", skjema="RA0187")
    assert "Unit" in str(unit)

    # 5. UnitInfo
    unit_info = UnitInfo(iso_period="2026-01", ident="123", variable="var", verdi="val")
    assert "UnitInfo" in str(unit_info)

    # 6. FormReception
    reception = FormReception.model_validate(
        {
            "start_date": datetime.datetime(2026, 1, 1),
            "end_date": datetime.datetime(2026, 1, 31),
            "iso_period": "2026-01",
            "skjema": "RA0187",
            "ident": "123",
            "refnr": "ref123",
            "dato_mottatt": datetime.datetime(2026, 2, 1),
            "status": "ikke editert",
            "kommentar": "",
            "aktiv": True,
            "periodeType": "MND",
            "periodeNummer": "1",
            "periodeAAr": "2026",
        }
    )
    assert "FormReception" in str(reception)

    # 7. FormJsonData
    json_data = FormJsonData.model_validate(
        {
            "altinnReferanse": "ref123",
            "altinnTidspunktLevert": datetime.datetime(2026, 2, 1),
        }
    )
    assert "FormJsonData" in str(json_data)

    # 8. ExtractedForm
    extracted = ExtractedForm(
        reception=reception,
        contact_info=contact,
        unit=unit,
        unit_info=[unit_info],
        form_data=[form_data],
    )
    assert "ExtractedForm" in str(extracted)


def test_form_reception_validation_errors() -> None:
    import datetime

    import pytest
    from pydantic import ValidationError

    from ssb_altinn_form_tools.models import FormReception

    # Raise exception in `.get` for periodeType (Line 221-222)
    class BadDict(dict):
        def get(self, key: Any, /) -> Any | None:
            if key == "periodeType":
                raise ValueError("Bad get")
            return None

    with pytest.raises(ValidationError, match="periodeType could not be validated"):
        FormReception.model_validate(BadDict())

    # Raise exception in periodeNummer (Line 234-235)
    bad_nummer_data = {
        "periodeType": "MND",
        "periodeNummer": "not-an-int",
        "periodeAAr": "2026",
        "raNummer": "RA0187",
        "enhetsIdent": "123",
        "altinnReferanse": "ref123",
        "altinnTidspunktLevert": datetime.datetime(2026, 2, 1),
        "status": "ikke editert",
        "kommentar": "",
        "aktiv": True,
    }
    with pytest.raises(ValidationError, match="periodeNummer could not be validated"):
        FormReception.model_validate(bad_nummer_data)

    # Raise exception in periodeAAr (Line 242-243)
    bad_year_data = {
        "periodeType": "MND",
        "periodeNummer": "1",
        "periodeAAr": "not-an-int",
        "raNummer": "RA0187",
        "enhetsIdent": "123",
        "altinnReferanse": "ref123",
        "altinnTidspunktLevert": datetime.datetime(2026, 2, 1),
        "status": "ikke editert",
        "kommentar": "",
        "aktiv": True,
    }
    with pytest.raises(ValidationError, match="periodeAar could not be validated"):
        FormReception.model_validate(bad_year_data)

    # Raise exception in period_type (Line 273)
    bad_type_data = {
        "periodeType": "INVALID",
        "periodeNummer": "1",
        "periodeAAr": "2026",
        "raNummer": "RA0187",
        "enhetsIdent": "123",
        "altinnReferanse": "ref123",
        "altinnTidspunktLevert": datetime.datetime(2026, 2, 1),
        "status": "ikke editert",
        "kommentar": "",
        "aktiv": True,
    }
    with pytest.raises(ValidationError, match="period_type could not be validated"):
        FormReception.model_validate(bad_type_data)
