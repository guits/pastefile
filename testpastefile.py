#!/usr/bin/python


import os
import unittest
import json
from StringIO import StringIO
import shutil
os.environ['PASTEFILE_SETTINGS'] = '../pastefile-test.cfg'
os.environ['TESTING'] = 'TRUE'

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
        assert rv.data == '{}'

    def test_upload(self):
        rnd_str = os.urandom(1024)
        with open('./tests/test_file', 'w+') as f:
            f.writelines(rnd_str)
        test_md5 = flaskr.get_md5('./tests/test_file')
        with open('./tests/test_file', 'r') as f:
            rv = self.app.post('/', data={'file': (f, 'test_pastefile_random.file'),})
        assert rv.data == "http://localhost/%s\n" % (test_md5)
        assert rv.status == '200 OK'
        rv = self.app.get("/%s" % (test_md5), headers={'User-Agent': 'curl'})

if __name__ == '__main__':
    unittest.main()
