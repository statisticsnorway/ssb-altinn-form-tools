import pytest

from ssb_altinn_form_tools.default_form_extractor import calc_depth
from ssb_altinn_form_tools.default_form_extractor import parse_entries
from ssb_altinn_form_tools.default_form_extractor import parse_index
from ssb_altinn_form_tools.models import FormNode


def test_index_calculations():
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


def test_depth_calulations():
    depth = calc_depth("parent/child")
    assert depth == 2

    depth = calc_depth("parent")
    assert depth == 1

    depth = calc_depth(None)
    assert depth is None

    depth = calc_depth("parent/child/child")
    assert depth == 3


def test_entry_parsing_checkbox():
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


def test_entry_parsing_list():
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


def test_entry_parsing_nested_list():
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


def test_entry_parsing_regular_field():
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
