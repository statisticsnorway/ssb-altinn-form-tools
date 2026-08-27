# Data Models
## Pydantic Domain Models
Form-level and structural types:
- FormReception — submission metadata
- ContactInfo — contact person metadata
- Unit — reporting unit
- UnitInfo — unit-level attributes
- FormNode / FormData — field-level extracted entries
- FormJsonData — supplemental JSON metadata
- ExtractedForm — fully combined extraction product

## SQLAlchemy ORM Models
(Defined in schema.py)

- kontaktinfo
- enheter
- enhetsinfo
- skjemamottak
- skjemadata
- kontroller
- kontrollutslag

Relationship logic is based on composite keys like (aar, ident, skjema, refnr).
Entity–Relationship Diagram
```mermaid
erDiagram
    ENHETER {
        int id PK
        int aar
        string ident
        string skjema
    }

    ENHETSINFO {
        int id PK
        int aar
        string ident
        string variabel
        string verdi
    }

    SKJEMAMOTTAK {
        int id PK
        int aar
        string skjema
        string ident
        string refnr
        string kommentar
        timestamp dato_mottatt
        string editert
        boolean aktiv
    }

    KONTAKTINFO {
        int id PK
        int aar
        string skjema
        string ident
        string refnr
        string kontaktperson
        string epost
        string telefon
        string bekreftet_kontaktinfo
        string kommentar_kontaktinfo
        string kommentar_krevende
    }

    SKJEMADATA {
        int id PK
        int aar
        string skjema
        string ident
        string refnr
        string feltsti
        string feltnavn
        string verdi
        string alias
        int dybde
        int indeks
    }

    KONTROLLER {
        int id PK
        int aar
        string skjema
        string kontrollid
        string kontrolltype
        string beskrivelse
        string sorting_var
        string sorting_order
    }

    KONTROLLUTSLAG {
        int id PK
        int aar
        string skjema
        string kontrollid
        string ident
        string refnr
        boolean utslag
        int verdi
    }

    ENHETER ||--o{ ENHETSINFO : "1..* (aar, ident)"
    ENHETER ||--o{ SKJEMAMOTTAK : "1..* (aar, ident, skjema)"
    ENHETER ||--o{ KONTAKTINFO : "1..* (aar, ident, skjema)"
    ENHETER ||--o{ SKJEMADATA : "1..* (aar, ident, skjema)"
    SKJEMAMOTTAK ||--o{ KONTAKTINFO : "1..* (aar, ident, skjema, refnr)"
    SKJEMAMOTTAK ||--o{ SKJEMADATA : "1..* (aar, ident, skjema, refnr)"
    KONTROLLER ||--o{ KONTROLLUTSLAG : "1..* (aar, skjema, kontrollid)"
    ENHETER ||--o{ KONTROLLUTSLAG : "1..* (aar, ident, skjema)"
```
