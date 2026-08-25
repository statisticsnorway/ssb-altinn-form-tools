import logging

from ssb_parquedit import ParquEdit

logging.basicConfig(
    level=logging.DEBUG,  # Set minimum log level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.parquedit_storage_connector import ParqueditStorageConnector

extractor = DefaultFormExtractor()

parquedit_conn = ParquEdit.local("data")


def get_duckdb_connection():
    raw = parquedit_conn._get_connection().raw
    return raw


connector = ParqueditStorageConnector(parquedit_conn)
for form_number in ["RA0485"]:

    processor = DefaultFormProcessor(
        form_name=form_number,
        form_base_path=f"/home/dbo/Github/ssb-altinn-form-tools/tests/testdata/{form_number}",
        extractor=extractor,
        connector=connector,
        alias_mapping={"omsVirksomhetPerioden": "omsetning"},
        checkbox_mapping=[],
    )
    processor.process_new_forms()

conn = parquedit_conn._get_connection().raw
rows = conn.execute("SELECT * FROM enheter LIMIT 10;").fetchall()
for row in rows:
    print(row)
