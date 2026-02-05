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

    calls = mock_to_parquet.call_args_list

    dfs = [call.args[0] for call in calls]      # DataFrame instances
    paths = [call.kwargs.get("path") for call in calls]    # parquet paths

    for actual_df, path in zip(dfs, paths):
        expected_df = pd.read_parquet(path)
        
        # Ensure missing values are the same type
        actual_df = actual_df.fillna(pd.NA)
        expected_df = expected_df.fillna(pd.NA)

        # Proper comparison
        pd.testing.assert_frame_equal(actual_df, expected_df)