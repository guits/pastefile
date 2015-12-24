#!/usr/bin/python

import os
from os.path import join as osjoin
import unittest
import json
import shutil
import mock
os.environ['PASTEFILE_SETTINGS'] = '../pastefile-test.cfg'
os.environ['TESTING'] = 'TRUE'

import pastefile.app as flaskr
from pastefile.tests.tools import write_random_file, write_file
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
        assert 'Get infos about one file' in rv.get_data()

    def test_ls(self):
        # Test ls without files
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        self.assertEquals('200 OK', rv.status)
        self.assertEquals(json.loads(rv.get_data()), {})

        # With one posted file
        _file = osjoin(self.testdir, 'test_file')
        last_file_md5 = write_random_file(_file) # keep md5 for next test
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile_random.file'),})
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        self.assertEquals('200 OK', rv.status)
        # basic check if we have an array like {md5: {name: ...}}
        filenames = [infos['name'] for md5, infos in json.loads(rv.get_data()).iteritems()]
        self.assertEquals(['test_pastefile_random.file'], filenames)

        # Add one new file. Remove the first file from disk only in the last test
        os.remove(osjoin(flaskr.app.config['UPLOAD_FOLDER'], last_file_md5))
        _file = osjoin(self.testdir, 'test_file_2')
        write_random_file(_file)
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile2_random.file'),})
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        filenames = [infos['name'] for md5, infos in json.loads(rv.get_data()).iteritems()]
        self.assertEquals(['test_pastefile2_random.file'], filenames)

        # if we lock the database, get should work
        with mock.patch('pastefile.controller.JsonDB._lock', mock.Mock(return_value=False)):
            rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        self.assertEquals(['test_pastefile2_random.file'], filenames)

        # Try with ls disables
        flaskr.app.config['DISABLE_LS'] = True
        rv = self.app.get('/ls', headers={'User-Agent': 'curl'})
        self.assertEquals(rv.get_data(), 'Administrator disabled the /ls option.\n')

    def test_upload_and_retrieve(self):
        # Upload a random file
        _file = osjoin(self.testdir, 'test_file')
        test_md5 = write_random_file(_file)
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile_random.file'),})
        self.assertEquals(rv.get_data(), "http://localhost/%s\n" % (test_md5))
        self.assertEquals(rv.status, '200 OK')

        # Get the file
        rv = self.app.get("/%s" % (test_md5), headers={'User-Agent': 'curl'})
        gotten_file = osjoin(self.testdir, 'gotten_test_file')
        gotten_test_md5 = write_file(filename=gotten_file, content=rv.get_data())

        self.assertEquals(test_md5, gotten_test_md5)
        self.assertEquals(rv.status, '200 OK')

        # Try to re upload the same file. Should return same url
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile_random.file'),})
        self.assertEquals(rv.get_data(), "http://localhost/%s\n" % (test_md5))

        # Try to upload a second file with the same filename. Both file should still available
        _file_bis = osjoin(self.testdir, 'test_file')
        test_md5_bis = write_random_file(_file_bis)
        rv = self.app.post('/', data={'file': (open(_file_bis, 'r'), 'test_pastefile_random.file'),})
        self.assertEquals(rv.get_data(), "http://localhost/%s\n" % (test_md5_bis))

        db_content = json.load(open(flaskr.app.config['FILE_LIST']))
        md5s = sorted([md5 for md5 in db_content.keys()])
        self.assertEquals(sorted([test_md5, test_md5_bis]), md5s)

        # can't lock the database, post should work for an existing file (using last test file)
        with mock.patch('pastefile.controller.JsonDB._lock', mock.Mock(return_value=False)):
            # Take file from last test
            rv = self.app.post('/', data={'file': (open(_file_bis, 'r'), 'test_pastefile_random.file'),})
        self.assertEquals(rv.get_data(), "http://localhost/%s\n" % (test_md5_bis))

        # can't lock the database, get should work (using last test file)
        with mock.patch('pastefile.controller.JsonDB._lock', mock.Mock(return_value=False)):
            # Take file from last test
            rv = self.app.get("/%s" % (test_md5_bis), headers={'User-Agent': 'curl'})
        gotten_file = osjoin(self.testdir, 'gotten_test_file')
        gotten_test_md5 = write_file(filename=gotten_file, content=rv.get_data())
        self.assertEquals(test_md5_bis, gotten_test_md5)
        self.assertEquals(rv.status, '200 OK')

        # can't lock the database, post should NOT work for new file
        with mock.patch('pastefile.controller.JsonDB._lock', mock.Mock(return_value=False)):
            _file = osjoin(self.testdir, 'test_file')
            test_md5 = write_random_file(_file)
            rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile_random.file'),})
            self.assertTrue('Unable to upload the file' in rv.get_data())


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
