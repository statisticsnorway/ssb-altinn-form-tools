import os
import sys

from ssb_altinn_form_tools.schema import KontaktInfo
from ssb_altinn_form_tools.schema import Skjemadata
from ssb_altinn_form_tools.schema import SkjemaMottak

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy import select

from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.parquedit_storage_connector import ParqueditStorageConnector
from ssb_altinn_form_tools.sqlalchemy_storage_connector import (
    SqlAlchemyStorageConnector,
)
from test_parquedit_connector import connector_with_schema  # noqa: F401
from test_parquedit_connector import parquedit_session  # noqa: F401
from test_sqlalchemy_connector import (
    connector_with_schema as sqlalchemy_connector,  # noqa: F401
)
from test_sqlalchemy_connector import sqlite_session  # noqa: F401
from utils import Form
from utils import load_expected_data


def load_test_cases():
    cases = []
    for data in load_expected_data():
        for form in data.forms:
            cases.append((data, form))
    return cases


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


@pytest.mark.parametrize("data", load_expected_data())
def test_processor_sqlalchemy(
    subtests,
    mocker,
    sqlalchemy_connector: SqlAlchemyStorageConnector,  # noqa: F811
    data: Form,
):

    extractor = DefaultFormExtractor()

    processor = DefaultFormProcessor(
        form_name=data.form_name,
        form_base_path=str(data.form_info.base_path),
        extractor=extractor,
        connector=sqlalchemy_connector,
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
                sqlalchemy_connector._get_session()
                .execute(select(Skjemadata).filter(Skjemadata.refnr == form.form_id))
                .fetchall()
            )

            assert len(res) == form.skjemadata_rows, (
                f"Expected skjemadata to have {form.skjemadata_rows}, but got {len(res)}"
            )

            res = (
                sqlalchemy_connector._get_session()
                .execute(select(KontaktInfo).filter(KontaktInfo.refnr == form.form_id))
                .fetchall()
            )

            assert len(res) == form.kontaktinfo_rows, (
                f"Expected kontaktinfo to have {form.skjemadata_rows} rows, but got {len(res)}"
            )

            res = (
                sqlalchemy_connector._get_session()
                .execute(
                    select(SkjemaMottak).filter(SkjemaMottak.refnr == form.form_id)
                )
                .fetchall()
            )

            assert len(res) == form.skjemamottak_rows, (
                f"Expected skjemamottak to have {form.skjemamottak_rows} rows, but got {len(res)}"
            )

            for field in form.test_fields:
                field_df = (
                    sqlalchemy_connector._get_session()
                    .execute(
                        select(Skjemadata.verdi).filter(
                            Skjemadata.refnr == form.form_id,
                            Skjemadata.feltsti == field.field_name,
                        )
                    )
                    .fetchall()
                )

                assert len(field_df) != 0, (
                    f"Fetched formdata was empty - refnr={form.form_id} AND feltsti={field.field_name}:\n{field_df}"
                )
                field_val = field_df[0][0]

                assert str(field_val) == field.field_value, (
                    f"Expected form field {form.form_id} - {field.field_name} to have value {field.field_value} rows, but got {field_val}"
                )


def test_custom_mapping(
    mocker,
    connector_with_schema: ParqueditStorageConnector,  # noqa: F811
):

    extractor = DefaultFormExtractor()

    mapping = {
        "options_id": "test_id",
        "options": [{"label": "label", "value": "value"}],
        "node_names": ["node_1", "node_2"],
    }

    processor = DefaultFormProcessor(
        form_name="RA0187",
        form_base_path="tests/testdata/RA0187",
        extractor=extractor,
        connector=connector_with_schema,
        checkbox_mapping=[mapping],
    )

    # processor._metadata_helper = metadata
    mocker.patch.object(processor._metadata_helper, "get_array_fields", return_value=[])

    mocker.patch.object(processor._metadata_helper, "_get_metadata", return_value=[])

    processor.process_new_forms()
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM optionslists")
        .fetchall()
    )

    assert any("test_id" in row for row in res)
    assert any("value" in row for row in res)
    assert any("label" in row for row in res)

    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM optionnodes")
        .fetchall()
    )
    assert any("node_1" in row for row in res)
    assert any("node_2" in row for row in res)
