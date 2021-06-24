import datetime
import time
import logging
from web3.datastructures import AttributeDict
from abc import ABC, abstractmethod

from models import get_db_session
from sqlalchemy import and_, or_, not_, func
from models import Base
from models import delete_all_table
from models import get_db_session
from models import Event
from models import Sequence
from models import Holder
import decimal

class EventScannerState(ABC):
    """Application state that remembers what blocks we have scanned in the case of crash.
    """

    @abstractmethod
    def get_last_scanned_block(self) -> int:
        """Number of the last block we have scanned on the previous cycle.

        :return: 0 if no blocks scanned yet
        """

    @abstractmethod
    def start_chunk(self, block_number: int):
        """Scanner is about to ask data of multiple blocks over JSON-RPC.

        Start a database session if needed.
        """

    @abstractmethod
    def end_chunk(self, block_number: int):
        """Scanner finished a number of blocks.

        Persistent any data in your state now.
        """

    @abstractmethod
    def process_event(self, block_when: datetime.datetime, event: AttributeDict) -> object:
        """Scanner finished a number of blocks.

        Persistent any data in your state now.
        """

    @abstractmethod
    def delete_data(self, since_block: int) -> int:
        """Delete any data since this block was scanned.

        Purges any potential minor reorg data.
        """

class DBScannerState(EventScannerState):
    def __init__(self, db_url):
        self.engine, self.DBSESS = get_db_session(db_url)
        self.sess = self.DBSESS()
        self.event_cache=[]

    def get_last_block(self):
        """
        just return txhash set in a block to detect minor reorg
        """
        curblock = self.get_last_scanned_block()
        txhash_set = set()
        with self.sess.begin():
            block = self.sess.query(Event).filter(Event.blocknum == curblock)
            for event in block:
                txhash_set.add(event.__dict__['txhash'])
        return txhash_set, curblock

    def get_last_scanned_block(self) -> int:
        """Number of the last block we have scanned on the previous cycle.

        :return: 0 if no blocks scanned delete_potentially_forked_block_data
        """
        curblock = 0
        with self.sess.begin():
            seq = self.sess.query(Sequence).first()
            if seq == None:
                seq = Sequence(curblock=curblock)
                self.sess.add(seq)
            else:
                curblock = seq.curblock
        return curblock


    def start_chunk(self, block_number: int, chunk_size: int):
        """Scanner is about to ask data of multiple blocks over JSON-RPC.

        Start a database session if needed.
        """
        pass

    def update_holder(self, sess, event):
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

    def end_chunk(self, block_number: int):
        """Scanner finished a number of blocks.

        Persistent any data in your state now.
        """
        with self.sess.begin():
            seq = self.sess.query(Sequence).first()
            if seq == None:
                new_seq = Sequence(curblock=block_num)
                self.sess.add(new_seq)
            else:
                seq.curblock=block_number
            for event in self.event_cache:
                self.sess.add(event)
                self.update_holder(self.sess, event)
        self.event_cache=[]
                
    def rollback_last(self):
        with self.sess.begin():
            seq = self.sess.query(Sequence).first()
            if seq == None:
                return
            last_block_num = seq.curblock
            events = self.sess.query(Event).filter(Event.blocknum == last_block_num)
            for old_event in events:
                tmp = old_event.src
                old_event.src = old_event.dst
                old_event.dst = tmp
                self.update_holder(self.sess, old_event)            
            events.delete()
            seq.curblock = self.sess.query(func.max(Event.blocknum)).scalar()
            pass


    def process_event(self, block_when: datetime.datetime, event: AttributeDict) -> object:
        """Process incoming events.

        This function takes raw events from Web3, transforms them to your application internal
        format, then saves them in a database or some other state.

        :param block_when: When this block was mined

        :param event: Symbolic dictionary of the event data

        :return: Internal state structure that is the result of event tranformation.
        """
        """Record a ERC-20 transfer in our database."""
        # Events are keyed by their transaction hash and log index
        # One transaction may contain multiple events
        # and each one of those gets their own log index

        # event_name = event.event # "Transfer"
        log_index = event.logIndex  # Log index within the block
        # transaction_index = event.transactionIndex  # Transaction index within the block
        txhash = event.transactionHash.hex()  # Transaction hash
        block_number = event.blockNumber

        # Convert ERC-20 Transfer event to our internal format
        args = event["args"]
        transfer = {
            "blocknum": block_number,
            "logindex": log_index,
            "txhash": txhash,
            "src": args["from"],
            "dst": args.to,
            "value": args.value,
            "timestamp": block_when.isoformat(),
        }
        event = Event(**transfer)
        self.event_cache.append(event)
    def delete_data(self, since_block: int) -> int:
        """Delete any data since this block was scanned.

        Purges any potential minor reorg data.
        """
        pass

