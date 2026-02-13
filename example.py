import logging

logging.basicConfig(
    level=logging.DEBUG,  # Set minimum log level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True
)

from sqlalchemy import create_engine
from src.ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from src.ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from src.ssb_altinn_form_tools.sqlalchemy_storage_connector import SqlAlchemyStorageConnector

extractor = DefaultFormExtractor()

engine = engine = create_engine("sqlite:///./db.db", echo=False)
connector = SqlAlchemyStorageConnector(engine)

processor = DefaultFormProcessor(form_name="RA0187", form_base_path="/home/onyxia/work/ssb-altinn-form-tools/tests/testdata/RA0187", extractor=extractor, connector=connector)
processor.process_new_forms()