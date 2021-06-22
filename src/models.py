from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
import contextlib
from sqlalchemy import MetaData
from sqlalchemy.orm import registry
mapper_registry = registry()
Base = mapper_registry.generate_base()
meta = mapper_registry.metadata

def delete_all_table():
    engine, _ = get_db_session()
    with contextlib.closing(engine.connect()) as con:
        trans = con.begin()
        meta.drop_all(engine, meta.sorted_tables, checkfirst=True)
        #for table in reversed(meta.sorted_tables):
        #    con.execute(table.delete())
        trans.commit()

def get_db_session(url='root:1@192.168.0.106/crypto'):
    engine = create_engine('mysql+mysqldb://' + url)
    DBSession = sessionmaker(bind=engine)
    return engine, DBSession

#Base = declarative_base()

class Holder(Base):
    __tablename__ = 'holder'
    addr = sa.Column(sa.String(256), nullable=False, primary_key=True)
    balance = sa.Column(sa.Numeric(36))

class Event(Base):
    __tablename__ = 'event'
    id = sa.Column(sa.Integer, primary_key = True)
    blocknum = sa.Column(sa.BigInteger, nullable=True)
    txhash = sa.Column(sa.String(256), nullable=True)
    logindex = sa.Column(sa.BigInteger, nullable=True)
    src = sa.Column(sa.String(256), nullable=True)
    dst = sa.Column(sa.String(256), nullable=True)
    value = sa.Column(sa.Numeric(36))
    timestamp = sa.Column(sa.TIMESTAMP, nullable=True)

class Sequence(Base):
    __tablename__ = 'sequence'
    id = sa.Column(sa.Integer, primary_key = True)
    curblock = sa.Column(sa.BigInteger)

