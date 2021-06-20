from models import Base
from models import get_db_session
from models import Event
import json
import tqdm
engine, DBSession = get_db_session()
sess = DBSession()
Base.metadata.create_all(engine)
#d={'blocknum':111, 'logindex':1, 'txhash':'0xd11342c2bdae1598d06ffa235e1aa99b842c79a5f81b13896c8bb6eee8e6211b','fr': '0x811beEd0119b4AfCE20D2583EB608C6F7AF1954f', 'to': '0xf85D3886bda22C444f71065c5Cba3a73D8B9C7F2', 'value': 287345289140.947906864228012127, 'timestamp': '2020-08-05T15:58:11'}
#event = Event(**d)
#with sess.begin():
#    sess.add(event)

if __name__ == '__main__':
    record = json.load(open('/work/we3/test-state.json.bak10-05-2021','r'))
    seq = record['last_scanned_block']
    events = record['blocks']
    i = 0
    verify_block = 0
    verify_log_index = 0
    for key in tqdm.tqdm(events.keys()):
        blocknum = int(key)
        txs = events[key]
        for txhash in txs.keys():
            logs = txs[txhash]
            for logindex_str in logs.keys():
                logindex = int(logindex_str)
                if blocknum < verify_block or (blocknum == verify_block and logindex <= verify_log_index):
                    print('fuck ' + key +'block num reverse')
                    exit(1)
                verify_block = blocknum
                verify_log_index = logindex
                log = logs[logindex_str]
                event_db = {}
                event_db['blocknum'] = blocknum
                event_db['logindex'] = logindex
                event_db['txhash'] = txhash
                event_db['fr'] = log['from']
                event_db['to'] = log['to']
                event_db['value'] = log['value'] / 1000000000000000000
                event_db['timestamp']= log['timestamp']
                event = Event(**event_db)
                with sess.begin():
                    sess.add(event)
#    for k,v in events:
#        print(k)
    print(seq)
