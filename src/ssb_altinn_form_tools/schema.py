from sqlalchemy.sql.schema import Column
from sqlalchemy import TIMESTAMP, BOOLEAN

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, Session

engine = create_engine("sqlite:///:memory:", echo=True)
Base = declarative_base()

class kontaktinfo(Base):
    __tablename__ = "kontaktinfo"
    aar = Column(Integer, primary_key=True)
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
    __tablename__ = "enheter"
    aar: Column[int] = Column(Integer, primary_key=True)
    enheter = Column(String)
    skjema = Column(String)


class skjemamottak(Base):
    __tablename__ = "skjemamottak"
    aar = Column(Integer, primary_key=True)
    skjema = Column(String)
    ident = Column(String)
    refnr = Column(String)
    kommentar = Column(String)
    dato_mottatt = Column(TIMESTAMP)
    editert = Column(String)
    aktiv = Column(BOOLEAN)



class enhetsinfo(Base):
    __tablename__ = "enhetsinfo"
    aar = Column(Integer, primary_key=True)
    ident = Column(String)
    variabel = Column(String)
    verdi = Column(String)


class kontroller(Base):
    __tablename__ = "kontroller"
    aar = Column(Integer, primary_key=True)
    skjema = Column(String)
    kontrollid = Column(String)
    kontrolltype = Column(String)
    beskrivelse = Column(String)
    sorting_var = Column(String)
    sorting_order = Column(String)


class kontrollutslag(Base):
    __tablename__ = "kontrollutslag"
    aar = Column(Integer, primary_key=True)
    skjema = Column(String)
    kontrollid = Column(String)
    ident = Column(String)
    refnr = Column(String)
    utslag = Column(BOOLEAN)

    verdi = Column(Integer)


class skjemadata(Base):
    __tablename__ = "skjemadata"
    id = Column(Integer, primary_key=True)
    feltsti = Column(String, primary_key=True)
    feltnavn = Column(String)
    verdi = Column(String)
    is_attribute = Column(BOOLEAN)
    dybde =  Column(Integer)
    ordinal =  Column(Integer, primary_key=True)
    parent_sti =  Column(String)



# Create tables
Base.metadata.create_all(engine)

