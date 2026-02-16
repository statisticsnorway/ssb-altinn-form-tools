from abc import ABC
from abc import abstractmethod

from .models import (
    ContactInfo,
    FormJsonData,
    Unit,
    UnitInfo,
    FormData,
    FormReception,
    ExtractedForm,
)

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
        self, form_dict_data: InputFormType, json_data: FormJsonData
    ) -> FormReception: ...

    def extract_unit(self, year: int, form: str, ident: str) -> Unit:
        return Unit(aar=year, ident=ident, skjema=form)

    @abstractmethod
    def extract_unit_info(
        self, form_dict_data: InputFormType, year: int, ident: str
    ) -> list[UnitInfo]: ...

    def extract_form(
        self, form_dict_data: InputFormType, json_data: FormJsonData
    ) -> ExtractedForm:
        form_info = self.extract_form_reception(form_dict_data, json_data)
        test_case = self.extract_contact_info(
            form_dict_data,
            year=form_info.aar,
            form=form_info.skjema,
            ident=form_info.ident,
            refnr=form_info.refnr,
        )

        return ExtractedForm(
            reception=form_info,
            contact_info=self.extract_contact_info(
                form_dict_data,
                year=form_info.aar,
                form=form_info.skjema,
                ident=form_info.ident,
                refnr=form_info.refnr,
            ),
            unit=self.extract_unit(
                year=form_info.aar,
                form=form_info.skjema,
                ident=form_info.ident,
            ),
            unit_info=self.extract_unit_info(
                form_dict_data,
                year=form_info.aar,
                ident=form_info.ident,
            ),
            form_data=self.extract_form_data(
                form_dict_data,
                year=form_info.aar,
                form=form_info.skjema,
                ident=form_info.ident,
                refnr=form_info.refnr,
            ),
        )
