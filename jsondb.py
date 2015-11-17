#!/usr/bin/python

import json
import os
import logging
import signal
import errno
import fcntl
from contextlib import contextmanager


@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        pass

    original_handler = signal.signal(signal.SIGALRM, timeout_handler)

    try:
        signal.alarm(seconds)
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)


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
        with timeout(3):
            f = open(lockfile, 'w')
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            except IOError as e:
                if e.errno != errno.EINTR:
                    raise e
                self._logger.DEBUG('Lock timed out!')

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
