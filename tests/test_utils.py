from .utils import form_paths


def test_utils():
    paths = form_paths()
    assert len(paths) != 0
