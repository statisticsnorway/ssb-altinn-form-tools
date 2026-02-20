from abc import ABC
from abc import abstractmethod

from .models import ContactInfo, FormData, FormReception, Unit, UnitInfo

class MetaStorageConnector(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @abstractmethod
    def begin_transaction(self) -> None:
        ...
    
    @abstractmethod
    def commit(self) -> None:
        ...

    @abstractmethod
    def rollback(self, ref_number: str) -> None:
        ...
    @abstractmethod
    def insert_contact_info(self, contact_info: ContactInfo) -> None:
        ...

    @abstractmethod
    def insert_form_data(self, form_data: list[FormData]) -> None:
        ...

    @abstractmethod
    def insert_form_reception(self, form_reciept: FormReception) -> None:
        ...

    @abstractmethod
    def insert_unit(self, unit: Unit) -> None:
        ...

    @abstractmethod
    def insert_unit_info(self, unit: list[UnitInfo]) -> None:
        ...

    @abstractmethod
    def create_tables_if_not_exists(self) -> None:
        ...

    def validate_form_is_new(self, form_reference: str) -> bool:
        raise NotImplementedError(f"validate_new_form is not implemented for {self}")