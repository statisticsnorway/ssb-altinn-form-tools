# Usage
Instantiate the Default Processor (SQLAlchemy)
```Python
engine = create_engine("sqlite:///forms.db")
storage = SqlAlchemyStorageConnector(engine)

extractor = MyExtractor()  # implements MetaFormExtractor

processor = DefaultFormProcessor(
    form_name="A123",
    form_base_path="/path/to/forms",
    extractor=extractor,
    connector=storage,
    alias_mapping={"FieldX": "alias_x"},
    checkbox_vars=["MultiChoiceField"],
)

processor.process_new_forms()
```

## Implement Your Own Extractor
If your form has any diverging needs from what is covered by the default extractor, you can replace functionality by inheriting from the metaclasses and implementing your own methods.

```python
class MyExtractor(MetaFormExtractor):
    def extract_contact_info(...): ...
    def extract_form_data(...): ...
    def extract_form_reception(...): ...
    def extract_unit_info(...): ...
```

## Run Processing
Call:
```python
processor.process_new_forms()
```
