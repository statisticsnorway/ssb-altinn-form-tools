from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import text

from ssb_altinn_form_tools.default_form_extractor import parse_entries
from ssb_altinn_form_tools.meta_form_extractor import InputFormType
from ssb_altinn_form_tools.models import FormData
from ssb_altinn_form_tools.models import FormReception
from ssb_altinn_form_tools.sqlalchemy_storage_connector import (
    SqlAlchemyStorageConnector,
)

nested_dict = {
    "fruits": {"apple": 3, "banana": 5},
    "vegetables": {"root": {"carrot": 7, "beetroot": 4}, "leafy": {"spinach": 2}},
}


class CustomExtractor:
    """Demo of how to create a custom extractor class."""

    def extract_form_data(
        self,
        form_dict_data: InputFormType,
        form: str,
        ident: str,
        refnr: str,
        iso_period: str,
    ) -> list[FormData]:
        """Custom extraction code."""
        entries = parse_entries(form_dict_data)
        data = []
        for entry in entries:
            form_data = FormData.from_form_data(
                entry, form=form, ident=ident, refnr=refnr, iso_period=iso_period
            )
            data.append(form_data)
        return data


class CustomProcessor:
    """Demo of how to create a custom processor class."""

    def __init__(
        self, extractor: CustomExtractor, connector: SqlAlchemyStorageConnector
    ) -> None:
        """Initializes the class."""
        self.extractor = extractor
        self.connector = connector

    def process_new_forms(self) -> None:
        """Custom method to process new forms."""
        forms = [
            {"id": "id1", "form": "api1", "period": "2025-Q1", "data": nested_dict}
        ]

        forms_to_insert = []
        form_receptions_to_insert = []
        for form in forms:
            form_data = self.extractor.extract_form_data(
                form["data"],
                form=form["form"],
                refnr=form["id"],
                ident="",
                iso_period=form["period"],
            )
            forms_to_insert.extend(form_data)

            reception = FormReception(
                skjema=form["form"],
                refnr=form["id"],
                ident="",
                iso_period=form["period"],
                editert="ikke editert",
                kommentar="",
                aktiv=True,
                start_date=datetime(year=2025, month=1, day=1),
                end_date=datetime(year=2025, month=3, day=31),
                dato_mottatt=datetime.now(),
            )
            form_receptions_to_insert.append(reception)

        self.connector.begin_transaction()
        self.connector.create_tables_if_not_exists()
        self.connector.insert_form_data(forms_to_insert)
        self.connector.insert_form_data_unedited(forms_to_insert)
        self.connector.insert_form_reception(form_receptions_to_insert)
        self.connector.commit()


engine = engine = create_engine("sqlite:///./db.db", echo=False)
connector = SqlAlchemyStorageConnector(engine)
extractor = CustomExtractor()
processor = CustomProcessor(extractor, connector)
processor.process_new_forms()

with engine.connect() as conn:
    rows = conn.execute(text("SELECT * FROM skjemadata;")).mappings().all()
    for row in rows:
        print(dict(row))
