#!/usr/bin/python

import os
from os.path import join as osjoin
import unittest
import json
import shutil
os.environ['PASTEFILE_SETTINGS'] = '../pastefile-test.cfg'
os.environ['TESTING'] = 'TRUE'

import pastefile.app as flaskr
from pastefile.tests.tools import write_random_file
from pastefile import utils


class FlaskrTestCase(unittest.TestCase):

    def clean_dir(self):
        if os.path.isdir(self.testdir):
            shutil.rmtree(self.testdir)

    def setUp(self):
        self.testdir = './tests'
        flaskr.app.config['TESTING'] = True
        self.clean_dir()
        os.makedirs(osjoin(self.testdir, 'files'))
        os.makedirs(osjoin(self.testdir, 'tmp'))
        self.app = flaskr.app.test_client()

    def tearDown(self):
        self.clean_dir()

    def test_slash(self):
        rv = self.app.get('/', headers={'User-Agent': 'curl'})
        assert 'Get infos about one file' in rv.data

    def test_ls(self):
        # Test ls without files
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        self.assertEquals('200 OK', rv.status)
        self.assertEquals(json.loads(rv.data), {})

        # With one posted file
        _file = osjoin(self.testdir, 'test_file')
        last_file_md5 = write_random_file(_file) # keep md5 for next test
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile_random.file'),})
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        self.assertEquals('200 OK', rv.status)
        # basic check if we have an array like {md5: {name: ...}}
        filenames = [infos['name'] for md5, infos in json.loads(rv.data).iteritems()]
        self.assertEquals(['test_pastefile_random.file'], filenames)

        # Add one new file. Remove the first file from disk only in the last test
        os.remove(osjoin(flaskr.app.config['UPLOAD_FOLDER'], last_file_md5))
        _file = osjoin(self.testdir, 'test_file_2')
        write_random_file(_file)
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile2_random.file'),})
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        filenames = [infos['name'] for md5, infos in json.loads(rv.data).iteritems()]
        self.assertEquals(['test_pastefile2_random.file'], filenames)

        # Try with ls disables
        flaskr.app.config['DISABLE_LS'] = True
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        self.assertEquals(rv.data, 'Administrator disabled the /ls option.\n')

        # TODO
        # optionnal : if we lock the database, get should work

    def test_upload_and_retrieve(self):
        # Upload a random file
        _file = osjoin(self.testdir, 'test_file')
        test_md5 = write_random_file(_file)
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile_random.file'),})
        self.assertEquals(rv.data, "http://localhost/%s\n" % (test_md5))
        self.assertEquals(rv.status, '200 OK')
        rv = self.app.get("/%s" % (test_md5), headers={'User-Agent': 'curl'})
        self.assertEquals(rv.status, '200 OK')

        # TODO
        # Try to re upload the same file. Should return same url
        # Try to upload a second file with the same filename. Both file should still available
        # optionnal : if we lock the database, post should NOT work
        # optionnal : if we lock the database, get should work

    def test_delete_file(self):
        # TODO
        # Try to delete an existing file
        # Try to delete a non existing file, should return 404
        # Try to delete a file only in database (already deleted on the disk). Should just remove from the DB
        # optionnal : if we lock the database, should NOT work
        pass

    def test_burn_after_read(self):
        # TODO
        # Try to upload a file and get it one time.
        # Try to get the file a second time, it should NOT work
        # optionnal : if we lock the database, should NOT work
        pass

    def test_clean_file(self):
        # TODO
        # Try to upload 3 file
        #   * Remove one of them from the disk
        #   * Force a second to expire in the db.
        #   We should have at the end 1 file on disk and db
        # optionnal : if we lock the database, should NOT work
        pass

    def test_infos(self):
        # TODO
        # Try to get info on an existing file and validate some parameters is valide. Like name or md5
        # Try to get info on a wrong url. should return false
        # Try to get info on a file only in DB. (not on disk). Should return false
        # optionnal : if we lock the database, should work
        pass

if __name__ == '__main__':
    unittest.main()
