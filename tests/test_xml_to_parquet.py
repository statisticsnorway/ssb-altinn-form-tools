import pathlib
from ssb_altinn_form_tools import xml_to_parquet
import pandas as pd

def test_xml_to_parquet(mocker):
    """Mock write and find corresponding parquet file to compare results with."""
    mock_to_parquet = mocker.patch.object(
        pd.DataFrame, "to_parquet", autospec=True
    )

    xml_files = list(
        pathlib.Path("tests/testdata/xml_and_json").rglob("*.xml")
    )

    for form in xml_files:
        xml_to_parquet(str(form), destination_folder="tests/testdata/parquet/")

    assert mock_to_parquet.call_count == len(xml_files)