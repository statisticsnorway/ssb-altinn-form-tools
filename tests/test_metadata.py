from pytest_mock import MockerFixture

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


def test_form_metadata_missing_coverage(mocker: MockerFixture) -> None:
    import pytest
    import requests

    from ssb_altinn_form_tools.utils.form_metadata import FormMetadata
    from ssb_altinn_form_tools.utils.form_metadata import _fetch_with_retry
    from ssb_altinn_form_tools.utils.form_metadata import _node_filter

    with pytest.raises(
        ValueError, match="urls must be a non-empty list of URL strings"
    ):
        _fetch_with_retry([], "test_form", "test_resource")

    with pytest.raises(
        ValueError, match="urls must be a non-empty list of URL strings"
    ):
        _fetch_with_retry("not-a-list", "test_form", "test_resource")  # type: ignore[arg-type]

    mock_resp_500 = mocker.MagicMock()
    mock_resp_500.status_code = 500
    mock_resp_500.raise_for_status.side_effect = requests.HTTPError(
        "Internal Server Error"
    )
    mocker.patch("requests.get", return_value=mock_resp_500)
    with pytest.raises(requests.HTTPError, match="Internal Server Error"):
        _fetch_with_retry(
            ["http://dummy.url"],
            "test_form",
            "test_resource",
            max_retries=1,
            delay=0.01,
        )

    mock_resp_418 = mocker.MagicMock()
    mock_resp_418.status_code = 418
    mocker.patch("requests.get", return_value=mock_resp_418)
    res = _fetch_with_retry(
        ["http://dummy1", "http://dummy2"],
        "test_form",
        "test_resource",
        max_retries=2,
        delay=0.01,
    )
    assert res == {}

    mock_resp_empty = mocker.MagicMock()
    mock_resp_empty.status_code = 200
    mock_resp_empty.text = ""
    mocker.patch("requests.get", return_value=mock_resp_empty)
    res = _fetch_with_retry(
        ["http://dummy1"], "test_form", "test_resource", max_retries=1, delay=0.01
    )
    assert res == {}

    test_tree = {"outer": {"inner_key": {"search_key": "found"}}}
    nodes = _node_filter(test_tree, "search_key")
    assert len(nodes) > 0

    mocker.patch(
        "ssb_altinn_form_tools.utils.form_metadata._fetch_with_retry",
        return_value={"something": "else"},
    )
    api = FormMetadata(form_name="RA0485", max_retries=0)
    meta = api._get_metadata(ra_version=1)
    assert meta is not None

    api.array_fields = ["test_field"]
    assert api.get_array_fields() == ["test_field"]

    api.array_fields = None
    mocker.patch(
        "ssb_altinn_form_tools.utils.form_metadata._fetch_with_retry",
        return_value={"properties": {}},
    )
    assert api.get_array_fields(ra_version=1) == []

    api.array_fields = None
    mocker.patch(
        "ssb_altinn_form_tools.utils.form_metadata._fetch_with_retry", return_value={}
    )
    assert api.get_array_fields() == []

    api.array_fields = None
    mocker.patch(
        "ssb_altinn_form_tools.utils.form_metadata._fetch_with_retry",
        side_effect=Exception("Fetch Error"),
    )
    assert api.get_array_fields() is None
