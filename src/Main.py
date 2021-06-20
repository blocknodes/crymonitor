import configparser
import logging

from EventManager import EventManager
from StateManager import DBScannerState

if __name__ == "__main__":
    config = configparser.ConfigParser()
    logging.basicConfig(level=logging.DEBUG)
    logging.debug('what the fuck!')
    # Enable logs to the stdout.
    # DEBUG is very verbose level
    logging.basicConfig(level=logging.INFO)
    
    config.read('../config.ini')
    api_url = config['DEFAULT']['api_url']
    ABI = config['DEFAULT']['abi']
    addr =config['DEFAULT']['contract_addr']
    db_url = config['DEFAULT']['db_url']
    state = DBScannerState(db_url=db_url)

    scanner = EventManager(
        api_url = api_url,
        ABI = ABI,
        state=state,
        addr = addr,
        # How many maximum blocks at the time we request from JSON-RPC
        # and we are unlikely to exceed the response size limit of the JSON-RPC server
        max_chunk_scan_size=10000
    )

    scanner.run()
