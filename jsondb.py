#!/usr/bin/python

import json


class JsonDB(object):
    def __init__(self, dbfile):
        self._dbfile = dbfile
        self._db = {}

    def load(self):
        try:
            with open(self._dbfile, 'r') as f:
                buf = f.readlines()
                self._db = json.load(buf)
        except IOError as e:
            print "Can't load file: %s" % e

    def save(self):
        with open(self._dbfile, 'w') as f:
            json.dump(self._db, f)

    def read(self, key):
        return self._db.get(key)

    def write(self, key, value):
        self._db[key] = value


mydb = JsonDB('/tmp/tototo')
mydb.load()
foo = mydb.read('toto')
