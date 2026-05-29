import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import glob
from pathlib import Path

import pytest

from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.parquedit_storage_connector import ParqueditStorageConnector
from test_parquedit_connector import connector_with_schema
from test_parquedit_connector import parquedit_session
from utils import Form
from utils import load_expected_data


@pytest.mark.parametrize("data", load_expected_data())
def test_processor_parquedit(
    subtests, mocker, connector_with_schema: ParqueditStorageConnector, data: Form
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
        processor._metadata_helper, "get_array_fields", return_value=None
    )
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

            assert len(res) == form.skjemadata_rows

            for field in form.test_fields:
                field_val = (
                    connector_with_schema._get_session()
                    .execute(
                        "SELECT * FROM skjemadata WHERE refnr=? AND feltnavn=?",
                        [form.form_id, field.field_name],
                    )
                    .fetch_df()["verdi"][0]
                )
                assert str(field_val) == field.field_value
