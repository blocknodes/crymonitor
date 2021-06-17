import configparser
import logging

from EventManager import EventManager


if __name__ == "__main__":
    config = configparser.ConfigParser()
    logging.basicConfig(level=logging.DEBUG)
    logging.debug('what the fuck!')
    print("hello")
