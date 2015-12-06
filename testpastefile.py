#!/usr/bin/python


import os
import mock
import unittest
os.environ['PASTEFILE_SETTINGS'] = '../pastefile-test.cfg'

import pastefile.app as flaskr


class FlaskrTestCase(unittest.TestCase):

    @mock.patch('pastefile.app.os.path.exists')
    @mock.patch('pastefile.app.os.path')
    @mock.patch('pastefile.app.os')
    @mock.patch('pastefile.app')
    def setUp(self, mock, mock_os, mock_os_path, mock_os_path_exists):
        mock_os_path_exists.exists.return_value = True
        flaskr.app.config['TESTING'] = True
        self.app = flaskr.app.test_client()

    def tearDown(self):
        pass

    def test_slash(self):
        rv = self.app.get('/', headers={'User-Agent': 'curl'})
        assert 'Get infos about one file' in rv.data

    def test_ls(self):
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        print rv.data
#        assert '200 OK' == rv.status
        assert '{}' in rv.data

    def test_upload(self):
        pass

if __name__ == '__main__':
    unittest.main()
