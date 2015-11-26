#!/usr/bin/python

import json
import logging
import errno
import fcntl
import time


def timeout(timeout=3, start=None):
    now = int(time.time())
    if (now - start) >= 3:
        return True
#logger.DEBUG('Lock timed out!')
    return False


class JsonDB(object):
    def __init__(self, dbfile, logger=__name__, timeout=5):
        self._dbfile = dbfile
        self._logger = logging.getLogger(logger)
        self.db = {}
        self._timeout = timeout

    def __enter__(self):
        self._lock()
        return self

    def __exit__(self, type, value, traceback):
        self.save()
        self._release()

    def _lock(self):
        self._start = int(time.time())
        while True:
            try:
                self._f = open(self._dbfile, 'w+')
                fcntl.flock(self._f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.load()
            except IOError as e:
                if e.errno != errno.EINTR:
                    raise e
                time.sleep(0.01)
                if timeout(timeout=self._timeout, start=self._start):
                    return True

    def _release(self):
        self._f.close()

    def load(self):
        try:
            self.db = json.load(self._f)
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
