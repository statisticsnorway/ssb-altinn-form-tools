from .utils import form_paths
from .utils import load_expected_data


def test_utils():
    paths = form_paths()
    assert len(paths) != 0


def test_form_cases():
    form_cases = load_expected_data()
    paths = form_paths()
    assert len(paths) == len(form_cases), (
        f"Number of test cases and forms does not match. All forms must have test cases. Got {len(paths)} forms and {len(form_cases)} cases"
    )
