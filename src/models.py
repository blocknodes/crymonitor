from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa

def get_db_session(url='root:1@192.168.0.100/crypto'):
    engine = create_engine('mysql+mysqldb://' + url)
    DBSession = sessionmaker(bind=engine)
    return engine, DBSession

Base = declarative_base()

class Holder(Base):
    __tablename__ = 'holder'
    address = sa.Column(sa.String(256), nullable=False, primary_key=True)
    balance = sa.Column(sa.Numeric(36,18))

class Event(Base):
    __tablename__ = 'event'
    id = sa.Column(sa.Integer, primary_key = True)
    blocknum = sa.Column(sa.BigInteger, nullable=True)
    txhash = sa.Column(sa.String(256), nullable=True)
    logindex = sa.Column(sa.BigInteger, nullable=True)
    fr = sa.Column(sa.String(256), nullable=True)
    to = sa.Column(sa.String(256), nullable=True)
    value = sa.Column(sa.Numeric(36,18))
    timestamp = sa.Column(sa.TIMESTAMP, nullable=True)
