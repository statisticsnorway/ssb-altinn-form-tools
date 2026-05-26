import glob
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.default_form_processor import extract_xml_to_dict
from ssb_altinn_form_tools.models import FormJsonData


def test_processor_calls_extractor(mocker: MockerFixture):
    extractor = mocker.Mock()
    connector = mocker.Mock()

    processor = DefaultFormProcessor(
        form_name="RA0187",
        form_base_path="./tests/testdata/RA0187",
        extractor=extractor,
        connector=connector,
    )

    processor.process_new_forms()
    connector.validate_form_is_new.assert_called_once()
    # extractor.extract_klass_calls.assert_called_once()


@pytest.mark.parametrize(
    "glob_path, form_key",
    [
        ("tests/testdata/RA0485/**", "A3_RA0485_M"),
        # ("tests/testdata/RA0187/**", "A3_RA0187_M"),
    ],
)
def test_extractor(glob_path: str, form_key: str):
    processor = DefaultFormExtractor()
    paths = glob.glob(glob_path, recursive=True)
    for path in paths:
        if path.endswith(".xml") is False:
            continue
        xml_path = Path(path)
        json_path = xml_path.with_suffix(".json")
        json_path = json_path.with_name(json_path.name.replace("form", "meta"))
        form_json_data = FormJsonData.model_validate_json(json_path.read_text())
        temp = extract_xml_to_dict(
            xml_path,
            array_fields=[
                "KlassApiKall",
                "klassDatamodellNode",
                "AppMetaData",
                "Turer",
                "TurVarer",
            ],
        )[form_key]
        # print(temp)
        processor.extract_form(temp, form_json_data)
