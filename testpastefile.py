#!/usr/bin/python

import pastefile.app as flaskr
import unittest


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        flaskr.app.config['TESTING'] = True
        self.app = flaskr.app.test_client()

    def tearDown(self):
        pass

    def test_slash(self):
        rv = self.app.get('/', headers={'User-Agent': 'curl'})
        assert 'Get infos about one file' in rv.data

    def test_ls(self):
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        print type(rv)
        assert '200 OK' == rv.status

    def test_upload(self):
        pass

if __name__ == '__main__':
    unittest.main()
