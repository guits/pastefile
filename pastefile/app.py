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

hdl_file = logging.FileHandler(filename=app.config['LOG'])
hdl_file.setLevel(logging.DEBUG)
formatter_file = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hdl_file.setFormatter(formatter_file)
LOG.addHandler(hdl_file)


def build_base_url(env=None):
    return "%s://%s" % (env['wsgi.url_scheme'], env['HTTP_HOST'])


def usage(env=None):
    if 'base_url' not in env:
        env['base_url'] = build_base_url(env=env)

    return ("Usage:\n\n\n  "
            "Upload a file:\n"
            "curl -F file=@<file> %(base_url)s\n\n  "
            "View all uploaded files:\n"
            "curl %(base_url)s/ls\n\n  "
            "Get infos about one file:\n"
            "curl %(base_url)s/<id>/infos\n\n  "
            "Get a file:\n"
            "curl -JO %(base_url)s/<id>\n\n\n") % env


def human_readable(size):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if size < 1024.0:
            return "%2f%s" % (size, unit)
        size /= 1024.0
    return "%.2f%s" % (size, 'Y')


def get_md5(filename):
    return hashlib.md5(open(filename, 'rb').read()).hexdigest()


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
        for k, v in db.db.iteritems():
            if int(db.db[k]['timestamp']) < int(time.time() -
               int(app.config['EXPIRE'])):
                os.remove(db.db[k]['storage_full_filename'])
                db.delete(k)


def infos_file(id_file, env=None):
    infos = get_infos_file_from_md5(id_file)
    if infos:
        file_infos = {
            'name': os.path.basename(infos['real_full_filename']),
            'md5': id_file,
            'timestamp': infos['timestamp'],
            'expire': datetime.datetime.fromtimestamp(
                int(infos['timestamp']) + int(app.config['EXPIRE'])).strftime(
                    '%d-%m-%Y %H:%M:%S'),
            'type': magic.from_file(infos['storage_full_filename']),
            'size': human_readable(os.stat(infos['storage_full_filename']).st_size),
            'url': "%s/%s" % (build_base_url(env=env), id_file)
        }
        return file_infos
    return False


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        clean_files(app.config['FILE_LIST'])
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
            real_full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
                        'real_full_filename': real_full_filename,
                        'storage_full_filename': storage_full_filename,
                        'timestamp': int(time.time()),
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

    # request.method == 'GET'
    request.environ['base_url'] = build_base_url(env=request.environ)
    if 'curl' in request.headers.get('User-Agent', []):
        return usage(env=request.environ)
    else:
        return '''
        <!doctype html>
        <title>Pastefile</title>
        <h1>Upload new File</h1>
        <form action="" method=post enctype=multipart/form-data>
          <p><input type=file name=file>
             <input type=submit value=Upload>
        </form><br><br>
        Usage:<br><br>


          View all uploaded files:<br>
            %(base_url)s/ls<br><br>

          Get infos about one file:<br>
            %(base_url)s/&#60;id&#62;/infos<br><br>

          Get a file:<br>
            %(base_url)s/&#60;id&#62;
        ''' % request.environ


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

        filename = db.db[id_file]['storage_full_filename']
        LOG.info("[GET] Client %s has requested: %s (%s)" % (request.remote_addr, os.path.basename(db.db[id_file]['real_full_filename']), id_file))
        return send_from_directory(app.config['UPLOAD_FOLDER'],
                                   os.path.basename(filename),
                                   attachment_filename=os.path.basename(db.db[id_file]['real_full_filename']),
                                   as_attachment=True)


@app.route('/ls', methods=['GET'])
def ls():
    clean_files(app.config['FILE_LIST'])
    files_list_infos = {}
    with JsonDB(dbfile=app.config['FILE_LIST'], logger=app.config['LOGGER_NAME']) as db:
        if db.lock_error:
            return "Lock timed out"
        instant_db = db.db
    for k, v in instant_db.iteritems():
        if not infos_file(k, env=request.environ):
            return abort(500)
        files_list_infos[k] = infos_file(k, env=request.environ)
    return jsonify(files_list_infos)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
