from abc import ABC
from abc import abstractmethod

from .models import ContactInfo, FormData, FormReception, Unit, UnitInfo

class MetaStorageConnector(ABC):
    """Abstract base class defining the interface for persistent storage operations.

    Concrete implementations of this class are responsible for managing database
    connections, transactional boundaries, and persisting the different sections
    of an extracted form. This includes inserting contact information, unit
    metadata, form responses, and reception details into permanent storage.

    Implementations are typically used by a ``MetaFormProcessor`` during form
    ingestion to ensure atomic operations and enforce idempotency via
    ``validate_form_is_new``.
    """

    @abstractmethod
    def __init__(self, *args, **kwargs) -> None:
        """Initializes the storage connector.

        Args:
            *args: Positional arguments passed to the concrete implementation.
            **kwargs: Keyword arguments passed to the concrete implementation.

        Notes:
            Subclasses may use the constructor to establish connections,
            configure engines or clients, or load connection metadata.
        """
        super().__init__(*args, **kwargs)

    @abstractmethod
    def begin_transaction(self) -> None:
        """Begins a new transaction boundary.

        Notes:
            Implementations should ensure that subsequent insert operations are
            executed within a transactional context. Nested transactions may be
            allowed or disallowed, depending on the backend.
        """
        ...
    
    @abstractmethod
    def commit(self) -> None:
        """Commits the current transaction.

        Notes:
            Should finalize all pending inserts and make them durable. Errors
            during commit should be surfaced and handled by the caller, typically
            resulting in logging and aborting the form processing workflow.
        """
        ...

    @abstractmethod
    def rollback(self, ref_number: str) -> None:
        """Rolls back the current transaction.

        Args:
            ref_number (str): Reference number of the form being rolled back.
                Used for logging and diagnostics.

        Notes:
            Called when an error occurs during form insertion. Implementations
            should ensure that no partial writes remain after rollback.
        """
        ...
        
    @abstractmethod
    def insert_contact_info(self, contact_info: ContactInfo) -> None:
        """Inserts contact information into storage.

        Args:
            contact_info (ContactInfo): Structured model containing submitter
                and contact metadata extracted from the form.
        """
        ...

    @abstractmethod
    def insert_form_data(self, form_data: list[FormData]) -> None:
        """Inserts form field data entries.

        Args:
            form_data (list[FormData]): A list of structured form data objects
                representing the form's individual variables and values.
        """
        ...

    @abstractmethod
    def insert_form_reception(self, form_reciept: FormReception) -> None:
        """Inserts metadata about the form reception.

        Args:
            form_reciept (FormReception): Structured model describing how and
                when the form was received.
        """
        ...

    @abstractmethod
    def insert_unit(self, unit: Unit) -> None:
        """Inserts unit-level metadata.

        Args:
            unit (Unit): Structured model representing the reporting unit.
        """
        ...

    @abstractmethod
    def insert_unit_info(self, unit: list[UnitInfo]) -> None:
        """Inserts additional unit-level attributes.

        Args:
            unit (list[UnitInfo]): A list of key-value pairs describing extra
                metadata about the reporting unit.
        """
        ...

    @abstractmethod
    def create_tables_if_not_exists(self) -> None:
        """Creates storage tables if they do not already exist.

        Notes:
            Implementations should ensure this operation is idempotent and safe
            to call multiple times.
        """
        ...

    def validate_form_is_new(self, form_reference: str) -> bool:
        """Checks whether a form has already been inserted.

        Args:
            form_reference (str): Reference number identifying the form instance.

        Returns:
            bool: ``True`` if the form has not been inserted before, otherwise ``False``.

        Raises:
            NotImplementedError: If the subclass does not implement this method.

        Notes:
            Used primarily by form processors to ensure idempotent ingestion.
        """
        raise NotImplementedError(f"validate_new_form is not implemented for {self}")