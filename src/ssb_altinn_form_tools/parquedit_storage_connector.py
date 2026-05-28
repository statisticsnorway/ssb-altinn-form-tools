import logging

try:
    from _duckdb import CatalogException
    from duckdb import DuckDBPyConnection
    from ssb_parquedit import ParquEdit
except ImportError as e:
    raise ImportError(
        "This connector cannot be used if duckdb or parquedit is not installed"
    ) from e

from .meta_storage_connector import MetaStorageConnector
from .models import ContactInfo
from .models import FormData
from .models import FormReception
from .models import OptionMetadataModel
from .models import OptionNodes
from .models import Unit
from .models import UnitInfo

logger = logging.getLogger(__name__)


class ParqueditStorageConnector(MetaStorageConnector):
    """(WIP) Storage connector intended for a Parquet/Delta-style backend.

    This class is currently **work-in-progress** and not usable. The design
    mirrors the `MetaStorageConnector` interface and sketches out table creation
    and insert operations targeting a file/table format that uses JSON-like
    schemas (e.g., Parquet with a schema registry). For now, certain operations
    still reference a SQLAlchemy `Engine` and issue simple selects, acting as
    placeholders until a full Parquet-backed implementation is completed.
    """

    def __init__(self, engine: ParquEdit) -> None:
        """Initializes the connector with a SQLAlchemy engine (placeholder).

        Args:
            engine (Engine): A SQLAlchemy engine used temporarily for validation
                checks and to mirror the transactional lifecycle while the class
                is developed.

        Raises:
            NotImplementedError: Always raised to indicate the connector is not
                ready for use.

        """
        self._engine = engine._get_connection().raw
        self._session = None

    def begin_transaction(self) -> None:
        """Starts a new transactional session (placeholder).

        Notes:
            Provided to keep parity with the `MetaStorageConnector` interface.
            In a future Parquet-backed implementation, this may manage file
            writers, staging areas, or atomic rename workflows rather than a
            database transaction.

        Raises:
            Exception: Propagates any SQLAlchemy errors during session creation
                or transaction start.
        """
        self._session = self._engine.begin()

    def _get_session(self) -> DuckDBPyConnection:
        """Returns the active session or raises if not started.

        Returns:
            Session: The active SQLAlchemy session.

        Raises:
            RuntimeError: If a transaction/session has not been started.
        """
        if self._session is None:
            raise RuntimeError("Session is not started")
        return self._session

    def rollback(self) -> None:
        """Rolls back the current transaction (placeholder).

        Args:
            ref_number (str): Reference number for diagnostic logging/context.

        Raises:
            RuntimeError: If no active session/transaction exists.
        """
        self._get_session().rollback()

    def commit(self) -> None:
        """Commits the current transaction (placeholder).

        Raises:
            RuntimeError: If no active session/transaction exists.
            Exception: Propagates SQLAlchemy commit errors.
        """
        self._get_session().commit()

    def create_tables_if_not_exists(self) -> None:
        """Creates logical tables/schemas if they do not already exist.

        Notes:
            For a Parquet/Delta backend, this would create directories and write
            schema/metadata files (or register schemas with a catalog). This WIP
            method currently only defines in-memory schema descriptors.
        """
        self._create_contact_info_table()
        self._create_control_result_table()
        self._create_controls_table()
        self._create_form_data_table(table_name="skjemadata")
        self._create_form_data_table(table_name="skjemadata_unedited")
        self._create_form_reciept_table()
        self._create_unit_info_table()
        self._create_unit_table()
        self._create_optionnodes_table()
        self._create_optionslist_table()

    def _get_ingested_forms(self) -> list[str]:
        sess = self._engine
        try:
            data = sess.execute("SELECT refnr FROM skjemadata").fetchall()
            return list(set([item[0] for item in data]))
        except CatalogException:
            return []

    def validate_form_is_new(self, form_reference: str) -> bool:
        """Checks if a form reference is not already present.

        Args:
            form_reference (str): The reference number identifying the form.

        Returns:
            bool: ``True`` if no existing record for the reference is found,
            otherwise ``False``.

        Notes:
            This placeholder implementation uses a SQLAlchemy `SELECT` against
            ``skjemamottak``. In a Parquet/Delta backend, this would scan an
            index, metadata log, or keyed manifest to ensure idempotency.
        """
        try:
            self.__getattribute__("forms")
        except AttributeError:
            self.forms = self._get_ingested_forms()

        return form_reference not in self.forms

    def validate_options_exists(self, skjema: str, iso_period: str | None) -> bool:
        """Method for validating if options have already been ingested for a period."""
        sess = self._engine
        try:
            if iso_period is not None:
                stmt = "SELECT * FROM optionsnodes WHERE skjema = ? AND iso_period = ?"
                params = (skjema, iso_period)
            else:
                stmt = "SELECT * FROM optionsnodes WHERE skjema = ?"
                params = (skjema,)

            data = sess.execute(stmt, params).fetchone()
            return (data is not None) and (len(data) != 0)
        except CatalogException:
            logger.warning("Was not able verify that if options exists or not")
            return False

    def _create_contact_info_table(self):
        """Defines the schema for the `kontaktinfo` table (contact info).

        Notes:
            Intended to represent a schema descriptor for Parquet/Delta creation.
            Currently unused beyond in-code documentation.
        """
        table_name = "kontaktinfo"
        create_stmt = f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
                    iso_period   VARCHAR NOT NULL,
                    ident  VARCHAR NOT NULL,
                    skjema  VARCHAR NOT NULL,
                    refnr  VARCHAR NOT NULL,
                    kontaktperson  VARCHAR,
                    epost  VARCHAR,
                    telefon  VARCHAR,
                    bekreftet_kontaktinfo  VARCHAR,
                    kommentar_kontaktinfo  VARCHAR,
                    kommentar_krevende  VARCHAR
        );
        ALTER TABLE {table_name} SET PARTITIONED BY (iso_period);
        """
        self._get_session().execute(create_stmt)

    def _create_form_data_table(self, table_name: str):
        """Defines the schema for the `skjemadata` table (field-level data).

        Notes:
            The current code assigns `table_name = "kontaktinfo"` which appears
            to be a typo. In a future implementation, ensure the table name
            matches ``skjemadata``.
        """
        create_stmt = f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
                iso_period   VARCHAR NOT NULL,
                skjema  VARCHAR NOT NULL,
                ident  VARCHAR NOT NULL,
                refnr  VARCHAR NOT NULL,
                feltsti  VARCHAR,
                feltnavn  VARCHAR,
                verdi  VARCHAR,
                alias  VARCHAR,
                dybde  INTEGER,
                indeks  INTEGER
        );
        ALTER TABLE {table_name} SET PARTITIONED BY (iso_period);
        """
        self._get_session().execute(create_stmt)

    def _create_form_reciept_table(self):
        """Defines the schema for the `skjemamottak` table (form reception).

        Notes:
            The date is represented as a string with a `date-time` format hint.
            A Parquet/Delta implementation would likely map this to a TIMESTAMP
            logical type.
        """
        table_name = "skjemamottak"
        create_stmt = f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
                    iso_period   VARCHAR NOT NULL,
                    ident  VARCHAR NOT NULL,
                    skjema  VARCHAR NOT NULL,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    refnr  VARCHAR,
                    editert VARCHAR,
                    aktiv BOOLEAN,
                    kommentar VARCHAR,
                    dato_mottatt TIMESTAMP
        );
        ALTER TABLE {table_name} SET PARTITIONED BY (iso_period);
        """
        self._get_session().execute(create_stmt)

    def _create_unit_table(self):
        """Defines the schema for the `enheter` table (units)."""
        table_name = "enheter"
        create_stmt = f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
                    iso_period   VARCHAR NOT NULL,
                    skjema  VARCHAR NOT NULL,
                    ident  VARCHAR NOT NULL
        );
        ALTER TABLE {table_name} SET PARTITIONED BY (iso_period);
        """
        self._get_session().execute(create_stmt)

    def _create_unit_info_table(self):
        """Defines the schema for the `enhetsinfo` table (unit attributes)."""
        table_name = "enhetsinfo"
        create_stmt = f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
                    iso_period   VARCHAR NOT NULL,
                    ident  VARCHAR NOT NULL,
                    variabel  VARCHAR,
                    verdi  VARCHAR
        );
        ALTER TABLE {table_name} SET PARTITIONED BY (iso_period);
        """
        self._get_session().execute(create_stmt)

    def _create_controls_table(self):
        """Defines the schema for the `kontroller` table (control definitions)."""
        table_name = "kontroller"
        create_stmt = f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
                    iso_period   VARCHAR NOT NULL,
                    kontrollid  VARCHAR NOT NULL,
                    kontrolltype  VARCHAR,
                    beskrivelse  VARCHAR,
                    sorting_var VARCHAR,
                    sorting_order VARCHAR
        );
        ALTER TABLE {table_name} SET PARTITIONED BY (iso_period);
        """
        self._get_session().execute(create_stmt)

    def _create_control_result_table(self):
        """Defines the schema for the `kontrollutslag` table (control results)."""
        table_name = "kontrollutslag"
        create_stmt = f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
                    iso_period   VARCHAR NOT NULL,
                    skjema VARCHAR NOT NULL,
                    kontrollid  VARCHAR NOT NULL,
                    ident VARCHAR NOT NULL,
                    refnr VARCHAR NOT NULL,
                    utslag BOOLEAN NOT NULL,
                    verdi VARCHAR NOT NULL
        );
        ALTER TABLE {table_name} SET PARTITIONED BY (iso_period);
        """
        self._get_session().execute(create_stmt)

    def _create_optionnodes_table(self):
        table_name = "optionnodes"
        create_stmt = f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
                    iso_period   VARCHAR NOT NULL,
                    skjema VARCHAR NOT NULL,
                    node_name VARCHAR NOT NULL,
                    options_id VARCHAR NOT NULL
        );
        ALTER TABLE {table_name} SET PARTITIONED BY (iso_period);
        """
        self._get_session().execute(create_stmt)

    def _create_optionslist_table(self):
        table_name = "optionslists"
        create_stmt = f"""
        CREATE TABLE IF NOT EXISTS {table_name}(
                    iso_period   VARCHAR NOT NULL,
                    skjema VARCHAR NOT NULL,
                    options_id VARCHAR NOT NULL,
                    label VARCHAR NOT NULL,
                    value VARCHAR NOT NULL
        );
        ALTER TABLE {table_name} SET PARTITIONED BY (iso_period);
        """
        self._get_session().execute(create_stmt)

    def insert_contact_info(self, contact_info: list[ContactInfo]) -> None:
        """Stages a contact info record for insertion (WIP).

        Args:
            contact_info (ContactInfo): Contact information to persist.

        Notes:
            In a complete implementation, this would write to a Parquet/Delta table,
            potentially via a staging area and atomic commit.
        """
        table_name = "kontaktinfo"
        model = [model.model_dump() for model in contact_info]

        sess = self._get_session()
        sess.execute(
            f"insert into {table_name} by name(select unnest(v.unnest) from unnest($tbl) v)",
            {"tbl": model},
        )

    def insert_form_data(self, form_data: list[FormData]) -> None:
        """Stages a batch of form data records for insertion (WIP).

        Args:
            form_data (list[FormData]): Field-level form data entries to persist.

        Notes:
            In a complete implementation, this would batch-append rows to a
            columnar file and update an index/manifest.
        """
        table_name = "skjemadata"
        models = []
        for node in form_data:
            node_data = node.model_dump()
            models.append(node_data)
        sess = self._get_session()
        sess.execute(
            f"insert into {table_name} by name(select unnest(v.unnest) from unnest($tbl) v)",
            {"tbl": models},
        )

    def insert_form_data_unedited(self, form_data: list[FormData]) -> None:
        """Stages a batch of form data records for insertion (WIP).

        Args:
            form_data (list[FormData]): Field-level form data entries to persist.

        Notes:
            In a complete implementation, this would batch-append rows to a
            columnar file and update an index/manifest.
        """
        table_name = "skjemadata_unedited"
        models = []
        for node in form_data:
            node_data = node.model_dump()
            models.append(node_data)
        sess = self._get_session()
        sess.execute(
            f"insert into {table_name} by name(select unnest(v.unnest) from unnest($tbl) v)",
            {"tbl": models},
        )

    def insert_form_reception(self, form_reciept: list[FormReception]) -> None:
        """Stages a form reception record for insertion (WIP).

        Args:
            form_reciept (FormReception): Reception metadata to persist.
        """
        table_name = "skjemamottak"
        model = [model.model_dump() for model in form_reciept]
        sess = self._get_session()
        sess.execute(
            f"insert into {table_name} by name(select unnest(v.unnest) from unnest($tbl) v)",
            {"tbl": model},
        )

    def insert_unit(self, unit: list[Unit]) -> None:
        """Stages a unit record for insertion (WIP).

        Args:
            unit (Unit): Unit metadata to persist.

        """
        table_name = "enheter"
        model = [model.model_dump() for model in unit]
        sess = self._get_session()
        sess.execute(
            f"insert into {table_name} by name(select unnest(v.unnest) from unnest($tbl) v)",
            {"tbl": model},
        )

    def insert_unit_info(self, units: list[UnitInfo]) -> None:
        """Stages unit attribute records for insertion (WIP).

        Args:
            units (list[UnitInfo]): Unit key-value attributes to persist.
        """
        table_name = "enhetsinfo"
        unit_info = []
        for item in units:
            model = item.model_dump()
            unit_info.append(model)
        sess = self._get_session()
        sess.execute(
            f"insert into {table_name} by name(select unnest(v.unnest) from unnest($tbl) v)",
            {"tbl": unit_info},
        )

    def insert_option_list(self, models: list[OptionMetadataModel]) -> None:
        """Method for inserting options lists into the table."""
        table_name = "optionslists"
        models_to_insert = []
        for model in models:
            for option in model.options:
                orm_model = dict(
                    iso_period=model.iso_period,
                    skjema=model.skjema,
                    options_id=model.options_id,
                    label=option.label,
                    value=option.value,
                )
                models_to_insert.append(orm_model)

        sess = self._get_session()
        sess.execute(
            f"insert into {table_name} by name(select unnest(v.unnest) from unnest($tbl) v)",
            {"tbl": models_to_insert},
        )

    def insert_option_node(self, models: list[OptionNodes]) -> None:
        """Method for inserting options node into the table."""
        table_name = "optionnodes"
        models_to_insert = []
        for model in models:
            for node in model.node_list:
                orm_model = dict(
                    options_id=model.option_id,
                    node_name=node,
                    iso_period=model.iso_period,
                    skjema=model.skjema,
                )
                models_to_insert.append(orm_model)

        sess = self._get_session()
        sess.execute(
            f"insert into {table_name} by name(select unnest(v.unnest) from unnest($tbl) v)",
            {"tbl": models_to_insert},
        )
