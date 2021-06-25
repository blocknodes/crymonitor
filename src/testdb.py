from models import Base
from models import delete_all_table
from models import get_db_session
from models import Event
from models import Sequence
from models import Holder
import decimal
import json
import tqdm
engine, DBSession = get_db_session('root:1@172.16.0.112/crypto')
sess = DBSession()
Base.metadata.create_all(engine)
from sqlalchemy import and_, or_, not_


import sys

#d={'blocknum':111, 'logindex':1, 'txhash':'0xd11342c2bdae1598d06ffa235e1aa99b842c79a5f81b13896c8bb6eee8e6211b','fr': '0x811beEd0119b4AfCE20D2583EB608C6F7AF1954f', 'to': '0xf85D3886bda22C444f71065c5Cba3a73D8B9C7F2', 'value': 287345289140.947906864228012127, 'timestamp': '2020-08-05T15:58:11'}
#event = Event(**d)
#with sess.begin():
#    sess.add(event)

decimal.getcontext().prec=36

def update_holder(sess, event):
    if event.value == decimal.Decimal(0):
        return
    holder_src = sess.query(Holder).filter(Holder.addr==event.src).first()
    if holder_src is None:
        holder_src = Holder(addr=event.src, balance=0)
        sess.add(holder_src)

    holder_dst = sess.query(Holder).filter(Holder.addr==event.dst).first()
    if holder_dst is None:
        holder_dst = Holder(addr=event.dst, balance=0)
        sess.add(holder_dst)

    holder_src.balance = holder_src.balance - decimal.Decimal(event.value)
    holder_dst.balance = holder_dst.balance + decimal.Decimal(event.value)

    if holder_src.balance == decimal.Decimal(0):
        sess.delete(holder_src)
   
    if holder_dst.balance == decimal.Decimal(0):
        sess.delete(holder_dst)

if __name__ == '__main__':

    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        delete_all_table()
        print('drop all tables')
        exit(0)
    record = json.load(open(sys.argv[1],'r'))
    events = record['blocks']
    i = 0
    verify_block = 0
    verify_log_index = 0
    with sess.begin():
        seq = sess.query(Sequence).first()
        if seq == None:
            seq = Sequence(curblock=0)
            sess.add(seq)

    first_time = True
    first_time = False
    start_block=int(sys.argv[2])
    print(f"start block is {start_block}")
    end_block=int(sys.argv[3])
    print(f"end block is {end_block}")
    for key in tqdm.tqdm(events.keys()):
        blocknum = int(key)
        if blocknum < start_block:
            continue
        if blocknum > end_block:
            print('we stop')
            break
        txs = events[key]
        for txhash in txs.keys():
            logs = txs[txhash]
            for logindex_str in logs.keys():
                logindex = int(logindex_str)
               # if blocknum < verify_block or (blocknum == verify_block and logindex <= verify_log_index):
               #     print('fuck ' + key +'block num reverse')
               #     exit(1)
                verify_block = blocknum
                verify_log_index = logindex
                log = logs[logindex_str]
                event_db = {}
                event_db['blocknum'] = blocknum
                event_db['logindex'] = logindex
                event_db['txhash'] = txhash
                event_db['src'] = log['from']
                event_db['dst'] = log['to']
                event_db['value'] = log['value'] 
                event_db['timestamp']= log['timestamp']
                event = Event(**event_db)
                with sess.begin():
                    seq = sess.query(Sequence).first()
                    if first_time:
                        old_event = sess.query(Event).filter(
                                and_(
                            Event.blocknum == blocknum,
                            Event.txhash == txhash,
                            Event.logindex == logindex)).first()
                        if not old_event and seq.curblock !=0:
                            print(f'{blocknum}-{txhash}-{logindex} not found chain reorg')
                            exit(1)
                        old_events = sess.query(Event).filter(Event.blocknum >= blocknum)
                        for old_event in old_events:
                            tmp = old_event.src
                            old_event.src = old_event.dst
                            old_event.dst = tmp
                            update_holder(sess, old_event)
                        delete_num = old_events.delete() 
                        print(f'delete {delete_num} old events')
                        first_time = False
                    update_holder(sess,event)
                    sess.add(event)
                    seq.curblock= blocknum
                    
#    for k,v in events:
#        print(k)
    print(seq)
