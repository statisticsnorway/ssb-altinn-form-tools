import tempfile

import duckdb
import pytest
from ssb_parquedit import ParquEdit
from ssb_parquedit.connection import DuckDBConnection

from ssb_altinn_form_tools.parquedit_storage_connector import ParqueditStorageConnector


@pytest.fixture(scope="module", name="parquedit")
def parquedit_session():
    temp_dir = tempfile.TemporaryDirectory()

    class LocalDuckDbConnection(DuckDBConnection):  # pyright: ignore
        def __init__(self, db_config: dict[str, str]) -> None:
            conn_str = f"""ATTACH 'ducklake:duckdb:{temp_dir.name}/catalog.db' AS lake (DATA_PATH '{temp_dir.name}/data/')"""
            self._conn = duckdb.connect()
            self._conn.sql(conn_str)
            self._conn.sql("USE lake")

    class LocalParquedit(ParquEdit):  # pyright: ignore
        def __init__(self) -> None:
            self._conn = LocalDuckDbConnection({})

    parquedit_conn = LocalParquedit()

    try:
        yield parquedit_conn
    finally:
        temp_dir.cleanup()


@pytest.fixture(scope="module", name="conn")
def duckdb_session(parquedit: ParquEdit):
    raw = parquedit._get_connection().raw
    try:
        yield raw
    finally:
        raw.close()


@pytest.fixture(scope="module")
def connector_with_schema(parquedit: ParquEdit) -> ParqueditStorageConnector:
    conn = ParqueditStorageConnector(parquedit)
    conn.begin_transaction()
    conn.create_tables_if_not_exists()
    conn.commit()
    return conn


def test_parquedit_conn(parquedit: ParquEdit):
    # conn.execute("CREATE TABLE users (name VARCHAR)")
    conn = ParqueditStorageConnector(parquedit)
    with pytest.raises(RuntimeError):
        conn.create_tables_if_not_exists()

    conn.begin_transaction()
    conn.create_tables_if_not_exists()
    conn.commit()


def test_duckdb_conn(conn: DuckDBConnection):
    conn.execute("SELECT * FROM skjemadata").fetchall()


#    # ParqueditStorageConnector(parquedit)
