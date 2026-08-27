from typing import Any

import pytest

from ssb_altinn_form_tools.utils.form_metadata import FormMetadata

from .utils import form_paths


@pytest.fixture(params=form_paths())
def form_info_fixture(request: pytest.FixtureRequest) -> Any:
    return request.param


# @pytest.fixture(scope="session")
def metadata_fixture() -> dict[str, FormMetadata]:
    metadata: dict[str, FormMetadata] = {}
    for form in form_paths():
        metadata_handler = FormMetadata(form_name=form.form_name)
        metadata_handler.get_array_fields()
        metadata_handler.extract_options_list(form.form_name, "2026")
        metadata_handler.extract_options_nodes(form.form_name, "2026")
        metadata[form.form_name] = metadata_handler
    return metadata
