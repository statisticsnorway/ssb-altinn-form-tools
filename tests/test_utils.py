from typing import Any

from .utils import form_paths
from .utils import load_expected_data


def test_utils() -> None:
    paths = form_paths()
    assert len(paths) != 0


def test_form_cases() -> None:
    form_cases = load_expected_data()
    paths = form_paths()

    diff = set([form.form_name for form in form_cases]).symmetric_difference(
        [path.form_name for path in paths]
    )

    assert (
        len(diff) == 1
    ), f"Number of test cases and forms does not match. \
        All forms must have test cases. Got {len(paths)} forms \
        and {len(form_cases)} cases.\n Missing cases for {diff}"


def test_meta_form_processor_init() -> None:
    from unittest.mock import MagicMock

    from ssb_altinn_form_tools.meta_form_extractor import MetaFormExtractor
    from ssb_altinn_form_tools.meta_form_processor import MetaFormProcessor
    from ssb_altinn_form_tools.meta_storage_connector import MetaStorageConnector

    class DummyProcessor(MetaFormProcessor):
        def __init__(
            self, extractor: MetaFormExtractor, connector: MetaStorageConnector
        ) -> None:
            super().__init__(extractor, connector)

        def _find_forms(self) -> list[str]:
            return []

        def _process_form(self, xml_path: Any, json_data: Any) -> Any:
            return None

        def _process_forms(self, forms: list[str]) -> None:
            pass

        def process_new_forms(self) -> None:
            pass

    mock_extractor = MagicMock(spec=MetaFormExtractor)
    mock_connector = MagicMock(spec=MetaStorageConnector)
    processor = DummyProcessor(mock_extractor, mock_connector)
    assert processor is not None


def test_meta_storage_connector_not_implemented() -> None:
    import pytest

    from ssb_altinn_form_tools.meta_storage_connector import MetaStorageConnector

    class DummyConnector(MetaStorageConnector):
        def begin_transaction(self) -> None:
            pass

        def commit(self) -> None:
            pass

        def create_tables_if_not_exists(self) -> None:
            pass

        def insert_contact_info(self, contact_info: Any) -> None:
            pass

        def insert_form_data(self, form_data: Any) -> None:
            pass

        def insert_form_data_unedited(self, form_data: Any) -> None:
            pass

        def insert_form_reception(self, form_reception: Any) -> None:
            pass

        def insert_option_list(self, option_list: Any) -> None:
            pass

        def insert_option_node(self, option_node: Any) -> None:
            pass

        def insert_unit(self, unit: Any) -> None:
            pass

        def insert_unit_info(self, unit_info: Any) -> None:
            pass

        def rollback(self) -> None:
            pass

    connector = DummyConnector()

    with pytest.raises(
        NotImplementedError, match="validate_options_exists is not implemented"
    ):
        connector.validate_options_exists("RA0187", "2026")

    with pytest.raises(
        NotImplementedError, match="validate_form_is_new is not implemented"
    ):
        connector.validate_form_is_new("ref123")
