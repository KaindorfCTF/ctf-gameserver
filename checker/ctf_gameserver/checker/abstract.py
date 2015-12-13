#!/usr/bin/python3

from abc import ABCMeta, abstractmethod

import logging
import json
import socket
import requests

class AbstractChecker(metaclass=ABCMeta):
    """Base class for custom checker scripts

    Individual checkers should import `BaseChecker` which does the
    right thing in terms of backend depending on whether you test
    locally or the checker is run during the Contest. They must
    implement the place_flag and check_flag methods and may add
    individual __init__ code. You may override the run method but need
    to keep it morally the same

    ident used for store/retrieve are supposed to match
    [A-Za-z0-9_-]+. It must be uniq for every (service,target)
    """
    def __init__(self, tick, team, service, ip):
        self._team = team
        self._ip = ip
        self._tick = tick
        self._service = service
        self._tickduration = 300
        self._lookback = 5

    @property
    def tick(self):
        """Returns the current tick"""
        return self._tick

    def check_service(self):
        """ Check if the service is running as expected"""
        return 0

    @abstractmethod
    def check_flag(self, tick):
        """Check for the flag from tick on the tested team's server

        To be reimplemented by users
        """
        pass

    @abstractmethod
    def place_flag(self):
        """Place flag on the tested team's server

        To be reimplemented by users"""
        pass

    def store_yaml(self, ident, yaml):
        return self.store_blob(ident, json.dumps(yaml).encode('utf-8'))

    @abstractmethod
    def store_blob(self, ident, blob):
        "store binary blob on persistent storage"
        pass

    def retrieve_yaml(self, ident):
        try:
            return json.loads(self.retrieve_blob(ident).decode('utf-8'))
        except ValueError:
            return None

    @abstractmethod
    def retrieve_blob(self, ident):
        "return binary blob from persistent storage"
        pass

    @abstractmethod
    def get_flag(self, tick, payload=None):
        "returns the flag for tick possibly including payload"
        pass

    def run(self):
        try:
            logging.debug("Placing flag")
            result = self.place_flag()
            if result != 0:
                return result

            logging.debug("General Service Checks")
            result = self.check_service()
            if result != 0:
                return result

            oldesttick = max(self._tick - self._lookback, -1)
            for tick in range(self._tick, oldesttick, -1):
                logging.debug("Checking for flag of tick %d", tick)
                result = self.check_flag(tick)
                if result != 0:
                    return result

            return 0
        except socket.timeout:
            return 1
        except requests.exceptions.Timeout:
            return 1
