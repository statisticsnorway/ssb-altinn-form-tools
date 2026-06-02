import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.parquedit_storage_connector import ParqueditStorageConnector
from test_parquedit_connector import connector_with_schema  # noqa: F401
from test_parquedit_connector import parquedit_session  # noqa: F401
from utils import Form
from utils import load_expected_data


@pytest.mark.parametrize("data", load_expected_data())
def test_processor_parquedit(
    subtests,
    mocker,
    connector_with_schema: ParqueditStorageConnector,  # noqa: F811
    data: Form,
):

    extractor = DefaultFormExtractor()

    processor = DefaultFormProcessor(
        form_name=data.form_name,
        form_base_path=str(data.form_info.base_path),
        extractor=extractor,
        connector=connector_with_schema,
    )

    # processor._metadata_helper = metadata
    mocker.patch.object(
        processor._metadata_helper, "get_array_fields", return_value=data.forced_array
    )

    mocker.patch.object(processor._metadata_helper, "_get_metadata", return_value=[])

    processor.process_new_forms()

    for form in data.forms:
        with subtests.test(
            msg=f"Running sub tests on integrated form - {data.form_name} - {form.form_id}",
        ):
            res = (
                connector_with_schema._get_session()
                .execute("SELECT * FROM skjemadata WHERE refnr=?", [form.form_id])
                .fetchall()
            )

            assert len(res) == form.skjemadata_rows, (
                f"Expected skjemadata to have {form.skjemadata_rows}, but got {len(res)}"
            )

            res = (
                connector_with_schema._get_session()
                .execute("SELECT * FROM kontaktinfo WHERE refnr=?", [form.form_id])
                .fetchall()
            )

            assert len(res) == form.kontaktinfo_rows, (
                f"Expected kontaktinfo to have {form.skjemadata_rows} rows, but got {len(res)}"
            )

            res = (
                connector_with_schema._get_session()
                .execute("SELECT * FROM skjemamottak WHERE refnr=?", [form.form_id])
                .fetchall()
            )

            assert len(res) == form.skjemamottak_rows, (
                f"Expected skjemamottak to have {form.skjemamottak_rows} rows, but got {len(res)}"
            )

            for field in form.test_fields:
                field_df = (
                    connector_with_schema._get_session()
                    .execute(
                        "SELECT * FROM skjemadata WHERE refnr=? AND feltsti=?",
                        [form.form_id, field.field_name],
                    )
                    .fetch_df()
                )

                assert len(field_df) != 0, (
                    f"Fetched formdata was empty - refnr={form.form_id} AND feltsti={field.field_name}:\n{field_df}"
                )
                field_val = field_df["verdi"][0]

                assert str(field_val) == field.field_value, (
                    f"Expected form field {form.form_id} - {field.field_name} to have value {field.field_value} rows, but got {field_val}"
                )
