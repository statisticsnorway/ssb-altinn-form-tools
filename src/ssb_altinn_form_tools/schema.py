from sqlalchemy import BOOLEAN
from sqlalchemy import TIMESTAMP
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class kontaktinfo(Base):
    """Represents contact information associated with a submitted form.

    This table stores details about the person responsible for submitting or
    verifying the form, including email, phone number, and validation status.

    Attributes:
        id (int): Auto-incrementing primary key.
        aar (int): Reporting year of the form.
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
    aar = Column(String)
    skjema = Column(String)
    ident = Column(String)
    refnr = Column(String)
    kontaktperson = Column(String)
    epost = Column(String)
    telefon = Column(String)
    bekreftet_kontaktinfo = Column(String)
    kommentar_kontaktinfo = Column(String)
    kommentar_krevende = Column(String)


class enheter(Base):
    """Represents a reporting unit submitting a form.

    Attributes:
        id (int): Auto-incrementing primary key.
        aar (int): Reporting year.
        ident (str): Unique identifier of the reporting unit.
        skjema (str): Form code or identifier.
    """

    __tablename__ = "enheter"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(String)
    ident = Column(String)
    skjema = Column(String)


class skjemamottak(Base):
    """Represents the reception metadata for a submitted form.

    Stores information about when the form was received, whether it is active,
    and any associated comments.

    Attributes:
        id (int): Auto-incrementing primary key.
        aar (int): Reporting year.
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
    aar = Column(String)
    skjema = Column(String)
    ident = Column(String)
    refnr = Column(String)
    kommentar = Column(String)
    dato_mottatt = Column(TIMESTAMP)
    editert = Column(String)
    aktiv = Column(BOOLEAN)


class enhetsinfo(Base):
    """Represents additional metadata associated with a reporting unit.

    Stores key-value attributes describing properties of the unit.

    Attributes:
        id (int): Auto-incrementing primary key.
        aar (int): Reporting year.
        ident (str): Identifier of the reporting unit.
        variabel (str): Name of the metadata variable.
        verdi (str): Value of the metadata variable.
    """

    __tablename__ = "enhetsinfo"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(String)
    ident = Column(String)
    variabel = Column(String)
    verdi = Column(String)


class kontroller(Base):
    """Represents a control rule applied to a form.

    Each record defines a validation or consistency check that may be applied
    during form processing.

    Attributes:
        id (int): Auto-incrementing primary key.
        aar (int): Reporting year.
        skjema (str): Form code or identifier.
        kontrollid (str): Unique identifier for the control rule.
        kontrolltype (str): Type or category of the control.
        beskrivelse (str): Description of the control logic.
        sorting_var (str): Variable used for sorting control rules.
        sorting_order (str): Order key used for deterministic sorting.
    """

    __tablename__ = "kontroller"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(String)
    skjema = Column(String)
    kontrollid = Column(String)
    kontrolltype = Column(String)
    beskrivelse = Column(String)
    sorting_var = Column(String)
    sorting_order = Column(String)


class kontrollutslag(Base):
    """Represents the result of a control rule evaluation for a specific form.

    Attributes:
        id (int): Auto-incrementing primary key.
        aar (int): Reporting year.
        skjema (str): Form code or identifier.
        kontrollid (str): Identifier of the applied control rule.
        ident (str): Identifier of the reporting unit.
        refnr (str): Reference number of the evaluated form.
        utslag (bool): Whether the control rule triggered (True/False).
        verdi (int): Value associated with the control evaluation result.
    """

    __tablename__ = "kontrollutslag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(String)
    skjema = Column(String)
    kontrollid = Column(String)
    ident = Column(String)
    refnr = Column(String)
    utslag = Column(BOOLEAN)
    verdi = Column(Integer)


class skjemacheckboxes(Base):
    """SQLAlchemy model for storing checkbox selections in a schema form.

    Associated with a specific form (`skjema`), year (`aar`), and respondent identifier (`ident`).
    Each row corresponds to a single checkbox option and whether it was selected.

    Attributes:
        id (int): Primary key, auto-incremented.
        aar (str): Year the form submission applies to.
        skjema (str): Name or code of the form.
        ident (str): Identifier for the respondent or entity.
        refnr (str): Reference number linking to an external system or submission.
        feltsti (str): Path to the field within the form structure.
        feltnavn (str): Name of the checkbox field.
        checkbox_option (str): Specific checkbox option label or value.
        checked (bool): Whether the checkbox option was selected.
    """

    __tablename__ = "skjemacheckboxes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(String)
    skjema = Column(String)
    ident = Column(String)
    refnr = Column(String)

    feltsti = Column(String)
    feltnavn = Column(String)
    checkbox_option = Column(String)
    checked = Column(BOOLEAN)


class skjemadata(Base):
    """Represents a single extracted data field from a submitted form.

    Each row corresponds to an XML node in the parsed form.

    Attributes:
        id (int): Auto-incrementing primary key.
        aar (int): Reporting year.
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

    __tablename__ = "skjemadata"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(String)
    skjema = Column(String)
    ident = Column(String)
    refnr = Column(String)
    feltsti = Column(String)
    feltnavn = Column(String)
    verdi = Column(String)
    alias = Column(String)
    dybde = Column(Integer)
    indeks = Column(Integer)
