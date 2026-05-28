from sqlalchemy import BOOLEAN
from sqlalchemy import TIMESTAMP
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.orm import mapped_column

Base = declarative_base()


class KontaktInfo(Base):
    """Represents contact information associated with a submitted form.

    This table stores details about the person responsible for submitting or
    verifying the form, including email, phone number, and validation status.

    Attributes:
        id (int): Auto-incrementing primary key.
        iso_period (str): Iso period of the form.
        skjema (str): Code or identifier of the form.
        ident (str): Identifier of the reporting unit.
        refnr (str): Reference number of the submitted form.
        kontaktperson (str): Name of the contact person.
        epost (str): Email address associated with the contact.
        telefon (str): Phone number for the contact person.
        bekreftet_kontaktinfo (str): Flag or marker indicating whether contact
            information has been confirmed.
        kommentar_kontaktinfo (str): Free-text comment regarding contact info.
        kommentar_krevende (str): Notes regarding challenging communication cases.
    """

    __tablename__ = "kontaktinfo"
    id = Column(Integer, primary_key=True, autoincrement=True)
    iso_period = Column(String)
    skjema = Column(String)
    ident = Column(String)
    refnr = Column(String)
    kontaktperson = Column(String)
    epost = Column(String)
    telefon = Column(String)
    bekreftet_kontaktinfo = Column(String)
    kommentar_kontaktinfo = Column(String)
    kommentar_krevende = Column(String)


class Enheter(Base):
    """Represents a reporting unit submitting a form.

    Attributes:
        id (int): Auto-incrementing primary key.
        iso_period (str): Iso period of the form.
        ident (str): Unique identifier of the reporting unit.
        skjema (str): Form code or identifier.
    """

    __tablename__ = "enheter"
    id = Column(Integer, primary_key=True, autoincrement=True)
    iso_period = Column(String)
    ident = Column(String)
    skjema = Column(String)


class SkjemaMottak(Base):
    """Represents the reception metadata for a submitted form.

    Stores information about when the form was received, whether it is active,
    and any associated comments.

    Attributes:
        id (int): Auto-incrementing primary key.
        iso_period (str): Iso period of the form.
        skjema (str): Form code or identifier.
        ident (str): Identifier of the reporting unit.
        refnr (str): Unique reference number for the form instance.
        kommentar (str): Free-text comment associated with reception.
        dato_mottatt (datetime): Timestamp of when the form was received.
        editert (str): Marker indicating whether the form has been edited.
        aktiv (bool): Indicates whether the reception entry is active.
    """

    __tablename__ = "skjemamottak"
    id = Column(Integer, primary_key=True, autoincrement=True)
    iso_period = Column(String)
    start_date = Column(TIMESTAMP)
    end_date = Column(TIMESTAMP)
    skjema = Column(String)
    ident = Column(String)
    refnr = Column(String)
    kommentar = Column(String)
    dato_mottatt = Column(TIMESTAMP)
    editert = Column(String)
    aktiv = Column(BOOLEAN)


class EnhetsInfo(Base):
    """Represents additional metadata associated with a reporting unit.

    Stores key-value attributes describing properties of the unit.

    Attributes:
        id (int): Auto-incrementing primary key.
        iso_period (str): Iso period of the form.
        ident (str): Identifier of the reporting unit.
        variabel (str): Name of the metadata variable.
        verdi (str): Value of the metadata variable.
    """

    __tablename__ = "enhetsinfo"
    id = Column(Integer, primary_key=True, autoincrement=True)
    iso_period = Column(String)
    ident = Column(String)
    variabel = Column(String)
    verdi = Column(String)


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

    __tablename__ = "kontroller"
    id = Column(Integer, primary_key=True, autoincrement=True)
    iso_period = Column(String)
    skjema = Column(String)
    kontrollid = Column(String)
    kontrolltype = Column(String)
    beskrivelse = Column(String)
    sorting_var = Column(String)
    sorting_order = Column(String)


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

    __tablename__ = "kontrollutslag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    iso_period = Column(String)
    skjema = Column(String)
    kontrollid = Column(String)
    ident = Column(String)
    refnr = Column(String)
    utslag = Column(BOOLEAN)
    verdi = Column(Integer)


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

    __abstract__ = True  # <- important
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

    __tablename__ = "skjemadata"


class SkjemadataUnedited(SkjemadataBase):
    """Same table as skjemadata, but should not be edited."""

    __tablename__ = "skjemadata_editert"


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

    __tablename__ = "optionnodes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    iso_period = Column(String)
    skjema = Column(String)
    node_name = Column(String)
    options_id = Column(String)


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

    __tablename__ = "optionslists"
    id = Column(Integer, primary_key=True, autoincrement=True)
    iso_period = Column(String)
    skjema = Column(String)
    options_id = Column(String)
    label = Column(String)
    value = Column(String)
