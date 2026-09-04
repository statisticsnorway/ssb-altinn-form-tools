import os
import sys

from ssb_altinn_form_tools.schema import KontaktInfo
from ssb_altinn_form_tools.schema import Skjemadata
from ssb_altinn_form_tools.schema import SkjemaMottak

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import select

from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.parquedit_storage_connector import ParqueditStorageConnector
from ssb_altinn_form_tools.sqlalchemy_storage_connector import (
    SqlAlchemyStorageConnector,
)
from test_parquedit_connector import (  # pyright: ignore [reportImplicitRelativeImport]
    connector_with_schema,  # noqa: F401 type: ignore[import-untyped]
)
from test_parquedit_connector import (  # pyright: ignore [reportImplicitRelativeImport]
    parquedit_session,  # noqa: F401 type: ignore[import-untyped]
)
from test_sqlalchemy_connector import (  # pyright: ignore [reportImplicitRelativeImport]
    connector_with_schema as sqlalchemy_connector,  # noqa: F401 type: ignore[import-untyped]
)
from test_sqlalchemy_connector import (  # pyright: ignore [reportImplicitRelativeImport]
    sqlite_session,  # noqa: F401 type: ignore[import-untyped]
)
from utils import Form  # pyright: ignore [reportImplicitRelativeImport]
from utils import FormTestParams  # pyright: ignore [reportImplicitRelativeImport]
from utils import load_expected_data  # pyright: ignore [reportImplicitRelativeImport]


def load_test_cases() -> list[tuple[Form, FormTestParams]]:
    cases = []
    for data in load_expected_data():
        for form in data.forms:
            cases.append((data, form))
    return cases


@pytest.mark.parametrize("data", load_expected_data())
def test_processor_parquedit(
    subtests: pytest.Subtests,
    mocker: MockerFixture,
    connector_with_schema: ParqueditStorageConnector,  # noqa: F811
    data: Form,
) -> None:

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

            assert (
                len(res) == form.skjemadata_rows
            ), f"Expected skjemadata to have {form.skjemadata_rows}, but got {len(res)}"

            res = (
                connector_with_schema._get_session()
                .execute("SELECT * FROM kontaktinfo WHERE refnr=?", [form.form_id])
                .fetchall()
            )

            assert (
                len(res) == form.kontaktinfo_rows
            ), f"Expected kontaktinfo to have {form.skjemadata_rows} rows, but got {len(res)}"

            res = (
                connector_with_schema._get_session()
                .execute("SELECT * FROM skjemamottak WHERE refnr=?", [form.form_id])
                .fetchall()
            )

            assert (
                len(res) == form.skjemamottak_rows
            ), f"Expected skjemamottak to have {form.skjemamottak_rows} rows, but got {len(res)}"

            for field in form.test_fields:
                field_df = (
                    connector_with_schema._get_session()
                    .execute(
                        "SELECT * FROM skjemadata WHERE refnr=? AND feltsti=?",
                        [form.form_id, field.field_name],
                    )
                    .fetch_df()
                )

                assert (
                    len(field_df) != 0
                ), f"Fetched formdata was empty - refnr={form.form_id} AND feltsti={field.field_name}:\n{field_df}"
                field_val = field_df["verdi"][0]

                assert (
                    str(field_val) == field.field_value
                ), f"Expected form field {form.form_id} - {field.field_name} to have value {field.field_value} rows, but got {field_val}"


@pytest.mark.parametrize("data", load_expected_data())
def test_processor_sqlalchemy(
    subtests: pytest.Subtests,
    mocker: MockerFixture,
    sqlalchemy_connector: SqlAlchemyStorageConnector,  # noqa: F811
    data: Form,
) -> None:

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
            res_skjemadata = (
                sqlalchemy_connector._get_session()
                .execute(select(Skjemadata).filter(Skjemadata.refnr == form.form_id))
                .fetchall()
            )

            assert (
                len(res_skjemadata) == form.skjemadata_rows
            ), f"Expected skjemadata to have {form.skjemadata_rows}, but got {len(res_skjemadata)}"

            res_contact_info = (
                sqlalchemy_connector._get_session()
                .execute(select(KontaktInfo).filter(KontaktInfo.refnr == form.form_id))
                .fetchall()
            )

            assert (
                len(res_contact_info) == form.kontaktinfo_rows
            ), f"Expected kontaktinfo to have {form.skjemadata_rows} rows, but got {len(res_contact_info)}"

            res_form_reception = (
                sqlalchemy_connector._get_session()
                .execute(
                    select(SkjemaMottak).filter(SkjemaMottak.refnr == form.form_id)
                )
                .fetchall()
            )

            assert (
                len(res_form_reception) == form.skjemamottak_rows
            ), f"Expected skjemamottak to have {form.skjemamottak_rows} rows, but got {len(res_form_reception)}"

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

                assert (
                    len(field_df) != 0
                ), f"Fetched formdata was empty - refnr={form.form_id} AND feltsti={field.field_name}:\n{field_df}"
                field_val = field_df[0][0]

                assert (
                    str(field_val) == field.field_value
                ), f"Expected form field {form.form_id} - {field.field_name} to have value {field.field_value} rows, but got {field_val}"


def test_custom_mapping(
    mocker: MockerFixture,
    connector_with_schema: ParqueditStorageConnector,  # noqa: F811
) -> None:

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


