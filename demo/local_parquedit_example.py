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


parquedit_conn = LocalParquedit()


def get_duckdb_connection():
    raw = parquedit_conn._get_connection().raw
    return raw


connector = ParqueditStorageConnector(parquedit_conn)
for form_number in ["RA0536"]:
    if form_number == "RA0689":
        mapping = [
            {"field_name": "hjelpefeltLand", "options": [str(i) for i in range(1000)]},
        ]
    else:
        mapping = []

    processor = DefaultFormProcessor(
        form_name=form_number,
        form_base_path=f"/home/dbo/Github/ssb-altinn-form-tools/tests/testdata/{form_number}",
        extractor=extractor,
        connector=connector,
        alias_mapping={"omsVirksomhetPerioden": "omsetning"},
        checkbox_mapping=mapping,
    )
    processor.process_new_forms()

conn = parquedit_conn._get_connection().raw
rows = conn.execute("SELECT * FROM enheter LIMIT 10;").fetchall()
for row in rows:
    print(row)
