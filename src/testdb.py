from models import Base
from models import get_db_session
from models import Event
engine, DBSession = get_db_session()
sess = DBSession()
Base.metadata.create_all(engine)
d={'blocknum':111, 'logindex':1, 'txhash':'0xd11342c2bdae1598d06ffa235e1aa99b842c79a5f81b13896c8bb6eee8e6211b','fr': '0x811beEd0119b4AfCE20D2583EB608C6F7AF1954f', 'to': '0xf85D3886bda22C444f71065c5Cba3a73D8B9C7F2', 'value': 287345289140.947906864228012127, 'timestamp': '2020-08-05T15:58:11'}
event = Event(**d)
with sess.begin():
    sess.add(event)
