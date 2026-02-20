from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from .meta_storage_connector import MetaStorageConnector
from .models import ContactInfo, Unit, UnitInfo, FormData, FormReception
from .schema import Base, kontaktinfo, enheter, enhetsinfo, skjemadata, skjemamottak


class SqlAlchemyStorageConnector(MetaStorageConnector):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._session = None

    def begin_transaction(self) -> None:
        self._session = Session(bind=self._engine)
        self._get_session().begin()

    def _get_session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Session is not started")
        return self._session

    def rollback(self, ref_number: str) -> None:
        self._get_session().rollback()

    def commit(self) -> None:
        self._get_session().commit()

    def create_tables_if_not_exists(self) -> None:
        self._create_contact_info_table()
        self._create_control_result_table()
        self._create_controls_table()
        self._create_form_data_table()
        self._create_form_reciept_table()
        self._create_unit_info_table()
        self._create_unit_table()

    def validate_form_is_new(self, form_reference: str) -> bool:
        """Return True if the reference number does not exist"""
        stmt = select(skjemamottak).filter(skjemamottak.refnr == form_reference)
        conn = self._engine.connect()
        result = conn.execute(stmt).first()
        return result is None

    def _create_contact_info_table(self):
        table_name = "kontaktinfo"
        schema = {
            "properties": {
                "id": {"type": "integer"},
                "aar": {"type": "integer"},
                "skjema": {"type": "string"},
                "ident": {"type": "string"},
                "refnr": {"type": "string"},
                "kontaktperson": {"type": "string"},
                "epost": {"type": "string"},
                "telefon": {"type": "string"},
                "bekreftet_kontaktinfo": {"type": "string"},
                "kommentar_kontaktinfo": {"type": "string"},
                "kommentar_krevende": {"type": "string"},
            },
            "required": ["id", "aar", "skjema", "ident", "refnr"],
        }

    def _create_form_data_table(self):
        table_name = "kontaktinfo"
        schema = {
            "properties": {
                "id": {"type": "integer"},
                "aar": {"type": "integer"},
                "skjema": {"type": "string"},
                "ident": {"type": "string"},
                "refnr": {"type": "string"},
                "feltsti": {"type": "string"},
                "feltnavn": {"type": "string"},
                "verdi": {"type": "string"},
                "alias": {"type": "string"},
                "dybde": {"type": "integer"},
                "indeks": {"type": "integer"},
            },
            "required": [
                "id",
                "aar",
                "skjema",
                "ident",
                "refnr",
                "feltsti",
                "feltnavn",
                "verdi",
            ],
        }

    def _create_form_reciept_table(self):
        table_name = "skjemamottak"
        schema = {
            "properties": {
                "id": {"type": "integer"},
                "aar": {"type": "integer"},
                "skjema": {"type": "string"},
                "ident": {"type": "string"},
                "refnr": {"type": "string"},
                "kommentar": {"type": "string"},
                "dato_mottatt": {"type": "string", "fmt": "date-time"},
                "editert": {"type": "string"},
                "aktiv": {"type": "boolean"},
            },
            "required": [
                "id",
                "aar",
                "skjema",
                "ident",
                "refnr",
                "dato_mottatt",
                "editert",
                "aktiv",
            ],
        }

    def _create_unit_table(self):
        table_name = "enheter"
        schema = {
            "properties": {
                "id": {"type": "integer"},
                "aar": {"type": "integer"},
                "skjema": {"type": "string"},
                "ident": {"type": "string"},
            },
            "required": [
                "id",
                "aar",
                "skjema",
                "ident",
            ],
        }

    def _create_unit_info_table(self):
        table_name = "enhetsinfo"
        schema = {
            "properties": {
                "id": {"type": "integer"},
                "aar": {"type": "integer"},
                "ident": {"type": "string"},
                "variabel": {"type": "string"},
                "verdi": {"type": "string"},
            },
            "required": ["id", "aar", "ident", "variabel", "verdi"],
        }

    def _create_controls_table(self):
        table_name = "kontroller"
        schema = {
            "properties": {
                "id": {"type": "integer"},
                "aar": {"type": "integer"},
                "kontrollid": {"type": "string"},
                "kontrolltype": {"type": "string"},
                "beskrivelse": {"type": "string"},
                "sorting_var": {"type": "string"},
                "sorting_order": {"type": "string"},
            },
            "required": [
                "id",
                "aar",
                "kontrollid",
                "kontrolltype",
                "beskrivelse",
                "sorting_var",
                "sorting_order",
            ],
        }

    def _create_control_result_table(self):
        table_name = "kontrollutslag"
        schema = {
            "properties": {
                "id": {"type": "integer"},
                "aar": {"type": "integer"},
                "skjema": {"type": "string"},
                "kontrollid": {"type": "string"},
                "ident": {"type": "string"},
                "refnr": {"type": "string"},
                "utslag": {"type": "boolean"},
                "verdi": {"type": "string"},
            },
            "required": [
                "id",
                "aar",
                "kontrollid",
                "skjema",
                "ident",
                "refnr",
                "utslag",
            ],
        }

    def insert_contact_info(self, contact_info: ContactInfo) -> None:
        table_name = "kontaktinfo"
        model = [contact_info.model_dump()]

    def insert_form_data(self, form_data: list[FormData]) -> None:
        table_name = "skjemadata"
        models = []
        for node in form_data:
            node_data = node.model_dump()
            models.append(node_data)

    def insert_form_reception(self, form_reciept: FormReception) -> None:
        table_name = "skjemamottak"
        model = [form_reciept.model_dump()]

    def insert_unit(self, unit: Unit) -> None:
        table_name = "enheter"
        model = [unit.model_dump()]

    def insert_unit_info(self, units: list[UnitInfo]) -> None:
        table_name = "enhetsinfo"
        unit_info = []
        for item in units:
            model = item.model_dump()
            unit_info.append(model)
