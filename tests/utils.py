import glob
from pathlib import Path

from pydantic import BaseModel
from pydantic import computed_field


class FormInfo(BaseModel):
    base_path: Path

    @computed_field
    @property
    def xml_paths(self) -> list[Path]:
        return list(self.base_path.rglob("**/*.xml"))

    @computed_field
    @property
    def form_name(self) -> str:
        """Eg.: RA0485."""
        return self.base_path.name

    @computed_field
    @property
    def form_name_a3_format(self) -> str:
        """Eg.: A3_RA0485_M."""
        return f"A3_{self.base_path.name}_M"

    @staticmethod
    def from_paths(paths: list[Path]) -> list["FormInfo"]:
        return [FormInfo(base_path=path) for path in paths]


def form_paths() -> list[FormInfo]:
    form_paths = glob.glob("tests/testdata/*")
    paths = [Path(path) for path in form_paths]
    infos = FormInfo.from_paths(paths)
    return infos


if __name__ == "__main__":
    form_paths()
