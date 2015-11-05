#!/usr/bin/python

import json
import os
import logging


class JsonDB(object):
    def __init__(self, dbfile, logger=__name__, lockfile='/tmp/jsondb.lock'):
        self._dbfile = dbfile
        self._logger = logging.getLogger(logger)
        self._lockfile = lockfile
        self.db = {}

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, type, value, traceback):
        self.save()

    def _lock(self, lockfile):
        if os.path.isexists(lockfile):
            pass

    def _release(self):
        pass

    def load(self):
        try:
            with open(self._dbfile, 'r') as f:
                self.db = json.load(f)
        except (IOError, AttributeError, ValueError) as e:
            self._logger.debug("Can't load file: %s" % e)

    def save(self):
        with open(self._dbfile, 'w') as f:
            json.dump(self.db, f)

    def delete(self, key):
        del self.db[key]

    def read(self, key):
        return self.db.get(key)

    def write(self, key, value):
        self.db[key] = value