def test_processor_coverage_additional(
    mocker: MockerFixture,
    sqlalchemy_connector: SqlAlchemyStorageConnector,  # noqa: F811
) -> None:
    from pathlib import Path

    import pytest

    from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
    from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
    from ssb_altinn_form_tools.default_form_processor import extract_xml_to_dict
    from ssb_altinn_form_tools.models import ExtractedForm
    from ssb_altinn_form_tools.models import FormData

    # 1. Test extract_xml_to_dict with invalid non-str keys (line 48)
    mocker.patch("xmltodict.parse", return_value={123: "value"})
    with pytest.raises(TypeError, match="Not all keys are of type 'str'"):
        extract_xml_to_dict(
            Path(
                "tests/testdata/RA0438/2025/3/19/1f13c3d0c905_b3e49da5-29c1-419d-bf51-cb4be669f50b/form_1f13c3d0c905.xml"
            )
        )

    # 2. Test alias mapping (lines 150-155 and 192)
    extractor = DefaultFormExtractor()
    processor = DefaultFormProcessor(
        form_name="RA0187",
        form_base_path="tests/testdata/RA0187",
        extractor=extractor,
        connector=sqlalchemy_connector,
        alias_mapping={"some_field": "new_alias"},
    )
    mock_form_data = FormData(
        feltsti="/some_field",
        feltnavn="some_field",
        verdi="test",
        dybde=1,
        indeks=None,
        alias=None,
        iso_period="2026",
        skjema="RA0187",
        ident="123",
        refnr="ref123",
    )
    import datetime

    from ssb_altinn_form_tools.models import ContactInfo
    from ssb_altinn_form_tools.models import FormReception
    from ssb_altinn_form_tools.models import Unit

    reception = FormReception.model_validate(
        {
            "start_date": datetime.datetime(2026, 1, 1),
            "end_date": datetime.datetime(2026, 1, 31),
            "iso_period": "2026-01",
            "skjema": "RA0187",
            "ident": "123",
            "refnr": "ref123",
            "dato_mottatt": datetime.datetime(2026, 2, 1),
            "status": "ikke editert",
            "kommentar": "",
            "aktiv": True,
            "periodeType": "MND",
            "periodeNummer": "1",
            "periodeAAr": "2026",
        }
    )
    contact = ContactInfo(
        iso_period="2026-01", skjema="RA0187", ident="123", refnr="ref123"
    )
    unit = Unit(iso_period="2026-01", ident="123", skjema="RA0187")
    extracted_form = ExtractedForm(
        reception=reception,
        contact_info=contact,
        unit=unit,
        unit_info=[],
        form_data=[mock_form_data],
    )

    processor._map_alias({"some_field": "new_alias"}, extracted_form)
    assert extracted_form.form_data[0].alias == "new_alias"

    # 3. Test warning when no forms are found (line 312)
    empty_processor = DefaultFormProcessor(
        form_name="NON_EXISTENT",
        form_base_path="tests/non_existent_path",
        extractor=extractor,
        connector=sqlalchemy_connector,
    )
    empty_processor.process_new_forms()

    # 4. Test continue when JSON metadata file does not exist (line 218 and 221->212)
    mocker.patch.object(
        processor,
        "_find_forms",
        return_value=["tests/test_default_processor/nonexistent.xml"],
    )
    processor.process_new_forms()

    # 5. Test when form already exists (lines 196-199)
    mocker.patch.object(
        sqlalchemy_connector, "validate_form_is_new", return_value=False
    )
    mocker.patch.object(
        processor,
        "_find_forms",
        return_value=["tests/testdata/RA0187/2025/1/1/meta_xxx.xml"],
    )
    from ssb_altinn_form_tools.models import FormJsonData

    json_data = FormJsonData.model_validate(
        {
            "altinnReferanse": "ref123",
            "altinnTidspunktLevert": datetime.datetime(2026, 2, 1),
        }
    )
    res = processor._process_form(Path("dummy.xml"), json_data)
    assert res is None

    # 6. Test exception rollback during inserts (lines 280-283)
    mocker.patch.object(sqlalchemy_connector, "validate_form_is_new", return_value=True)
    mocker.patch.object(
        sqlalchemy_connector, "insert_contact_info", side_effect=Exception("DB Error")
    )
    mocker.patch.object(processor, "_process_form", return_value=extracted_form)
    processor._process_forms(["some_path.xml"])

    # 7. Test exception rollback during create_tables_if_not_exists (lines 316-319)
    mocker.patch.object(
        sqlalchemy_connector,
        "create_tables_if_not_exists",
        side_effect=Exception("Create Error"),
    )
    with pytest.raises(Exception, match="Create Error"):
        processor.process_new_forms()

    # 8. Test options already exist branch (line 250->246)
    mocker.patch.object(
        sqlalchemy_connector, "create_tables_if_not_exists", return_value=None
    )
    mocker.patch.object(sqlalchemy_connector, "validate_form_is_new", return_value=True)
    mocker.patch.object(
        sqlalchemy_connector, "validate_options_exists", return_value=True
    )
    mocker.patch.object(sqlalchemy_connector, "insert_contact_info")
    mocker.patch.object(sqlalchemy_connector, "insert_form_data")
    mocker.patch.object(sqlalchemy_connector, "insert_form_data_unedited")
    mocker.patch.object(sqlalchemy_connector, "insert_form_reception")
    mocker.patch.object(sqlalchemy_connector, "insert_unit")
    mocker.patch.object(sqlalchemy_connector, "insert_unit_info")
    processor._process_forms(["some_path.xml"])
