#!/usr/bin/python

import json
import logging
import fcntl
import time
import tempfile
import os


def timeout(timeout=3, start=None):
    now = int(time.time())
    if (now - start) >= 3:
        return True
    return False


class JsonDB(object):
    def __init__(self, dbfile, logger=__name__, timeout=60, tmp_dir='/tmp'):
        self._dbfile = dbfile
        self._logger = logging.getLogger(logger)
        self.db = {}
        self._timeout = timeout
        self.lock_error = False
        self._tmp_dir = tmp_dir

    def __enter__(self):
        if not self._lock():
            self.lock_error = True
        self.load()
        return self

    def __exit__(self, type, value, traceback):
        if not self.lock_error:
            self.save()
            self._release()

    def _lock(self):
        self._start = int(time.time())
        # Open the file for lock only. If the file does not exist,
        # it will be created
        try:
            self._f = open(self._dbfile, 'a')
        except IOError as e:
            self._logger.error('Error opening db file: %s' % e)
            return False
        while True:
            try:
                fcntl.flock(self._f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except IOError:
                time.sleep(0.01)
                if timeout(timeout=self._timeout, start=self._start):
                    self._logger.critical('Unable to lock')
                    self._f.close()
                    return False

    def _release(self):
        self._f.close()

    def load(self):
        try:
            self.db = json.load(open(self._dbfile, 'r'))
        except (IOError, AttributeError, ValueError) as e:
            self._logger.debug("Can't load file: %s" % e)

    def save(self):
        try:
            fd, tmp_file = tempfile.mkstemp(prefix='jsondb-',
                                            dir=self._tmp_dir)
            json.dump(self.db, os.fdopen(fd, 'w'))
            os.rename(tmp_file, self._dbfile)

        except OSError as e:
            self._logger.error('Error while saving the db: %s' % e)

    def delete(self, key):
        del self.db[key]

    def read(self, key):
        return self.db.get(key)

    def write(self, key, value):
        self.db[key] = value
