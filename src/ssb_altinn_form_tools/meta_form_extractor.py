from abc import ABC
from abc import abstractmethod

from .models import ContactInfo, Unit, UnitInfo, FormData, FormReception

InputFormType = dict[str, list | dict | str | int | None]


class MetaFormExtractor(ABC):
    @abstractmethod
    def extract_contact_info(
        self,
        form_dict_data: InputFormType,
        year: int,
        form: str,
        ident: str,
        refnr: str,
    ) -> ContactInfo: ...

    @abstractmethod
    def extract_form_data(
        self,
        form_dict_data: InputFormType,
        year: int,
        form: str,
        ident: str,
        refnr: str,
    ) -> list[FormData]: ...

    @abstractmethod
    def extract_form_reception(
        self, form_dict_data: InputFormType, json_data: dict
    ) -> FormReception: ...

    def extract_unit(self, year: int, form: str, ident: str) -> Unit:
        return Unit(aar=year, ident=ident, skjema=form)

    @abstractmethod
    def extract_unit_info(
        self, form_dict_data: InputFormType, year: int, ident: str
    ) -> list[UnitInfo]: ...
