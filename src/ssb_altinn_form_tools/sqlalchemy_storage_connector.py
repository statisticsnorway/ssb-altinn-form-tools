from sqlalchemy import Engine
from sqlalchemy import select
from sqlalchemy.orm import Session

from .meta_storage_connector import MetaStorageConnector
from .models import ContactInfo
from .models import FormData
from .models import FormReception
from .models import OptionMetadataModel
from .models import OptionNodes
from .models import Unit
from .models import UnitInfo
from .schema import Base
from .schema import Enheter
from .schema import EnhetsInfo
from .schema import KontaktInfo
from .schema import OptionNodes as OrmOptionNodes
from .schema import OptionsLists
from .schema import Skjemadata
from .schema import SkjemadataUnedited
from .schema import SkjemaMottak


class SqlAlchemyStorageConnector(MetaStorageConnector):
    """SQLAlchemy-based storage connector implementing MetaStorageConnector.

    This connector manages a SQLAlchemy engine and session to perform transactional
    inserts of form sections (contact info, unit, unit info, form data, reception)
    and to enforce idempotency by checking whether a form reference already exists.

    Attributes:
        _engine (Engine): SQLAlchemy engine used for connections and DDL.
        _session (Session | None): Lazily initialized session used for transactions.
    """

    def __init__(self, engine: Engine) -> None:
        """Initializes the connector with a SQLAlchemy engine.

        Args:
            engine (Engine): A configured SQLAlchemy engine instance.

        Notes:
            The session is created on demand when a transaction is started via
            ``begin_transaction``.
        """
        self._engine = engine
        self._session = None

    def begin_transaction(self) -> None:
        """Starts a new transactional session.

        Creates a new SQLAlchemy ``Session`` bound to the configured engine and
        begins a transaction context.

        Raises:
            Exception: Propagates any SQLAlchemy errors that occur during session
                creation or transaction start.
        """
        self._session = Session(bind=self._engine)
        self._get_session().begin()

    def _get_session(self) -> Session:
        """Returns the active session or raises if not started.

        Returns:
            Session: The active SQLAlchemy session.

        Raises:
            RuntimeError: If a transaction has not been started (session is None).
        """
        if self._session is None:
            raise RuntimeError("Session is not started")
        return self._session

    def rollback(self) -> None:
        """Rolls back the current transaction.

        Args:
            ref_number (str): Reference number of the form being rolled back.
                Provided for API parity/logging, though not used directly here.

        Raises:
            RuntimeError: If no active session/transaction exists.
        """
        self._get_session().rollback()

    def commit(self) -> None:
        """Commits the current transaction.

        Raises:
            RuntimeError: If no active session/transaction exists.
            Exception: Propagates any SQLAlchemy commit errors.
        """
        self._get_session().commit()

    def create_tables_if_not_exists(self) -> None:
        """Creates all mapped tables if they do not already exist.

        Notes:
            Uses SQLAlchemy metadata reflection to create tables defined in
            ``.schema.Base``. This operation is idempotent.
        """
        Base.metadata.create_all(self._engine)

    def validate_form_is_new(self, form_reference: str) -> bool:
        """Checks if a form reference is not already present.

        Args:
            form_reference (str): The Altinn/reference number identifying the form.

        Returns:
            bool: ``True`` if no existing row for the reference is found, else ``False``.

        Notes:
            Executes a ``SELECT`` against the ``skjemamottak`` table and returns
            whether any row exists with the same reference number.
        """
        stmt = select(SkjemaMottak).filter(SkjemaMottak.refnr == form_reference)
        conn = self._engine.connect()
        result = conn.execute(stmt).first()
        return result is None

    def validate_options_exists(self, skjema: str, iso_period: str | None) -> bool:
        """Method to check if options have already been inserted for the period."""
        stmt = select(OrmOptionNodes).filter(OrmOptionNodes.skjema == skjema)
        if iso_period:
            stmt = stmt.filter(OrmOptionNodes.iso_period == iso_period)

        conn = self._engine.connect()
        result = conn.execute(stmt).first()
        return result is not None

    def insert_contact_info(self, contact_info: list[ContactInfo]) -> None:
        """Inserts contact information for a form.

        Args:
            contact_info (ContactInfo): Contact metadata extracted from the form.

        Side Effects:
            Adds a new ``kontaktinfo`` ORM instance to the current session.
        """
        forms = []
        for form in contact_info:
            model = KontaktInfo(
                iso_period=form.iso_period,
                skjema=form.skjema,
                ident=form.ident,
                refnr=form.refnr,
                kontaktperson=form.kontaktperson,
                epost=form.epost,
                telefon=form.telefon,
                bekreftet_kontaktinfo=form.bekreftet_kontaktinfo,
                kommentar_kontaktinfo=form.kommentar_kontaktinfo,
                kommentar_krevende=form.kommentar_krevende,
            )
            forms.append(model)
        self._get_session().add_all(forms)

    def insert_form_data(self, form_data: list[FormData]) -> None:
        """Inserts all field-level form data entries.

        Args:
            form_data (list[FormData]): A list of form data items to persist.

        Side Effects:
            Adds multiple ``skjemadata`` ORM instances to the current session.
        """
        models = []
        for node in form_data:
            node_data = Skjemadata(
                iso_period=node.iso_period,
                skjema=node.skjema,
                ident=node.ident,
                refnr=node.refnr,
                feltsti=node.feltsti,
                feltnavn=node.feltnavn,
                verdi=node.verdi,
                dybde=node.dybde,
                indeks=node.indeks,
                alias=node.alias,
            )
            models.append(node_data)
        self._get_session().add_all(models)

    def insert_form_data_unedited(self, form_data: list[FormData]) -> None:
        """Same as skjemadata, but should not be edited."""
        models = []
        for node in form_data:
            node_data = SkjemadataUnedited(
                iso_period=node.iso_period,
                skjema=node.skjema,
                ident=node.ident,
                refnr=node.refnr,
                feltsti=node.feltsti,
                feltnavn=node.feltnavn,
                verdi=node.verdi,
                dybde=node.dybde,
                indeks=node.indeks,
                alias=node.alias,
            )
            models.append(node_data)
        self._get_session().add_all(models)

    def insert_form_reception(self, form_reciept: list[FormReception]) -> None:
        """Inserts metadata describing the reception of a form.

        Args:
            form_reciept (FormReception): Reception model (date received, active flag,
                edit status, comments, etc.).

        Side Effects:
            Adds a new ``skjemamottak`` ORM instance to the current session.
        """
        forms = []
        for form in form_reciept:
            model = SkjemaMottak(
                iso_period=form.iso_period,
                start_date=form.start_date,
                end_date=form.end_date,
                skjema=form.skjema,
                skjema_versjon=form.skjema_versjon,
                ident=form.ident,
                refnr=form.refnr,
                kommentar=form.kommentar,
                dato_mottatt=form.dato_mottatt,
                editert=form.editert,
                aktiv=form.aktiv,
            )
            forms.append(model)
        self._get_session().add_all(forms)

    def insert_unit(self, unit: list[Unit]) -> None:
        """Inserts unit-level metadata.

        Args:
            unit (Unit): Reporting unit model to persist.

        Side Effects:
            Adds a new ``enheter`` ORM instance to the current session.
        """
        forms = []
        for form in unit:
            model = Enheter(
                iso_period=form.iso_period,
                ident=form.ident,
                skjema=form.skjema,
            )
            forms.append(model)
        self._get_session().add_all(forms)

    def insert_unit_info(self, units: list[UnitInfo]) -> None:
        """Inserts additional key-value attributes for a unit.

        Args:
            units (list[UnitInfo]): Collection of unit info entries to persist.

        Side Effects:
            Adds multiple ``enhetsinfo`` ORM instances to the current session.
        """
        unit_info = []
        for item in units:
            model = EnhetsInfo(
                iso_period=item.iso_period,
                ident=item.ident,
                variabel=item.variabel,
                verdi=item.verdi,
            )
            unit_info.append(model)
        self._get_session().add_all(unit_info)

    def insert_option_list(self, models: list[OptionMetadataModel]) -> None:
        """Method for inserting options lists into the table."""
        models_to_insert = []
        for model in models:
            for option in model.options:
                orm_model = OptionsLists(
                    iso_period=model.iso_period,
                    skjema=model.skjema,
                    options_id=model.options_id,
                    label=option.label,
                    value=option.value,
                )
                models_to_insert.append(orm_model)
        self._get_session().add_all(models_to_insert)

    def insert_option_node(self, models: list[OptionNodes]) -> None:
        """Method for inserting options node into the table."""
        models_to_insert = []
        for model in models:
            for node in model.node_list:
                orm_model = OrmOptionNodes(
                    options_id=model.option_id,
                    node_name=node,
                    iso_period=model.iso_period,
                    skjema=model.skjema,
                )
                models_to_insert.append(orm_model)
        self._get_session().add_all(models_to_insert)
