from pathlib import Path

from ssb_altinn_form_tools.default_form_processor import extract_xml_to_dict


def test_xml_convert_to_dict_checkbox():
    checkbox_xml = Path("tests/testdata/xml_patterns/checkbox.xml")
    res = extract_xml_to_dict(checkbox_xml)

    assert res == {"Checkbox": {"hvilkeFylker": "56,03,15,50,31"}}


def test_xml_convert_to_dict_list():
    list_xml = Path("tests/testdata/xml_patterns/list.xml")
    res = extract_xml_to_dict(list_xml)

    assert res == {
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


def test_xml_convert_to_dict_single_list():
    single_list_xml = Path("tests/testdata/xml_patterns/list_single.xml")
    res = extract_xml_to_dict(single_list_xml, array_fields=["RepGruppe"])
    assert res == {
        "List": {
            "SkjemaData": {
                "driftStatus": "1",
                "RepGruppe": [
                    {"ubruktKodeGnuPrefill": "G", "ubruktKodeBasPrisPrefill": "391.48"},
                ],
            }
        }
    }

    res = extract_xml_to_dict(single_list_xml, array_fields=[])
    assert res == {
        "List": {
            "SkjemaData": {
                "driftStatus": "1",
                "RepGruppe": {
                    "ubruktKodeGnuPrefill": "G",
                    "ubruktKodeBasPrisPrefill": "391.48",
                },
            }
        }
    }


def test_xml_convert_to_dict_nested_list():
    nested_list_xml = Path("tests/testdata/xml_patterns/nested_list.xml")
    res = extract_xml_to_dict(nested_list_xml)
    assert res == {
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


def test_xml_convert_to_dict_regular_field():
    regular_fields_xml = Path("tests/testdata/xml_patterns/regular_fields.xml")
    res = extract_xml_to_dict(regular_fields_xml)
    assert res == {
        "Regular": {
            "SkjemaData": {
                "omsForrigePerPrefill": "4545",
                "omsVirksomhetPerioden": "6661",
                "ikkeEksisterende": None,
            }
        }
    }
