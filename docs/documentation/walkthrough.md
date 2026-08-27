# Walkthrough

This walkthrough is designed to help you understand how the package works and how to adapt it to your own needs.

- [Design](#design)
- [Form extractor](#extractor)
    - [Default extractor](#default-extractor)
    - [Overwrite extractor](#overwrite-extractor)
    - [Custom extractor](#custom-extractor)
- [Storage connector](#storage-connector)
    - [Custom connector](#custom-connector)
- [Form processor](#form-processor)
    - [Form paths](#path-to-forms)
    - [Checkboxes](#checkbox-mapping)
- [Full example](#full-example)

<a id="design"></a>
## Design
Processing of a form consists of extracting and transforming data from an xml to a uniform format, and ingesting that data into a database or some other form of storage. Some form of bridge between these two processes are also needed, which results in a complete extractor.

The package tries to mimic that process. This is done by providing three "meta classes". These classes describe expected behaviour and allows us to write connectors to different storage solutions, and handle forms with diverging needs.

These meta classes are ``MetaFormProcessor``, ``MetaFormExtractor`` and ``MetaStorageConnector``. ``MetaStorageConnector`` is responsible for defining an interface to connect to a storage solution. ``MetaFormExtractor`` defines required methods and types for extracting form data. ``MetaFormProcessor`` defines an interfacing for binding these two together.

We have provided default implementation of the ``MetaFormProcessor``and the ``MetaFormExtractor`` classes. We have also provided two ``MetaStorageConnector``, one for sqlalchemy, which works for all databases that sqlalchemy can connect to, e.g. Postgresql and SQLite. One connector for Parquedit is also provided. NOTE: The connector for parquedit is a WIP and is not currently working.

## Extractor

<a id="default-extractor"></a>

### Default extractor
```python
from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
extractor = DefaultFormExtractor()
```
<a id="overwrite-extractor"></a>

### ADVANCED: Overwrite part of the extractor
```python
from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.meta_form_extractor import InputFormType
from ssb_altinn_form_tools.models import ContactInfo

class CustomExtractor(DefaultFormExtractor):
    def extract_contact_info(
        self,
        form_dict_data: InputFormType,
        year: int,
        form: str,
        ident: str,
        refnr: str,
    ) -> ContactInfo:
    # Your own implementation
extractor = CustomExtractor()
```
<a id="custom-extractor"></a>

### ADVANCED: Custom extractor
```python
from ssb_altinn_form_tools.meta_form_extractor import (
        MetaFormExtractor,
        InputFormType
    )
from ssb_altinn_form_tools.models import *

class CustomExtractor(MetaFormExtractor):
    def extract_contact_info(
        self,
        form_dict_data: InputFormType,
        year: int,
        form: str,
        ident: str,
        refnr: str,
    ) -> ContactInfo:
    # Your own implementation

    def extract_form_data(
        self,
        form_dict_data: InputFormType,
        year: int,
        form: str,
        ident: str,
        refnr: str,
    ) -> list[FormData]:
        # Your own implementation

    def extract_form_reception(
        self, form_dict_data: InputFormType, json_data: FormJsonData
    ) -> FormReception:
        # Your own implementation

    def extract_unit(self, year: int, form: str, ident: str) -> Unit:
        # Your own implementation

    def extract_unit_info(
        self, form_dict_data: InputFormType, year: int, ident: str
    ) -> list[UnitInfo]:
        # Your own implementation

extractor = CustomExtractor()
```
<a id="connector"></a>

## Storage connector
As of now the Sqlalchemy connector is the one that should be used.
```python
from sqlalchemy import create_engine
from ssb_altinn_form_tools.sqlalchemy_storage_connector import (
    SqlAlchemyStorageConnector,
)

engine = engine = create_engine("sqlite:///./db.db", echo=False)
connector = SqlAlchemyStorageConnector(engine)

```
<a id="custom-connector"></a>

### ADVANCED: Custom connector
Note: If you want to do this, contact the package maintainers as it is likely the custom connector should be added to the package.

```python
from ssb_altinn_form_tools.meta_storage_connector import MetaStorageConnector,

from ssb_altinn_form_tools.models import *

class CustomConnector(MetaStorageConnector):
    def __init__(self, *args, **kwargs) -> None:
        # Your implementation

    def begin_transaction(self) -> None:
        # Your implementation

    def commit(self) -> None:
        # Your implementation

    def rollback(self, ref_number: str) -> None:
        # Your implementation

    def insert_contact_info(self, contact_info: ContactInfo) -> None:
        # Your implementation

    def insert_form_data(self, form_data: list[FormData]) -> None:
        # Your implementation

    def insert_form_reception(self, form_reciept: FormReception) -> None:
        # Your implementation

    def insert_unit(self, unit: Unit) -> None:
        # Your implementation

    def insert_unit_info(self, unit: list[UnitInfo]) -> None:
        # Your implementation

    def insert_checkboxes(self, unit: list[Checkboxmodel]) -> None:
        # Your implementation

    def create_tables_if_not_exists(self) -> None:
        # Your implementation

    def validate_form_is_new(self, form_reference: str) -> bool:
        # Your implementation

connector = CustomConnector()
```
<a id="processor"></a>

## Form processor
NOTE: The processor automatically tries to derive the schema of the form by using metadata provided by an Altinn-api. Some forms does not contain metadata, and this should be added.

The chosen connector and extractor is expected as init arguments.

```python
from sqlalchemy import create_engine
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.sqlalchemy_storage_connector import (
    SqlAlchemyStorageConnector,
)

extractor = DefaultFormExtractor()

engine = engine = create_engine("sqlite:///./db.db", echo=False)
connector = SqlAlchemyStorageConnector(engine)
processor = DefaultFormProcessor(
        form_name="RAXXXX",
        form_base_path=f"/path/to/forms/RAXXXX",
        extractor=extractor,
        connector=connector,
        #alias_mapping={"fieldname": "alias"},
        #checkbox_mapping=[],
        #ra_version=1,
        #alternative_glob_path=None,
    )
processor.process_new_forms()

```
<a id="processor-path"></a>

### Path to forms
The default expected path to forms is the same path as forms are processed by the SUV-team /YEAR/MONTH/DAY/unique_id/form.xml

If your forms have a different structure you can provide the ``alternative_glob_path``argument that should be globbable and result in a list of strings with paths to all xml-forms

<a id="processor-checkbox-mapping"></a>

### Checkbox mapping
Info about checkboxes are not provided in the form and have to be entered manually. Example:
```python
checkbox_mapping = [
    {"field_name": "name", "options": ["option1", "option2"]}
]
processor = DefaultFormProcessor(
        ...
        checkbox_mapping=checkbox_mapping,
    )
```
<a id="full-example"></a>

## Full example
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Set minimum log level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

from sqlalchemy import create_engine
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.sqlalchemy_storage_connector import (
    SqlAlchemyStorageConnector,
)

extractor = DefaultFormExtractor()

engine = engine = create_engine("sqlite:///./db.db", echo=False)
connector = SqlAlchemyStorageConnector(engine)
form_number = "RA0187":
processor = DefaultFormProcessor(
    form_name=form_number,
    form_base_path=f"/home/onyxia/work/ssb-altinn-form-tools/tests/testdata/{form_number}",
    extractor=extractor,
    connector=connector,
    alias_mapping={"omsVirksomhetPerioden": "omsetning"},
)
processor.process_new_forms()

from sqlalchemy import text

with engine.connect() as conn:
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
    print("Tables:", tables)

with engine.connect() as conn:
    rows = conn.execute(text("SELECT * FROM enheter LIMIT 10;")).mappings().all()
    for row in rows:
        print(dict(row))

```
