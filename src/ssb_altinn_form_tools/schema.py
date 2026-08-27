from datetime import datetime

from sqlalchemy import BOOLEAN
from sqlalchemy import TIMESTAMP
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy ORM base class."""

    pass


class KontaktInfo(Base):
    """Represents contact information associated with a submitted form.

    Stores details about the person responsible for submitting or verifying
    the form, including contact details, validation status, and comments.

    Attributes:
        id: Auto-incrementing primary key.
        iso_period: ISO period associated with the form.
        skjema: Code or identifier of the form.
        ident: Identifier of the reporting unit.
        refnr: Reference number of the submitted form.
        kontaktperson: Name of the contact person.
        epost: Email address associated with the contact.
        telefon: Phone number for the contact person.
        bekreftet_kontaktinfo: Marker indicating whether contact information
            has been confirmed.
        kommentar_kontaktinfo: Free-text comment regarding contact information.
        kommentar_krevende: Notes regarding challenging communication cases.
    """

    __tablename__: str = "kontaktinfo"
    id: Column[int] = Column(Integer, primary_key=True, autoincrement=True)
    iso_period: Column[str] = Column(String)
    skjema: Column[str] = Column(String)
    ident: Column[str] = Column(String)
    refnr: Column[str] = Column(String)
    kontaktperson: Column[str] = Column(String)
    epost: Column[str] = Column(String)
    telefon: Column[str] = Column(String)
    bekreftet_kontaktinfo: Column[str] = Column(String)
    kommentar_kontaktinfo: Column[str] = Column(String)
    kommentar_krevende: Column[str] = Column(String)


class Enheter(Base):
    """Represents a reporting unit submitting a form.

    Attributes:
        id: Auto-incrementing primary key.
        iso_period: Iso period of the form.
        ident: Unique identifier of the reporting unit.
        skjema: Form code or identifier.
    """

    __tablename__: str = "enheter"
    id: Column[int] = Column(Integer, primary_key=True, autoincrement=True)
    iso_period: Column[str] = Column(String)
    ident: Column[str] = Column(String)
    skjema: Column[str] = Column(String)


class SkjemaMottak(Base):
    """Represents reception metadata for a submitted form.

    Stores information about the reporting period, form, reporting unit,
    form version, reception timestamp, status, and associated comments.

    Attributes:
        id: Auto-incrementing primary key.
        iso_period: ISO period associated with the form.
        start_date: Start date of the reporting period.
        end_date: End date of the reporting period.
        skjema: Form code or identifier.
        skjema_versjon: Version of the submitted form, if available.
        ident: Identifier of the reporting unit.
        refnr: Reference number for the form submission.
        kommentar: Free-text comment associated with the reception.
        dato_mottatt: Timestamp when the form was received.
        status: Marker indicating whether the form has been edited.
        aktiv: Indicates whether the reception entry is active.
    """

    __tablename__: str = "skjemamottak"
    id: Column[int] = Column(Integer, primary_key=True, autoincrement=True)
    iso_period: Column[str] = Column(String)
    start_date: Column[datetime] = Column(TIMESTAMP)
    end_date: Column[datetime] = Column(TIMESTAMP)
    skjema: Column[str] = Column(String)
    skjema_versjon: Column[str] = Column(String, nullable=True)
    ident: Column[str] = Column(String)
    refnr: Column[str] = Column(String)
    kommentar: Column[str] = Column(String)
    dato_mottatt: Column[datetime] = Column(TIMESTAMP)
    status: Column[str] = Column(String)
    aktiv: Column[bool] = Column(BOOLEAN)


class EnhetsInfo(Base):
    """Represents additional metadata associated with a reporting unit.

    Stores key-value attributes describing properties of the unit.

    Attributes:
        id (int): Auto-incrementing primary key.
        iso_period (str): Iso period of the form.
        ident (str): Identifier of the reporting unit.
        variable (str): Name of the metadata variable.
        verdi (str): Value of the metadata variable.
    """

    __tablename__: str = "enhetsinfo"
    id: Column[int] = Column(Integer, primary_key=True, autoincrement=True)
    iso_period: Column[str] = Column(String)
    ident: Column[str] = Column(String)
    variable: Column[str] = Column(String)
    verdi: Column[str] = Column(String)


class Kontroller(Base):
    """Represents a control rule applied to a form.

    Each record defines a validation or consistency check that may be applied
    during form processing.

    Attributes:
        id (int): Auto-incrementing primary key.
        iso_period (str): Iso period of the form.
        skjema (str): Form code or identifier.
        kontrollid (str): Unique identifier for the control rule.
        kontrolltype (str): Type or category of the control.
        beskrivelse (str): Description of the control logic.
        sorting_var (str): Variable used for sorting control rules.
        sorting_order (str): Order key used for deterministic sorting.
    """

    __tablename__: str = "kontroller"
    id: Column[int] = Column(Integer, primary_key=True, autoincrement=True)
    iso_period: Column[str] = Column(String)
    skjema: Column[str] = Column(String)
    kontrollid: Column[str] = Column(String)
    kontrolltype: Column[str] = Column(String)
    beskrivelse: Column[str] = Column(String)
    sorting_var: Column[str] = Column(String)
    sorting_order: Column[str] = Column(String)


class KontrollUtslag(Base):
    """Represents the result of a control rule evaluation for a specific form.

    Attributes:
        id (int): Auto-incrementing primary key.
        iso_period (str): Iso period of the form.
        skjema (str): Form code or identifier.
        kontrollid (str): Identifier of the applied control rule.
        ident (str): Identifier of the reporting unit.
        refnr (str): Reference number of the evaluated form.
        utslag (bool): Whether the control rule triggered (True/False).
        verdi (int): Value associated with the control evaluation result.
    """

    __tablename__: str = "kontrollutslag"
    id: Column[int] = Column(Integer, primary_key=True, autoincrement=True)
    iso_period: Column[str] = Column(String)
    skjema: Column[str] = Column(String)
    kontrollid: Column[str] = Column(String)
    ident: Column[str] = Column(String)
    refnr: Column[str] = Column(String)
    utslag: Column[bool] = Column(BOOLEAN)
    verdi: Column[int] = Column(Integer)


@declarative_mixin
class SkjemadataBase(Base):
    """Represents a single extracted data field from a submitted form.

    Each row corresponds to an XML node in the parsed form.

    Attributes:
        id (int): Auto-incrementing primary key.
        iso_period (str): Iso period of the form.
        skjema (str): Form code or identifier.
        ident (str): Identifier of the reporting unit.
        refnr (str): Reference number of the submitted form.
        feltsti (str): Full XML path of the field.
        feltnavn (str): Name of the field/variable.
        verdi (str): Value extracted from the field.
        alias (str): Optional alias for reporting/interpretation.
        dybde (int): Nesting depth of the XML field.
        indeks (int): Index for repeated structures (arrays/lists).
    """

    __abstract__: bool = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    iso_period: Mapped[str] = mapped_column(String)
    skjema: Mapped[str] = mapped_column(String)
    ident: Mapped[str] = mapped_column(String)
    refnr: Mapped[str] = mapped_column(String)
    feltsti: Mapped[str] = mapped_column(String, nullable=True)
    feltnavn: Mapped[str] = mapped_column(String)
    verdi: Mapped[str] = mapped_column(String, nullable=True)
    alias: Mapped[str] = mapped_column(String, nullable=True)
    dybde: Mapped[int] = mapped_column(Integer, nullable=True)
    indeks: Mapped[int] = mapped_column(Integer, nullable=True)


class Skjemadata(SkjemadataBase):
    """Table for skjema data."""

    __tablename__: str = "skjemadata"


class SkjemadataUnedited(SkjemadataBase):
    """Same table as skjemadata, but should not be edited."""

    __tablename__: str = "skjemadata_editert"


class OptionNodes(Base):
    """Represents a single extracted data field from a submitted form.

    Each row corresponds to an XML node in the parsed form.

    Attributes:
        id (int): Auto-incrementing primary key.
        iso_period (str): Iso period of the form.
        skjema (str): Form code or identifier.
        node_name (str): Name of the node in the form
        options_id (str): Id for the option list
    """

    __tablename__: str = "optionnodes"
    id: Column[int] = Column(Integer, primary_key=True, autoincrement=True)
    iso_period: Column[str] = Column(String)
    skjema: Column[str] = Column(String)
    node_name: Column[str] = Column(String)
    options_id: Column[str] = Column(String)


class OptionsLists(Base):
    """Represents a single extracted data field from a submitted form.

    Each row corresponds to an XML node in the parsed form.

    Attributes:
        id (int): Auto-incrementing primary key.
        iso_period (str): Iso period of the form.
        skjema (str): Form code or identifier.
        options_id (str): Id for the option list
        label (str): Label in the form
        value (str): Value in the form
    """

    __tablename__: str = "optionslists"
    id: Column[int] = Column(Integer, primary_key=True, autoincrement=True)
    iso_period: Column[str] = Column(String)
    skjema: Column[str] = Column(String)
    options_id: Column[str] = Column(String)
    label: Column[str] = Column(String)
    value: Column[str] = Column(String)
