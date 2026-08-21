import datetime
import tempfile

import duckdb
import pytest
from ssb_parquedit import ParquEdit
from ssb_parquedit.connection import DuckDBConnection

from ssb_altinn_form_tools.models import ContactInfo
from ssb_altinn_form_tools.models import FormData
from ssb_altinn_form_tools.models import FormReception
from ssb_altinn_form_tools.models import OptionMetadataModel
from ssb_altinn_form_tools.models import OptionModel
from ssb_altinn_form_tools.models import OptionNodes
from ssb_altinn_form_tools.models import Unit
from ssb_altinn_form_tools.models import UnitInfo
from ssb_altinn_form_tools.parquedit_storage_connector import ParqueditStorageConnector


@pytest.fixture(scope="session", name="parquedit")
def parquedit_session():
    temp_dir = tempfile.TemporaryDirectory()

    parquedit_conn = ParquEdit.local(f"{temp_dir.name}")

    try:
        yield parquedit_conn
    finally:
        temp_dir.cleanup()


@pytest.fixture(scope="session")
def connector_with_schema(parquedit: ParquEdit) -> ParqueditStorageConnector:
    conn = ParqueditStorageConnector(parquedit)
    conn.begin_transaction()
    conn.create_tables_if_not_exists()
    conn.commit()
    return conn


def test_parquedit_conn(parquedit: ParquEdit):
    conn = ParqueditStorageConnector(parquedit)
    #with pytest.raises(RuntimeError):
    #    conn.create_tables_if_not_exists()

    conn.begin_transaction()
    conn.create_tables_if_not_exists()
    conn.commit()


def test_duckdb_conn(connector_with_schema: ParqueditStorageConnector):
    connector_with_schema._get_session().execute("SELECT * FROM skjemadata").fetchall()


def test_insert_unit_info(connector_with_schema: ParqueditStorageConnector):
    connector_with_schema.insert_unit_info([])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM enhetsinfo")
        .fetchall()
    )
    assert len(res) == 0

    test_unit = UnitInfo(iso_period="2026", ident="test", variabel="var", verdi="verd")
    connector_with_schema.insert_unit_info([test_unit])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM enhetsinfo")
        .fetchdf()
        .to_dict(orient="records")
    )
    assert len(res) == 1
    res_unit = UnitInfo(**res[0])

    assert res_unit == test_unit


def test_insert_unit(connector_with_schema: ParqueditStorageConnector):
    connector_with_schema.insert_unit([])
    res = (
        connector_with_schema._get_session().execute("SELECT * FROM enheter").fetchall()
    )
    assert len(res) == 0

    test_unit = Unit(iso_period="2026", ident="test", skjema="testskjema")
    connector_with_schema.insert_unit([test_unit])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM enheter")
        .fetchdf()
        .to_dict(orient="records")
    )
    assert len(res) == 1
    res_unit = Unit(**res[0])

    assert res_unit == test_unit


def test_insert_contact_info(connector_with_schema: ParqueditStorageConnector):
    connector_with_schema.insert_contact_info([])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM kontaktinfo")
        .fetchall()
    )
    assert len(res) == 0

    test_unit = ContactInfo(
        iso_period="2026", ident="test", skjema="testskjema", refnr="test_ref"
    )
    connector_with_schema.insert_contact_info([test_unit])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM kontaktinfo")
        .fetchdf()
        .to_dict(orient="records")
    )
    assert len(res) == 1
    res_unit = ContactInfo(**res[0])

    assert res_unit == test_unit


def test_insert_form_reception(connector_with_schema: ParqueditStorageConnector):
    connector_with_schema.insert_form_reception([])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM skjemamottak")
        .fetchall()
    )
    assert len(res) == 0

    test_unit = FormReception.model_validate(
        dict(
            iso_period="2026",
            ident="test",
            skjema="testskjema",
            refnr="test_ref",
            editert="under editering",
            kommentar="komm",
            aktiv=True,
            start_date=datetime.datetime(2026, 1, 1),
            end_date=datetime.datetime(2026, 12, 31),
            dato_mottatt=datetime.datetime(2026, 5, 1),
            periodeAAr=2026,
            periodeType="AAR",
            periodeNummer=1,
        )
    )
    print(test_unit)
    connector_with_schema.insert_form_reception([test_unit])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM skjemamottak")
        .fetch_df()
        .to_dict(orient="records")
    )
    print(res)
    assert len(res) == 1
    res_unit = FormReception(**res[0])

    assert res_unit == test_unit


def test_insert_form_data(connector_with_schema: ParqueditStorageConnector):
    connector_with_schema.insert_form_data([])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM skjemadata")
        .fetchall()
    )
    assert len(res) == 0
    test_unit = FormData(
        iso_period="2026",
        ident="test",
        skjema="testskjema",
        refnr="test_ref",
        feltsti="sti",
        feltnavn="navn",
    )

    connector_with_schema.insert_form_data([test_unit])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM skjemadata")
        .fetch_df()
        .to_dict(orient="records")
    )
    assert len(res) == 1
    res_unit = FormData(**res[0])

    assert res_unit == test_unit


def test_insert_form_data_unedited(connector_with_schema: ParqueditStorageConnector):
    connector_with_schema.insert_form_data_unedited([])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM skjemadata_unedited")
        .fetchall()
    )
    assert len(res) == 0
    test_unit = FormData(
        iso_period="2026",
        ident="test",
        skjema="testskjema",
        refnr="test_ref",
        feltsti="sti",
        feltnavn="navn",
    )

    connector_with_schema.insert_form_data_unedited([test_unit])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM skjemadata_unedited")
        .fetch_df()
        .to_dict(orient="records")
    )
    assert len(res) == 1
    res_unit = FormData(**res[0])

    assert res_unit == test_unit


def test_insert_option_list(connector_with_schema: ParqueditStorageConnector):
    connector_with_schema.insert_option_list([])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM optionslists")
        .fetchall()
    )
    assert len(res) == 0
    test_unit = OptionMetadataModel(
        iso_period="2026",
        skjema="testskjema",
        options=[OptionModel(value="test_val", label="test_label")],
        options_id="opsjons_id",
        options_url=None,
        node_name="nodenavn",
    )

    connector_with_schema.insert_option_list([test_unit])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM optionslists")
        .fetch_df()
        .to_dict(orient="records")
    )

    assert len(res) == 1
    assert res[0]["iso_period"] == test_unit.iso_period
    assert res[0]["skjema"] == test_unit.skjema
    assert res[0]["label"] == next(iter(test_unit.options)).label
    assert res[0]["value"] == next(iter(test_unit.options)).value
    assert res[0]["options_id"] == test_unit.options_id


def test_insert_option_nodes(connector_with_schema: ParqueditStorageConnector):
    connector_with_schema.insert_option_node([])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM optionnodes")
        .fetchall()
    )
    assert len(res) == 0
    test_unit = OptionNodes(
        iso_period="2026",
        skjema="testskjema",
        node_list=set(["node_1"]),
        option_id="opsjons_id",
    )

    connector_with_schema.insert_option_node([test_unit])
    res = (
        connector_with_schema._get_session()
        .execute("SELECT * FROM optionnodes")
        .fetch_df()
        .to_dict(orient="records")
    )

    assert len(res) == 1
    assert res[0]["iso_period"] == test_unit.iso_period
    assert res[0]["skjema"] == test_unit.skjema
    assert res[0]["node_name"] == next(iter(test_unit.node_list))
    assert res[0]["options_id"] == test_unit.option_id
