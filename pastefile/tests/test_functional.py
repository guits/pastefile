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
from pastefile.jsondb import JsonDB
from pastefile import controller


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
        flaskr.app.config['DISABLED_FEATURE'] = ['ls']
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
        # Try to delete a non existing file, should return 404
        rv = self.app.delete('/foobar', headers={'User-Agent': 'curl'})
        self.assertEquals(rv.status, '404 NOT FOUND')

        # if can't lock the database, should NOT work
        _file = osjoin(self.testdir, 'test_file')
        file_md5 = write_random_file(_file)
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile_random.file'),})
        with mock.patch('pastefile.controller.JsonDB._lock', mock.Mock(return_value=False)):
            rv = self.app.delete('/%s' % file_md5, headers={'User-Agent': 'curl'})
        self.assertTrue('Lock timed out' in rv.get_data())

        # Try to delete an existing file
        self.assertTrue(os.path.isfile(osjoin(flaskr.app.config['UPLOAD_FOLDER'], file_md5)))

        rv = self.app.delete('/%s' % file_md5, headers={'User-Agent': 'curl'})

        self.assertTrue('%s deleted' % file_md5 in rv.get_data())
        self.assertFalse(os.path.isfile(osjoin(flaskr.app.config['UPLOAD_FOLDER'], file_md5)))
        with JsonDB(dbfile=flaskr.app.config['FILE_LIST']) as db:
            self.assertFalse(file_md5 in db.db.keys())

        # Try to delete a file only in database (already deleted on the disk). Should remove from the DB
        _file = osjoin(self.testdir, 'test_file')
        file_md5 = write_random_file(_file)
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile_random.file'),})
        os.remove(osjoin(flaskr.app.config['UPLOAD_FOLDER'], file_md5))

        rv = self.app.delete('/%s' % file_md5, headers={'User-Agent': 'curl'})

        with JsonDB(dbfile=flaskr.app.config['FILE_LIST']) as db:
            self.assertFalse(file_md5 in db.db.keys())

        # Try with delete disables
        flaskr.app.config['DISABLED_FEATURE'] = ['delete']
        rv = self.app.delete('/%s' % file_md5, headers={'User-Agent': 'curl'})
        self.assertEquals(rv.get_data(), 'Administrator disabled the delete option.\n')


    def test_clean_files(self):
        # Try to upload 2 file and force one to expire in the db.
        # file 1
        _file1 = osjoin(self.testdir, 'test_file1')
        file1_md5 = write_random_file(_file1)
        self.app.post('/', data={'file': (open(_file1, 'r'), 'test_pastefile_random1.file'),})
        # file 2
        _file2 = osjoin(self.testdir, 'test_file2')
        file2_md5 = write_random_file(_file2)
        self.app.post('/', data={'file': (open(_file2, 'r'), 'test_pastefile_random2.file'),})

        # Should do nothing, no file expired
        controller.clean_files(dbfile=flaskr.app.config['FILE_LIST'])

        for md5 in [file1_md5, file2_md5]:
            self.assertTrue(os.path.isfile(osjoin(flaskr.app.config['UPLOAD_FOLDER'], md5)))

        # Set expire on one file
        with JsonDB(dbfile=flaskr.app.config['FILE_LIST']) as db:
            db.db[file2_md5]['timestamp'] = 0

        # if we can't lock the database should do noting
        with mock.patch('pastefile.controller.JsonDB._lock', mock.Mock(return_value=False)):
            controller.clean_files(dbfile=flaskr.app.config['FILE_LIST'])

        for md5 in [file1_md5, file2_md5]:
            self.assertTrue(os.path.isfile(osjoin(flaskr.app.config['UPLOAD_FOLDER'], md5)))

        # If we acquire the lock, file2 should be removed on disk and db
        controller.clean_files(dbfile=flaskr.app.config['FILE_LIST'])

        self.assertTrue(os.path.isfile(osjoin(flaskr.app.config['UPLOAD_FOLDER'], file1_md5)))
        self.assertFalse(os.path.isfile(osjoin(flaskr.app.config['UPLOAD_FOLDER'], file2_md5)))
        with JsonDB(dbfile=flaskr.app.config['FILE_LIST']) as db:
            self.assertTrue(file1_md5 in db.db.keys())
            self.assertFalse(file2_md5 in db.db.keys())


    def test_burn_after_read(self):
        # Upload a random file
        _file = osjoin(self.testdir, 'test_file')
        test_md5 = write_random_file(_file)
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile_random.file'), 'burn': 'True',})

        # Try to get the file but can't acquire the lock. Shouldn't not send the file.
        with mock.patch('pastefile.controller.JsonDB._lock', mock.Mock(return_value=False)):
            rv = self.app.get('/%s' % test_md5, headers={'User-Agent': 'curl'})
        self.assertEquals("Can't lock db for burning file", rv.get_data())

        # Try to get the file with the lock acquired. Should send the file.
        rv = self.app.get('/%s' % test_md5, headers={'User-Agent': 'curl'})
        gotten_file = osjoin(self.testdir, 'gotten_test_file')
        gotten_test_md5 = write_file(filename=gotten_file, content=rv.get_data())
        self.assertEquals(test_md5, gotten_test_md5)

        # Try to get the file a second time, shouldn't work and return a 404 since it is 'burned'.
        rv = self.app.get('/%s' % test_md5, headers={'User-Agent': 'curl'})
        self.assertEquals(rv.status, '404 NOT FOUND')



    def test_check_db_consistency(self):
        # This feature is not yet implemented 
        # https://github.com/guits/pastefile/issues/48
        # TODO
        # Try to upload 2 file and remove one only from the disk.
        # if we can't lock the database should do noting
        # If we acquire the lock, this file should be removed from the db
        pass


    def test_infos(self):
        # Try to get info on a wrong url. should return false
        rv = self.app.get('/foobar/infos', headers={'User-Agent': 'curl'})
        self.assertEquals(rv.status, '404 NOT FOUND')

        # Try to get info on an existing file and validate some parameters is valide. Like name or md5
        # also if we lock the database, should work
        _file = osjoin(self.testdir, 'test_file')
        file_md5 = write_random_file(_file)
        rv = self.app.post('/', data={'file': (open(_file, 'r'), 'test_pastefile_random.file'),})
        with mock.patch('pastefile.controller.JsonDB._lock', mock.Mock(return_value=False)):
            rv = self.app.get('/%s/infos' % file_md5, headers={'User-Agent': 'curl'})

        self.assertEquals(rv.status, '200 OK')
        rv_json = json.loads(rv.get_data())
        self.assertEquals(rv_json['md5'], file_md5)
        self.assertEquals(rv_json['name'], 'test_pastefile_random.file')

        # Try to get info on a file only in DB. (not on disk). Should return false
        os.remove(osjoin(flaskr.app.config['UPLOAD_FOLDER'], file_md5))
        rv = self.app.get('/%s/infos' % file_md5, headers={'User-Agent': 'curl'})
        self.assertEquals(rv.status, '404 NOT FOUND')


if __name__ == '__main__':
    unittest.main()
