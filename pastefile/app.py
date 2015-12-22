#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import hashlib
import magic
import datetime
import logging
import tempfile
from jsondb import JsonDB
from flask import Flask, request, send_from_directory, abort
from flask import jsonify, render_template
from werkzeug import secure_filename
from functools import partial


app = Flask(__name__)
LOG = logging.getLogger(app.config['LOGGER_NAME'])
LOG.setLevel(logging.DEBUG)
hdl_stream = logging.StreamHandler()
hdl_stream.setLevel(logging.INFO)
formatter_stream = logging.Formatter('%(message)s')
hdl_stream.setFormatter(formatter_stream)
LOG.addHandler(hdl_stream)

try:
    app.config.from_envvar('PASTEFILE_SETTINGS')
except RuntimeError:
    LOG.error('PASTEFILE_SETTINGS envvar is not set')
    exit(1)

try:
    if os.environ['TESTING'] != 'TRUE':
        hdl_file = logging.FileHandler(filename=app.config['LOG'])
        hdl_file.setLevel(logging.DEBUG)
        formatter_file = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        hdl_file.setFormatter(formatter_file)
        LOG.addHandler(hdl_file)
except KeyError:
    pass

def build_base_url(env=None):
    return "%s://%s" % (env['wsgi.url_scheme'], env['HTTP_HOST'])


def human_readable(size):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if size < 1024.0:
            return "%2f%s" % (size, unit)
        size /= 1024.0
    return "%.2f%s" % (size, 'Y')


def get_md5(filename, chunksize=2**15, bufsize=-1):
    m = hashlib.md5()
    with open(filename, 'rb', bufsize) as f:
        for chunk in iter(partial(f.read, chunksize), b''):
            m.update(chunk)
    return m.hexdigest()


def get_infos_file_from_md5(md5):
    with JsonDB(dbfile=app.config['FILE_LIST']) as db:
        if db.lock_error:
            return False
        return db.read(md5)


def clean_files(file_list):
    with JsonDB(dbfile=file_list) as db:
        if db.lock_error:
            LOG.warning('Cant clean files')
            return False
        for k, v in list(db.db.iteritems()):
            if int(db.db[k]['timestamp']) < int(time.time() -
               int(app.config['EXPIRE'])):
                try:
                    os.remove(db.db[k]['storage_full_filename'])
                except OSError:
                    LOG.critical('Error while trying to remove %s' % db.db[k]['storage_full_filename'])
                if not os.path.isfile(db.db[k]['storage_full_filename']):
                    db.delete(k)


def infos_file(id_file, env=None):
    infos = get_infos_file_from_md5(id_file)
    if not infos:
       return False
    try:
        file_infos = {
            'name': infos['real_name'],
            'md5': id_file,
            'burn_after_read': infos['burn_after_read'],
            'timestamp': infos['timestamp'],
            'expire': datetime.datetime.fromtimestamp(
                int(infos['timestamp']) + int(app.config['EXPIRE'])).strftime(
                    '%d-%m-%Y %H:%M:%S'),
            'type': magic.from_file(infos['storage_full_filename']),
            'size': human_readable(os.stat(infos['storage_full_filename']).st_size),
            'url': "%s/%s" % (build_base_url(env=env), id_file)
        }
        return file_infos
    except:
        LOG.error('Unable to gather infos for file %s' % id_file)
        return False


