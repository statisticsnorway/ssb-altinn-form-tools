from ssb_altinn_form_tools.utils.form_metadata import FormMetadata
from ssb_altinn_form_tools.utils.form_metadata import extract_arr_fields


def test_metadata_api() -> None:
    api = FormMetadata(form_name="RA0485", max_retries=0)
    res_options_list = api.extract_options_list("RA0485", "2025")
    assert len(res_options_list) == 32
    assert any(item.options_id == "DagerIDrift" for item in res_options_list)

    res_options_nodes = api.extract_options_nodes("RA0485", "2025")
    assert any(item.option_id == "DagerIDrift" for item in res_options_nodes)
    assert len(res_options_nodes) == 13

    api = FormMetadata(form_name="RA0187", max_retries=0)
    res_options_list = api.extract_options_list("RA0187", "2025")
    assert len(res_options_list) == 0

    res_options_nodes = api.extract_options_nodes("RA0187", "2025")
    assert len(res_options_nodes) == 0


def test_jsonschema_api() -> None:
    api = FormMetadata(form_name="RA0485", max_retries=0)
    res = api.get_array_fields()
    assert res is not None
    assert len(res) == 5
    assert "Turer" in res
    assert "TurVarer" in res

    api = FormMetadata(form_name="RA0187", max_retries=0)
    res = api.get_array_fields()
    assert res is not None
    assert len(res) == 3


def test_array_field_extraction() -> None:
    data = {
        "SkjemaData": {
            "type": "object",
            "properties": {
                "Prefill": {
                    "type": "object",
                    "properties": {
                        "rapporteringsPeriodePre": {
                            "type": "string",
                        },
                        "Turer": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "turID": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "Turer2": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "turID": {"type": "string"},
                        },
                    },
                },
            },
        }
    }
    result = extract_arr_fields(data)
    assert result == ["Turer", "Turer2"]
