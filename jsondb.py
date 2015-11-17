#!/usr/bin/python

import json
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
        with timeout(self._timeout):
            self._f = open(self._dbfile, 'w+')
            try:
                fcntl.flock(self._f.fileno(), fcntl.LOCK_EX)
                self.load()
            except IOError as e:
                if e.errno != errno.EINTR:
                    raise e
                self._logger.DEBUG('Lock timed out!')

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
