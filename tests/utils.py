import glob
import json
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field
from pydantic import computed_field


class FormInfo(BaseModel):
    base_path: Path

    @computed_field
    @property # type: ignore[misc]
    def xml_paths(self) -> list[Path]:
        return list(self.base_path.rglob("**/*.xml"))

    @computed_field
    @property # type: ignore[misc]
    def form_name(self) -> str:
        """Eg.: RA0485."""
        return self.base_path.name

    @computed_field
    @property # type: ignore[misc]
    def form_name_a3_format(self) -> str:
        """Eg.: A3_RA0485_M."""
        return f"A3_{self.base_path.name}_M"

    @staticmethod
    def from_paths(paths: list[Path]) -> list["FormInfo"]:
        return [FormInfo(base_path=path) for path in paths]


def form_paths() -> list[FormInfo]:
    form_paths = glob.glob("tests/testdata/RA*")
    paths = [Path(path) for path in form_paths]
    infos = FormInfo.from_paths(paths)
    return infos


class TestField(BaseModel):
    field_name: str
    field_value: str = Field(coerce_numbers_to_str=True)


class FormTestParams(BaseModel):
    form_id: str
    skjemadata_rows: int
    kontaktinfo_rows: int
    skjemamottak_rows: int

    test_fields: list[TestField]


class Form(BaseModel):
    form_name: str
    forms: list[FormTestParams]
    forced_array: list[str] = Field(default_factory=lambda: [])

    @computed_field
    @property # type: ignore[misc]
    def form_info(self) -> FormInfo:
        return FormInfo(base_path=Path(f"tests/testdata/{self.form_name}"))


class ExpectedData(BaseModel):
    data: list[Form]


def load_expected_data() -> list[Form]:
    json_data = []
    files = glob.glob("tests/expected_data/*.json")
    for file in files:
        data = json.load(open(file))
        json_data.append(data)
    assert len(json_data) != 0
    model = ExpectedData.model_validate({"data": json_data})
    return model.data


if __name__ == "__main__":
    load_expected_data()
