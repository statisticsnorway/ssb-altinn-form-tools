import logging

logging.basicConfig(
    level=logging.DEBUG,  # Set minimum log level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

from sqlalchemy import create_engine
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.sqlalchemy_storage_connector import (
    SqlAlchemyStorageConnector,
)

extractor = DefaultFormExtractor()

engine = engine = create_engine("sqlite:///./db.db", echo=False)
connector = SqlAlchemyStorageConnector(engine)
for form_number in ["RA0187", "RA0297", "RA0307", "RA0366", "RA0479", "RA0481", "RA0530", "RA0536", "RA0689", "RA0745", "RA0825"]:
    processor = DefaultFormProcessor(
        form_name=form_number,
        form_base_path=f"/home/onyxia/work/ssb-altinn-form-tools/tests/testdata/{form_number}",
        extractor=extractor,
        connector=connector,
        alias_mapping={"omsVirksomhetPerioden": "omsetning"},
    )
    processor.process_new_forms()

from sqlalchemy import text

with engine.connect() as conn:
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
    print("Tables:", tables)

with engine.connect() as conn:
    rows = conn.execute(text("SELECT * FROM enheter LIMIT 10;")).mappings().all()
    for row in rows:
        print(dict(row))