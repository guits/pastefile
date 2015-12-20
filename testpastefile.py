#!/usr/bin/python


import os
import unittest
import json
from StringIO import StringIO
import shutil
os.environ['PASTEFILE_SETTINGS'] = '../pastefile-test.cfg'

import pastefile.app as flaskr


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        flaskr.app.config['TESTING'] = True
        if os.path.isdir('./tests'):
            shutil.rmtree('./tests')
        os.makedirs('./tests/files')
        os.makedirs('./tests/tmp')
        self.app = flaskr.app.test_client()

    def tearDown(self):
        pass

    def test_slash(self):
        rv = self.app.get('/', headers={'User-Agent': 'curl'})
        assert 'Get infos about one file' in rv.data

    def test_ls(self):
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        assert '200 OK' == rv.status
        print "data2=%s" % rv.data
        j = json.loads(rv.data)
#        m = re.match('^\{.*\}$', rv.data)
#        assert m

    def test_upload(self):
        rnd_str = os.urandom(1024)
        test_md5 = flaskr.get_md5(StringIO(rnd_str))
        rv = self.app.post('/', data={'file': (StringIO(rnd_str), 'test_pastefile_random.file'),})
        print "data=%s\nstatus=%s\n\n" % (rv.data, rv.status)
        print test_md5

if __name__ == '__main__':
    unittest.main()