class JSONifiedState(EventScannerState):
    """Store the state of scanned blocks and all events.

    All state is an in-memory dict.
    Simple load/store massive JSON on start up.
    """

    def __init__(self):
        self.state = None
        self.fname = "test-state.json"
        # How many second ago we saved the JSON file
        self.last_save = 0

    def reset(self):
        """Create initial state of nothing scanned."""
        self.state = {
            "last_scanned_block": 0,
            "blocks": {},
        }

    def restore(self):
        """Restore the last scan state from a file."""
        try:
            self.state = json.load(open(self.fname, "rt"))
            print(f"Restored the state, previously {self.state['last_scanned_block']} blocks have been scanned")
        except (IOError, json.decoder.JSONDecodeError):
            print("State starting from scratch")
            self.reset()

    def save(self):
        """Save everything we have scanned so far in a file."""
        with open(self.fname, "wt") as f:
            json.dump(self.state, f)
        self.last_save = time.time()

    #
    # EventScannerState methods implemented below
    #

    def get_last_scanned_block(self):
        """The number of the last block we have stored."""
        return self.state["last_scanned_block"]

    def delete_data(self, since_block):
        """Remove potentially reorganised blocks from the scan data."""
        for block_num in range(since_block, self.get_last_scanned_block()):
            if block_num in self.state["blocks"]:
                del self.state["blocks"][block_num]

    def start_chunk(self, block_number, chunk_size):
        pass

    def end_chunk(self, block_number):
        """Save at the end of each block, so we can resume in the case of a crash or CTRL+C"""
        # Next time the scanner is started we will resume from this block
        self.state["last_scanned_block"] = block_number

        # Save the database file for every minute
        if time.time() - self.last_save > 60:
            self.save()

    def process_event(self, block_when: datetime.datetime, event: AttributeDict) -> str:
        """Record a ERC-20 transfer in our database."""
        # Events are keyed by their transaction hash and log index
        # One transaction may contain multiple events
        # and each one of those gets their own log index

        # event_name = event.event # "Transfer"
        log_index = event.logIndex  # Log index within the block
        # transaction_index = event.transactionIndex  # Transaction index within the block
        txhash = event.transactionHash.hex()  # Transaction hash
        block_number = event.blockNumber

        # Convert ERC-20 Transfer event to our internal format
        args = event["args"]
        transfer = {
            "from": args["from"],
            "to": args.to,
            "value": args.value,
            "timestamp": block_when.isoformat(),
        }

        # Create empty dict as the block that contains all transactions by txhash
        if block_number not in self.state["blocks"]:
            self.state["blocks"][block_number] = {}

        block = self.state["blocks"][block_number]
        if txhash not in block:
            # We have not yet recorded any transfers in this transaction
            # (One transaction may contain multiple events if executed by a smart contract).
            # Create a tx entry that contains all events by a log index
            self.state["blocks"][block_number][txhash] = {}

        # Record ERC-20 transfer in our database
        self.state["blocks"][block_number][txhash][log_index] = transfer

        # Return a pointer that allows us to look up this event later if needed
        return f"{block_number}-{txhash}-{log_index}"


