import logging

import duckdb
from ssb_parquedit import ParquEdit
from ssb_parquedit.connection import DuckDBConnection

logging.basicConfig(
    level=logging.DEBUG,  # Set minimum log level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.parquedit_storage_connector import ParqueditStorageConnector

extractor = DefaultFormExtractor()


class LocalDuckDbConnection(DuckDBConnection):  # pyright: ignore
    def __init__(self, db_config: dict[str, str]) -> None:  # pyright: ignore
        conn_str = """ATTACH 'ducklake:duckdb:catalog.db' AS lake (DATA_PATH 'data/')"""
        self._conn = duckdb.connect()
        self._conn.sql(conn_str)
        self._conn.sql("USE lake")


class LocalParquedit(ParquEdit):  # pyright: ignore
    def __init__(self) -> None:  # pyright: ignore
        self._conn = LocalDuckDbConnection({})


parquedit_conn = ParquEdit.local("./data")
conn = parquedit_conn._get_connection().raw
res = conn.execute(
    "SELECT rowid, * FROM skjemadata WHERE feltnavn == 'politiskeFoeringerSvar'"
).fetch_df()
print(res)
# res = parquedit_conn.view("skjemadata")
# print(res)
