# pyright: reportPrivateUsage=false
import logging
from typing import Any
from typing import override

from _duckdb import DuckDBPyConnection

try:
    from _duckdb import CatalogException
    from duckdb import DuckDBPyConnection
    from ssb_parquedit import ParquEdit
except ImportError as e:
    raise ImportError(
        "This connector cannot be used if duckdb or parquedit is not installed"
    ) from e


import pandas as pd

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
            engine: A SQLAlchemy engine used temporarily for validation
                checks and to mirror the transactional lifecycle while the class
                is developed.
        """
        self._parquedit: ParquEdit = engine
        self._engine: DuckDBPyConnection = engine._get_connection().raw
        self._session: DuckDBPyConnection | None = None

    @override
    def begin_transaction(self) -> None:
        """Starts a new transactional session (placeholder).

        Notes:
            Provided to keep parity with the `MetaStorageConnector` interface.
            In a future Parquet-backed implementation, this may manage file
            writers, staging areas, or atomic rename workflows rather than a
            database transaction.
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

    @override
    def rollback(self) -> None:
        """Rolls back the current transaction (placeholder)."""
        _ = self._get_session().rollback()

    @override
    def commit(self) -> None:
        """Commits the current transaction (placeholder)."""
        _ = self._get_session().commit()

    @override
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

    @override
    def validate_form_is_new(self, form_reference: str) -> bool:
        """Checks if a form reference is not already present.

        Args:
            form_reference: The reference number identifying the form.

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
            self.forms: list[str] = self._get_ingested_forms()

        return form_reference not in self.forms

    @override
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

    def _create_contact_info_table(self) -> None:
        """Defines the schema for the `kontaktinfo` table (contact info).

        Notes:
            Intended to represent a schema descriptor for Parquet/Delta creation.
            Currently unused beyond in-code documentation.
        """
        schema = {
            "properties": {
                "iso_period": {"type": "string"},
                "skjema": {"type": "string"},
                "ident": {"type": "string"},
                "refnr": {"type": "string"},
                "kontaktperson": {"type": "string"},
                "epost": {"type": "string"},
                "telefon": {"type": "string"},
                "bekreftet_kontaktinfo": {"type": "string"},
                "kommentar_kontaktinfo": {"type": "string"},
                "kommentar_krevende": {"type": "stromg"},
            },
            "required": ["iso_period", "skjema", "refnr"],
        }
        if self._parquedit.exists("kontaktinfo") is False:
            self._parquedit.create_table(
                "kontaktinfo",
                schema,
                "kontaktinfo",
                user_defined_id=["iso_period", "skjema", "ident", "refnr"],
                part_columns=["iso_period"],
                fill=False,
            )

    def _create_form_data_table(self, table_name: str) -> None:
        """Defines the schema for the `skjemadata` table (field-level data).

        Notes:
            The current code assigns `table_name = "kontaktinfo"` which appears
            to be a typo. In a future implementation, ensure the table name
            matches ``skjemadata``.
        """
        schema = {
            "properties": {
                "iso_period": {"type": "string"},
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
            "required": ["iso_period", "skjema", "refnr", "ident", "feltnavn"],
        }
        if self._parquedit.exists(table_name) is False:
            self._parquedit.create_table(
                table_name,
                schema,
                table_name,
                user_defined_id=["iso_period", "skjema", "ident", "refnr", "feltnavn"],
                part_columns=["iso_period"],
                fill=False,
            )

    def _create_form_reciept_table(self) -> None:
        """Defines the schema for the `skjemamottak` table (form reception).

        Notes:
            The date is represented as a string with a `date-time` format hint.
            A Parquet/Delta implementation would likely map this to a TIMESTAMP
            logical type.
        """
        schema = {
            "properties": {
                "iso_period": {"type": "string"},
                "skjema": {"type": "string"},
                "ident": {"type": "string"},
                "skjema_versjon": {"type": "string"},
                "start_date": {"type": "date-time"},
                "end_date": {"type": "date-time"},
                "refnr": {"type": "string"},
                "status": {"type": "string"},
                "aktiv": {"type": "boolean"},
                "kommentar": {"type": "string"},
                "dato_mottatt": {"type": "date-time"},
            },
            "required": [
                "iso_period",
                "skjema",
                "refnr",
                "ident",
                "start_date",
                "end_date",
            ],
        }
        if self._parquedit.exists("skjemamottak") is False:
            self._parquedit.create_table(
                "skjemamottak",
                schema,
                "skjemamottak",
                user_defined_id=["iso_period", "skjema", "ident", "refnr"],
                part_columns=["iso_period"],
                fill=False,
            )

    def _create_unit_table(self) -> None:
        """Defines the schema for the `enheter` table (units)."""
        schema = {
            "properties": {
                "iso_period": {"type": "string"},
                "skjema": {"type": "string"},
                "ident": {"type": "string"},
            },
            "required": ["iso_period", "skjema", "ident"],
        }
        if self._parquedit.exists("enheter") is False:
            self._parquedit.create_table(
                "enheter",
                schema,
                "enheter",
                user_defined_id=["iso_period", "skjema", "ident"],
                part_columns=["iso_period"],
                fill=False,
            )

    def _create_unit_info_table(self) -> None:
        """Defines the schema for the `enhetsinfo` table (unit attributes)."""
        schema = {
            "properties": {
                "iso_period": {"type": "string"},
                "ident": {"type": "string"},
                "variable": {"type": "string"},
                "verdi": {"type": "string"},
            },
            "required": ["iso_period", "ident"],
        }
        if self._parquedit.exists("enhetsinfo") is False:
            self._parquedit.create_table(
                "enhetsinfo",
                schema,
                "enhetsinfo",
                user_defined_id=["iso_period", "ident", "variable"],
                part_columns=["iso_period"],
                fill=False,
            )

    def _create_controls_table(self) -> None:
        """Defines the schema for the `kontroller` table (control definitions)."""
        schema = {
            "properties": {
                "iso_period": {"type": "string"},
                "kontrollid": {"type": "string"},
                "kontrolltype": {"type": "string"},
                "beskrivelse": {"type": "string"},
                "sorting_var": {"type": "boolean"},
                "sorting_order": {"type": "string"},
            },
            "required": ["iso_period", "kontrollid"],
        }
        if self._parquedit.exists("kontroller") is False:
            self._parquedit.create_table(
                "kontroller",
                schema,
                "kontroller",
                user_defined_id=["iso_period", "kontrollid"],
                part_columns=["iso_period"],
                fill=False,
            )

    def _create_control_result_table(self) -> None:
        """Defines the schema for the `kontrollutslag` table (control results)."""
        schema = {
            "properties": {
                "iso_period": {"type": "string"},
                "skjema": {"type": "string"},
                "kontrollid": {"type": "string"},
                "ident": {"type": "string"},
                "refnr": {"type": "string"},
                "utslag": {"type": "boolean"},
                "verdi": {"type": "string"},
            },
            "required": ["iso_period", "skjema", "kontrollid", "ident", "refnr"],
        }
        if self._parquedit.exists("kontrollutslag") is False:
            self._parquedit.create_table(
                "kontrollutslag",
                schema,
                "kontrollutslag",
                user_defined_id=[
                    "iso_period",
                    "skjema",
                    "kontrollid",
                    "ident",
                    "refnr",
                ],
                part_columns=["iso_period"],
                fill=False,
            )

    def _create_optionnodes_table(self) -> None:
        """Defines the schema for the `optionsnodes` table (multi select options)."""
        schema = {
            "properties": {
                "iso_period": {"type": "string"},
                "skjema": {"type": "string"},
                "node_name": {"type": "string"},
                "options_id": {"type": "string"},
            },
            "required": ["iso_period", "skjema", "options_id", "node_name"],
        }
        if self._parquedit.exists("optionnodes") is False:
            self._parquedit.create_table(
                "optionnodes",
                schema,
                "optionnodes",
                user_defined_id=["iso_period", "skjema", "node_name", "options_id"],
                part_columns=["iso_period"],
                fill=False,
            )

    def _create_optionslist_table(self) -> None:
        """Defines the schema for the `optionslists` table (multi select options)."""
        schema = {
            "properties": {
                "iso_period": {"type": "string"},
                "skjema": {"type": "string"},
                "options_id": {"type": "string"},
                "label": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["iso_period", "skjema", "options_id", "label", "value"],
        }
        if self._parquedit.exists("optionslists") is False:
            self._parquedit.create_table(
                "optionslists",
                schema,
                "optionslists",
                user_defined_id=["iso_period", "skjema", "options_id"],
                part_columns=["iso_period"],
                fill=False,
            )

    def _insert(self, data: list[dict[str, Any]], table_name: str) -> None:
        """Internal method for inserting from a list of dicts."""
        if len(data):
            df = pd.DataFrame(data)
            self._parquedit.insert_data(table_name, df)

    @override
    def insert_contact_info(self, contact_info: list[ContactInfo]) -> None:
        """Stages a contact info record for insertion (WIP).

        Args:
            contact_info: Contact information to persist.

        Notes:
            In a complete implementation, this would write to a Parquet/Delta table,
            potentially via a staging area and atomic commit.
        """
        table_name = "kontaktinfo"
        model = [model.model_dump() for model in contact_info]

        self._insert(model, table_name)

    @override
    def insert_form_data(self, form_data: list[FormData]) -> None:
        """Stages a batch of form data records for insertion (WIP).

        Args:
            form_data: Field-level form data entries to persist.

        Notes:
            In a complete implementation, this would batch-append rows to a
            columnar file and update an index/manifest.
        """
        table_name = "skjemadata"
        models: list[dict[str, Any]] = []
        for node in form_data:
            node_data = node.model_dump()
            models.append(node_data)

        self._insert(models, table_name)

    @override
    def insert_form_data_unedited(self, form_data: list[FormData]) -> None:
        """Stages a batch of form data records for insertion (WIP).

        Args:
            form_data: Field-level form data entries to persist.

        Notes:
            In a complete implementation, this would batch-append rows to a
            columnar file and update an index/manifest.
        """
        table_name = "skjemadata_unedited"
        models: list[dict[str, Any]] = []
        for node in form_data:
            node_data = node.model_dump()
            models.append(node_data)

        self._insert(models, table_name)

    @override
    def insert_form_reception(self, form_reciept: list[FormReception]) -> None:
        """Stages a form reception record for insertion (WIP).

        Args:
            form_reciept: Reception metadata to persist.
        """
        table_name = "skjemamottak"
        model = [model.model_dump() for model in form_reciept]
        self._insert(model, table_name)

    @override
    def insert_unit(self, unit: list[Unit]) -> None:
        """Stages a unit record for insertion (WIP).

        Args:
            unit: Unit metadata to persist.

        """
        table_name = "enheter"
        model = [model.model_dump() for model in unit]
        self._insert(model, table_name)

    @override
    def insert_unit_info(self, units: list[UnitInfo]) -> None:
        """Stages unit attribute records for insertion (WIP).

        Args:
            units: Unit key-value attributes to persist.
        """
        table_name = "enhetsinfo"
        unit_info: list[dict[str, Any]] = []
        for item in units:
            model = item.model_dump()
            unit_info.append(model)
        self._insert(unit_info, table_name)

    @override
    def insert_option_list(self, models: list[OptionMetadataModel]) -> None:
        """Method for inserting options lists into the table."""
        table_name = "optionslists"
        models_to_insert: list[dict[str, Any]] = []
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

        self._insert(models_to_insert, table_name)

    @override
    def insert_option_node(self, models: list[OptionNodes]) -> None:
        """Method for inserting options node into the table."""
        table_name = "optionnodes"
        models_to_insert: list[dict[str, Any]] = []
        for model in models:
            for node in model.node_list:
                orm_model = dict(
                    options_id=model.option_id,
                    node_name=node,
                    iso_period=model.iso_period,
                    skjema=model.skjema,
                )
                models_to_insert.append(orm_model)

        self._insert(models_to_insert, table_name)
