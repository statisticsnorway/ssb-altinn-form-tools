import datetime
import sqlite3
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy import create_engine
from sqlalchemy import select

from ssb_altinn_form_tools.models import ContactInfo
from ssb_altinn_form_tools.models import FormData
from ssb_altinn_form_tools.models import FormReception
from ssb_altinn_form_tools.models import OptionMetadataModel
from ssb_altinn_form_tools.models import OptionModel
from ssb_altinn_form_tools.models import OptionNodes
from ssb_altinn_form_tools.models import Unit
from ssb_altinn_form_tools.models import UnitInfo
from ssb_altinn_form_tools.schema import Enheter
from ssb_altinn_form_tools.schema import EnhetsInfo
from ssb_altinn_form_tools.schema import KontaktInfo
from ssb_altinn_form_tools.schema import OptionNodes as OrmOptionNodes
from ssb_altinn_form_tools.schema import OptionsLists
from ssb_altinn_form_tools.schema import Skjemadata
from ssb_altinn_form_tools.schema import SkjemadataUnedited
from ssb_altinn_form_tools.schema import SkjemaMottak
from ssb_altinn_form_tools.sqlalchemy_storage_connector import (
    SqlAlchemyStorageConnector,
)


@pytest.fixture(scope="session", name="sqlite")
def sqlite_session(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Engine]:
    dir_path = tmp_path_factory.mktemp("data")
    conn = sqlite3.connect(f"{dir_path.resolve()}/catalog.db")
    engine = create_engine("sqlite://", creator=lambda: conn)
    yield engine


@pytest.fixture(scope="session")
def connector_with_schema(sqlite: Engine) -> SqlAlchemyStorageConnector:
    conn = SqlAlchemyStorageConnector(sqlite)
    conn.begin_transaction()
    conn.create_tables_if_not_exists()
    conn.commit()
    return conn


def test_parquedit_conn(sqlite: Engine) -> None:
    conn = SqlAlchemyStorageConnector(sqlite)
    conn.begin_transaction()
    conn.create_tables_if_not_exists()
    conn.commit()


def test_duckdb_conn(connector_with_schema: SqlAlchemyStorageConnector) -> None:
    result = connector_with_schema._get_session().execute(select(Skjemadata)).fetchall()
    assert result is not None


def test_insert_unit_info(connector_with_schema: SqlAlchemyStorageConnector) -> None:
    connector_with_schema.insert_unit_info([])
    res = connector_with_schema._get_session().execute(select(EnhetsInfo)).fetchall()
    assert len(res) == 0

    test_unit = UnitInfo(iso_period="2026", ident="test", variable="var", verdi="verd")
    connector_with_schema.insert_unit_info([test_unit])
    res = connector_with_schema._get_session().execute(select(EnhetsInfo)).fetchall()
    model: EnhetsInfo = res[0][0]

    assert len(res) == 1
    res_unit = UnitInfo.model_validate(model, from_attributes=True)

    assert res_unit == test_unit


def test_insert_unit(connector_with_schema: SqlAlchemyStorageConnector) -> None:
    connector_with_schema.insert_unit([])
    res = connector_with_schema._get_session().execute(select(Enheter)).fetchall()
    assert len(res) == 0

    test_unit = Unit(iso_period="2026", ident="test", skjema="testskjema")
    connector_with_schema.insert_unit([test_unit])
    res = connector_with_schema._get_session().execute(select(Enheter)).fetchall()
    model: Enheter = res[0][0]

    assert len(res) == 1
    res_unit = Unit.model_validate(model, from_attributes=True)

    assert res_unit == test_unit


def test_insert_contact_info(connector_with_schema: SqlAlchemyStorageConnector) -> None:
    res = connector_with_schema._get_session().execute(select(KontaktInfo)).fetchall()

    assert len(res) == 0

    test_unit = ContactInfo(
        iso_period="2026", ident="test", skjema="testskjema", refnr="test_ref"
    )
    connector_with_schema.insert_contact_info([test_unit])
    res = connector_with_schema._get_session().execute(select(KontaktInfo)).fetchall()

    model: KontaktInfo = res[0][0]

    assert len(res) == 1
    res_unit = ContactInfo.model_validate(model, from_attributes=True)

    assert res_unit == test_unit


def test_insert_form_reception(
    connector_with_schema: SqlAlchemyStorageConnector,
) -> None:
    connector_with_schema.insert_form_reception([])
    res = connector_with_schema._get_session().execute(select(SkjemaMottak)).fetchall()
    assert len(res) == 0

    test_unit = FormReception.model_validate(
        dict(
            iso_period="2026",
            ident="test",
            skjema="testskjema",
            refnr="test_ref",
            status="under editering",
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
    connector_with_schema.insert_form_reception([test_unit])
    res = connector_with_schema._get_session().execute(select(SkjemaMottak)).fetchall()
    model: SkjemaMottak = res[0][0]

    assert len(res) == 1
    res_unit = FormReception.model_validate(model.__dict__)

    assert res_unit == test_unit


def test_insert_form_data(connector_with_schema: SqlAlchemyStorageConnector) -> None:
    connector_with_schema.insert_form_data([])
    res = connector_with_schema._get_session().execute(select(Skjemadata)).fetchall()
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
    res = connector_with_schema._get_session().execute(select(Skjemadata)).fetchall()
    model: Skjemadata = res[0][0]

    assert len(res) == 1
    res_unit = FormData.model_validate(model, from_attributes=True)

    assert res_unit == test_unit


def test_insert_form_data_unedited(
    connector_with_schema: SqlAlchemyStorageConnector,
) -> None:
    connector_with_schema.insert_form_data_unedited([])
    res = (
        connector_with_schema._get_session()
        .execute(select(SkjemadataUnedited))
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
        .execute(select(SkjemadataUnedited))
        .fetchall()
    )
    model: SkjemadataUnedited = res[0][0]

    assert len(res) == 1
    res_unit = FormData.model_validate(model, from_attributes=True)

    assert res_unit == test_unit


def test_insert_option_list(connector_with_schema: SqlAlchemyStorageConnector) -> None:
    connector_with_schema.insert_option_list([])
    res = connector_with_schema._get_session().execute(select(OptionsLists)).fetchall()
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
    res = connector_with_schema._get_session().execute(select(OptionsLists)).fetchall()
    model: OptionsLists = res[0][0]

    assert len(res) == 1
    assert model.iso_period == test_unit.iso_period  # pyright: ignore
    assert model.skjema == test_unit.skjema  # pyright: ignore
    assert model.label == next(iter(test_unit.options)).label  # pyright: ignore
    assert model.value == next(iter(test_unit.options)).value  # pyright: ignore
    assert model.options_id == test_unit.options_id  # pyright: ignore


def test_insert_option_nodes(connector_with_schema: SqlAlchemyStorageConnector) -> None:
    connector_with_schema.insert_option_node([])
    res = (
        connector_with_schema._get_session().execute(select(OrmOptionNodes)).fetchall()
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
        connector_with_schema._get_session().execute(select(OrmOptionNodes)).fetchall()
    )

    model: OrmOptionNodes = res[0][0]

    assert len(res) == 1
    assert model.iso_period == test_unit.iso_period  # pyright: ignore
    assert model.skjema == test_unit.skjema  # pyright: ignore
    assert model.node_name == next(iter(test_unit.node_list))  # pyright: ignore
    assert model.options_id == test_unit.option_id  # pyright: ignore
