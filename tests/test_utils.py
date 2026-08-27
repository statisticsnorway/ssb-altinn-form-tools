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

    assert len(diff) == 1, f"Number of test cases and forms does not match. \
        All forms must have test cases. Got {len(paths)} forms \
        and {len(form_cases)} cases.\n Missing cases for {diff}"
