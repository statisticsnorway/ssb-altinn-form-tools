# Architecture
## Extraction Layer

- MetaFormExtractor defines the contract for turning raw XML-derived data (InputFormType) into:
    - ContactInfo
    - FormReception
    - Unit
    - UnitInfo
    - FormData (list)


- Implementors override:
    - extract_contact_info
    - extract_form_data
    - extract_form_reception
    - extract_unit_info

- extract_form orchestrates creation of a complete ExtractedForm.

## Processing Layer
- MetaFormProcessor defines the processing pipeline.
- DefaultFormProcessor:
    - Discovers XML files
    - Parses XML into dictionaries
    - Extracts structured models
    - Applies alias/checkbox transforms
    - Persists everything via MetaStorageConnector

## Storage Layer
- MetaStorageConnector defines transaction and insert methods.
- SqlAlchemyStorageConnector: Full production implementation.
- ParqueditStorageConnector: Work-in-progress file-based connector.