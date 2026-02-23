from abc import ABC
from abc import abstractmethod
from pathlib import Path

from .models import ExtractedForm, FormJsonData
from .meta_form_extractor import MetaFormExtractor
from .meta_storage_connector import MetaStorageConnector


class MetaFormProcessor(ABC):
    """Abstract base class defining the interface for form processing pipelines.

    Concrete implementations are responsible for discovering form files,
    parsing/validating associated metadata, delegating structured extraction to
    a ``MetaFormExtractor``, and persisting results through a
    ``MetaStorageConnector`` (typically with transactional semantics).

    Typical workflow:
      1. Discover form files (e.g., XML) via ``_find_forms``.
      2. For each form, load supplemental metadata (e.g., JSON).
      3. Extract structured models via a ``MetaFormExtractor``.
      4. Persist results using a ``MetaStorageConnector`` within a transaction.

    Subclasses must implement all abstract methods to define discovery, processing,
    and orchestration logic appropriate to their data sources and storage backends.
    """

    @abstractmethod
    def __init__(
        self, extractor: MetaFormExtractor, connector: MetaStorageConnector
    ) -> None:
        """Initializes the processor with extractor and storage connector.

        Args:
            extractor (MetaFormExtractor): Component responsible for turning parsed
                form dictionaries into domain models (e.g., contact info, unit info,
                reception, form data).
            connector (MetaStorageConnector): Storage backend used to validate
                uniqueness and persist extracted models.

        Notes:
            Implementations may store additional configuration (e.g., base paths,
            file naming conventions) and set up logging or other instrumentation.
        """
        super().__init__()

    @abstractmethod
    def _find_forms(self): 
        """Discovers input form files to process.

        Returns:
            Any: A collection of discovered form identifiers or file paths.
                 Implementations typically return ``list[str]`` (paths) but are
                 free to return another iterable or richer objects if needed.

        Notes:
            Subclasses should define the search strategy (e.g., recursive glob,
            database queries, cloud storage listing) and the expected return type.
        """
        ...

    @abstractmethod
    def _process_form(
        self,
        xml_path: Path,
        json_data: FormJsonData,
    ) -> None: 
        """Processes a single form given its XML path and parsed JSON metadata.

        Implementations typically:
          - Parse the XML (or read pre-parsed content).
          - Use a ``MetaFormExtractor`` to extract domain models.
          - Persist models through the ``MetaStorageConnector`` within a transaction.
          - Handle idempotency (e.g., skip if already inserted).

        Args:
            xml_path (Path): Filesystem path to the XML form.
            json_data (FormJsonData): Supplemental metadata for the form.

        Raises:
            Exception: Implementations may raise IO, parsing, validation, or
                storage-related exceptions. Subclasses should document specifics.
        """
        ...

    @abstractmethod
    def _process_forms(self, forms: list[str]) -> None: 
        """Processes a batch of discovered forms.

        Args:
            forms (list[str]): A list of form identifiers or file paths (commonly
                XML paths) returned by ``_find_forms``.

        Notes:
            This method is responsible for coordinating per-form metadata loading
            (e.g., locating and validating a corresponding JSON file) and then
            delegating to ``_process_form``. Implementations should decide on
            batching, concurrency, and error handling strategies.
        """
        ...

    @abstractmethod
    def process_new_forms(self) -> None: 
        """Entry point for end-to-end processing of newly discovered forms.

        Typical responsibilities:
          - Log the start of processing and configuration context.
          - Invoke ``_find_forms`` to discover inputs.
          - Ensure storage is ready (e.g., create tables if not present).
          - Call ``_process_forms`` to handle each discovered form.

        Notes:
            Implementations should handle empty results gracefully and may emit
            informative logs (debug/info/warning) to aid observability.
        """
        ...