def slash_post(request=None):
    clean_files(app.config['FILE_LIST'])
    value_burn_after_read = request.form.getlist('burn')
    if value_burn_after_read:
        burn_after_read = True
    else:
        burn_after_read = False
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        fd, tmp_full_filename = tempfile.mkstemp(
            prefix='processing-', dir=app.config['TMP_FOLDER'])
        os.close(fd)
        try:
            file.save(os.path.join(tmp_full_filename))
        except IOError as e:
            LOG.error("Can't save tmp file: %s" % e)
            return "Server error, contact administrator"
        file_md5 = get_md5(tmp_full_filename)
        storage_full_filename = os.path.join(app.config['UPLOAD_FOLDER'], file_md5)
        with JsonDB(dbfile=app.config['FILE_LIST']) as db:

            # Just inform for debug purpose
            if db.lock_error:
                LOG.error("Unable to get lock during file upload %s" % file_md5)

            # If we can lock, add this file in pastefile
            # tmpfile will be "removed" by rename
            if file_md5 not in db.db and not db.lock_error:

                try:
                    os.rename(tmp_full_filename, storage_full_filename)
                except OSError as e:
                    LOG.error("Can't move processing file to storage directory: %s" % e)
                    return "Server error, contact administrator"
                LOG.info("[POST] Client %s has successfully uploaded: %s (%s)" % (request.remote_addr, filename, file_md5))

                db.write(file_md5, {
                    'real_name': filename,
                    'storage_full_filename': storage_full_filename,
                    'timestamp': int(time.time()),
                    'burn_after_read': str(burn_after_read),
                })
            else:
                # Remove tmp posted file in any case
                try:
                    os.remove(tmp_full_filename)
                except OSError as e:
                    LOG.error("Can't remove tmp file: %s" % e)
                    return False

            # In the case the file is not in db, we have 2 reason :
            #  * We was not able to have the lock and write the file in the db.
            #  * Or an error occure during the file processing
            # In any case just tell the user to try later
            if db.lock_error and file_md5 not in db.db:
                LOG.info('Unable lock the db and find the file %s in db during upload' % file_md5)
                return 'Unable to upload the file, try again later ...'

        return "%s/%s\n" % (build_base_url(env=request.environ), file_md5)



@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        return slash_post(request=request)
    else:
        # In case no file, return help
        return abort(404)


@app.route('/<id_file>/infos', methods=['GET'])
def infos(id_file):
    file_infos = infos_file(id_file, env=request.environ)
    return jsonify(file_infos)


@app.route('/<id_file>', methods=['GET'])
def get_file(id_file):
    with JsonDB(dbfile=app.config['FILE_LIST']) as db:
        if db.lock_error:
            return "Lock timed out"
        if id_file not in db.db:
            return abort(404)

        filename = os.path.basename(db.db[id_file]['storage_full_filename'])
        LOG.info("[GET] Client %s has requested: %s (%s)" % (request.remote_addr, db.db[id_file]['real_name'], id_file))

        if not os.path.isabs(app.config['UPLOAD_FOLDER']):
            path = "%s/%s" % (os.path.dirname(app.instance_path), app.config['UPLOAD_FOLDER'])
        else:
            path = app.config['UPLOAD_FOLDER']

        return send_from_directory(path,
                                   filename,
                                   attachment_filename=db.db[id_file]['real_name'],
                                   as_attachment=True)


@app.route('/delete/<id_file>', methods=['GET'])
def delete_file(id_file):
    with JsonDB(dbfile=app.config['FILE_LIST']) as db:
        if db.lock_error:
            return "Lock timed out\n"
        if id_file not in db.db:
            return abort(404)
        try:
            storage_full_filename = db.db[id_file]['storage_full_filename']
            os.remove(storage_full_filename)
            LOG.info("[DELETE] Client %s has deleted: %s (%s)" % (request.remote_addr, db.db[id_file]['real_name'], id_file))
            db.delete(id_file)
            return "File %s deleted\n" % id_file
        except IOError as e:
            LOG.critical("Can't remove file: %s" % e)
            return "Error: %s\n" % e


@app.route('/ls', methods=['GET'])
def ls():
    if app.config['DISABLE_LS']:
        LOG.info("[LS] Tried to call /ls but this url is disabled")
        return 'Administrator disabled the /ls option.'
    clean_files(app.config['FILE_LIST'])
    files_list_infos = {}
    with JsonDB(dbfile=app.config['FILE_LIST'], logger=app.config['LOGGER_NAME']) as db:
        if db.lock_error:
            return "Lock timed out"
        instant_db = db.db
    for k, v in instant_db.iteritems():
        if not infos_file(k, env=request.environ):
            continue
        files_list_infos[k] = infos_file(k, env=request.environ)
    return jsonify(files_list_infos)


@app.errorhandler(404)
def page_not_found(e):
    # request.method == 'GET'
    base_url = build_base_url(env=request.environ)

    helps = {
      "Upload a file:": "curl -F file=@**filename** %s" % base_url,
      "View all uploaded files:": "curl %s/ls" % base_url,
      "Get infos about one file:": "curl %s/**file_id**/infos" % base_url,
      "Get a file:": "curl -JO %s/**file_id**" % base_url,
      }
    context = {'user_agent': request.headers.get('User-Agent', ''),
               'helps': helps}
    return render_template('404.html', **context), 404
