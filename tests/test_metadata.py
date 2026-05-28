import pytest

from ssb_altinn_form_tools.utils.form_metadata import FormMetadata
from ssb_altinn_form_tools.utils.form_metadata import extract_arr_fields

from .utils import FormInfo
from .utils import form_paths


@pytest.fixture(params=form_paths())
def form_info_fixture(request) -> str:
    return request.param


def test_metadata_api(form_info_fixture: FormInfo):
    api = FormMetadata(form_name=form_info_fixture.form_name)


def test_jsonschema_api(form_info_fixture: FormInfo):
    api = FormMetadata(form_name=form_info_fixture.form_name)
    # api.extract_options_list(form_info_fixture.form_name, "2025")


def test_array_field_extraction():
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
