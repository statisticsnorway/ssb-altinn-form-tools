import pandas as pd

from ssb_altinn_form_tools import AltinnFormProcessor


def test_ra_0187():
    class TestAltinnFormProcessor(AltinnFormProcessor):
        def __init__(
            self,
            ra_number: str,
            path_to_form_folder: str,
            parquet_ident_field: str,
            parquet_period_mapping: dict[str, str],
            delreg_nr: str | None = None,
            suv_period_mapping: dict[str, str] | None = None,
            suv_ident_field: str | None = None,
        ) -> None:
            super().__init__(
                ra_number,
                path_to_form_folder,
                parquet_ident_field,
                parquet_period_mapping,
                delreg_nr,
                suv_period_mapping,
                suv_ident_field,
            )

        def insert_or_save_data(self, data, primary_keys, table_name):
            expected = pd.read_json(f"tests/testdata/goal/RA-0187A3/{table_name}.json")
            pd.testing.assert_frame_equal(data, expected)
    
    TestAltinnFormProcessor(
        ra_number="RA-0187",
        path_to_form_folder="tests/testdata/parquet/",
        parquet_ident_field="InternInfo_reporteeOrgNr",
        parquet_period_mapping={"aar": "InternInfo_periodeAAr", "maaned": "InternInfo_periodeNummer"},
    ).process_altinn_form("tests/testdata/parquet/RA-0187A3_0055608a311b.parquet")