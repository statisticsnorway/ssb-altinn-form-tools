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
        Base.metadata.create_all(self._engine)

    def validate_form_is_new(self, form_reference: str) -> bool:
        """Return True if the reference number does not exist"""
        stmt = select(skjemamottak).filter(skjemamottak.refnr == form_reference)
        conn = self._engine.connect()
        result = conn.execute(stmt).first()
        return result is None

    def insert_contact_info(self, contact_info: ContactInfo) -> None:
        model = kontaktinfo(
            aar=contact_info.aar,
            skjema=contact_info.skjema,
            ident=contact_info.ident,
            refnr=contact_info.refnr,
            kontaktperson=contact_info.kontaktperson,
            epost=contact_info.epost,
            telefon=contact_info.telefon,
            bekreftet_kontaktinfo=contact_info.bekreftet_kontaktinfo,
            kommentar_kontaktinfo=contact_info.kommentar_kontaktinfo,
            kommentar_krevende=contact_info.kommentar_krevende,
        )
        self._get_session().add(model)

    def insert_form_data(self, form_data: list[FormData]) -> None:
        models = []
        for node in form_data:
            node_data = skjemadata(
                aar=node.aar,
                skjema=node.skjema,
                ident=node.ident,
                refnr=node.refnr,
                feltsti=node.feltsti,
                feltnavn=node.feltnavn,
                verdi=node.verdi,
                dybde=node.dybde,
                indeks=node.indeks,
            )
            models.append(node_data)
        self._get_session().add_all(models)

    def insert_form_reception(self, form_reciept: FormReception) -> None:
        model = skjemamottak(
            aar=form_reciept.aar,
            skjema=form_reciept.skjema,
            ident=form_reciept.ident,
            refnr=form_reciept.refnr,
            kommentar=form_reciept.kommentar,
            dato_mottatt=form_reciept.dato_mottatt,
            editert=form_reciept.editert,
            aktiv=form_reciept.aktiv,
        )
        self._get_session().add(model)

    def insert_unit(self, unit: Unit) -> None:
        model = enheter(aar=unit.aar, ident=unit.ident, skjema=unit.skjema)
        self._get_session().add(model)

    def insert_unit_info(self, units: list[UnitInfo]) -> None:
        unit_info = []
        for item in units:
            model = enhetsinfo(
                aar=item.aar, ident=item.ident, variabel=item.variabel, verdi=item.verdi
            )
            unit_info.append(model)
        self._get_session().add_all(unit_info)
