from sqlalchemy.sql.schema import Column
from sqlalchemy import TIMESTAMP, BOOLEAN

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()

class kontaktinfo(Base):
    __tablename__ = "kontaktinfo"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(Integer)
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
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar: Column[int] = Column(Integer)
    ident = Column(String)
    skjema = Column(String)


class skjemamottak(Base):
    __tablename__ = "skjemamottak"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(Integer)
    skjema = Column(String)
    ident = Column(String)
    refnr = Column(String)
    kommentar = Column(String)
    dato_mottatt = Column(TIMESTAMP)
    editert = Column(String)
    aktiv = Column(BOOLEAN)



class enhetsinfo(Base):
    __tablename__ = "enhetsinfo"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(Integer)
    ident = Column(String)
    variabel = Column(String)
    verdi = Column(String)


class kontroller(Base):
    __tablename__ = "kontroller"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(Integer)
    skjema = Column(String)
    kontrollid = Column(String)
    kontrolltype = Column(String)
    beskrivelse = Column(String)
    sorting_var = Column(String)
    sorting_order = Column(String)


class kontrollutslag(Base):
    __tablename__ = "kontrollutslag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(Integer)
    skjema = Column(String)
    kontrollid = Column(String)
    ident = Column(String)
    refnr = Column(String)
    utslag = Column(BOOLEAN)
    verdi = Column(Integer)


class skjemadata(Base):
    __tablename__ = "skjemadata"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aar = Column(Integer)
    skjema = Column(String)
    ident = Column(String)
    refnr = Column(String)
    feltsti = Column(String)
    feltnavn = Column(String)
    verdi = Column(String)
    dybde =  Column(Integer)
    indeks =  Column(Integer)



