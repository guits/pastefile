#!/usr/bin/python

import json
import logging

LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)
hdl = logging.StreamHandler()
logformat = '%(asctime)s %(levelname)s -: %(message)s'
formatter = logging.Formatter(logformat)
hdl.setFormatter(formatter)
LOG.addHandler(hdl)


class JsonDB(object):
    def __init__(self, dbfile, logger=__name__):
        self._dbfile = dbfile
        self._logger = logging.getLogger(logger)
        self._db = {}

    def load(self):
        try:
            with open(self._dbfile, 'r') as f:
                self._db = json.load(f)
        except (IOError, AttributeError) as e:
            self._logger.debug("Can't load file: %s" % e)

    def save(self):
        with open(self._dbfile, 'w') as f:
            json.dump(self._db, f)

    def read(self, key):
        return self._db.get(key)

    def write(self, key, value):
        self._db[key] = value


mydb = JsonDB('/tmp/tototo')
mydb.load()
mydb.write('5536fc9343e9ab0aca071354084dd3cc', {
    "expire": "06-11-2015 11:09:57",
    "md5": "5536fc9343e9ab0aca071354084dd3cc",
    "name": "group",
    "size": "696.000000",
    "timestamp": "1446718197",
    "type": "ASCII text",
    "url": "http://pastefile.fr/44b204457619bd448078f36ae5b500e0"
  })
mydb.save()
foo = mydb.read('5536fc9343e9ab0aca071354084dd3cc')
print foo
