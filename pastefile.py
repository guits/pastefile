import os
import time
import hashlib
import magic
import datetime
import ConfigParser
import logging
import tempfile
from jsondb import JsonDB
from flask import Flask, request, send_from_directory, abort, jsonify, render_template
from werkzeug import secure_filename

LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)
hdl = logging.StreamHandler()
logformat = '%(asctime)s %(levelname)s -: %(message)s'
formatter = logging.Formatter(logformat)
hdl.setFormatter(formatter)
LOG.addHandler(hdl)


config = ConfigParser.ConfigParser()
config.read('./pastefile.cfg')

app = Flask(__name__)
for section in config.sections():
    for k, v in config.items(section):
        app.config[k] = v

for app_dir in ['upload_folder', 'tmp_folder']:
    if not os.path.exists(app.config[app_dir]):
        os.makedirs(app.config[app_dir])

if app.config['port'] == str(80):
    app.config['base_url'] = "http://%s" % app.config['hostname']
else:
    app.config['base_url'] = "http://%s:%s" % (app.config['hostname'],
                                               app.config['port'])


def human_readable(size):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if size < 1024.0:
            return "%2f%s" % (size, unit)
        size /= 1024.0
    return "%.2f%s" % (size, 'Y')


def get_md5(filename):
    return hashlib.md5(open(filename, 'rb').read()).hexdigest()


def get_infos_file_from_md5(md5):
    with JsonDB(app.config['file_list']) as db:
        return db.read(md5)


def clean_files(file_list):
    with JsonDB(file_list) as db:
        for k, v in db.db.iteritems():
            if int(db.db[k]['timestamp']) < int(time.time() -
               int(app.config['expire'])):
                db.db.delete(k)
                os.remove(db.db[k]['storage_full_filename'])


def infos_file(id_file):
    infos = get_infos_file_from_md5(id_file)
    file_infos = {
        'name': os.path.basename(infos['real_full_filename']),
        'md5': id_file,
        'timestamp': infos['timestamp'],
        'expire': datetime.datetime.fromtimestamp(
            int(infos['timestamp']) + int(app.config['expire'])).strftime(
                '%d-%m-%Y %H:%M:%S'),
        'type': magic.from_file(infos['storage_full_filename']),
        'size': human_readable(os.stat(infos['storage_full_filename']).st_size),
        'url': "%s/%s" % (app.config['base_url'], id_file)
    }
    return file_infos


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    clean_files(app.config['file_list'])
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            fd, tmp_full_filename = tempfile.mkstemp(
                prefix='processing-', dir=app.config['upload_folder'])
            os.close(fd)
            file.save(os.path.join(tmp_full_filename))
            file_md5 = get_md5(tmp_full_filename)
            real_full_filename = os.path.join(app.config['upload_folder'], filename)
            storage_full_filename = os.path.join(app.config['upload_folder'], file_md5)
            with JsonDB(app.config['file_list']) as db:
                if file_md5 in db.db:
                    os.remove(tmp_full_filename)
                    return abort(403)
                db.write(file_md5, {
                    'real_full_filename': real_full_filename,
                    'storage_full_filename': storage_full_filename,
                    'timestamp': int(time.time()),
                })
            os.rename(tmp_full_filename, storage_full_filename)
            return "%s/%s\n" % (app.config['base_url'], file_md5)
    return '''
    <!doctype html>
    <title>Pastefile</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


@app.route('/<id_file>/infos', methods=['GET'])
def infos(id_file):
    file_infos = infos_file(id_file)
    return jsonify(file_infos)


@app.route('/<id_file>', methods=['GET'])
def get_file(id_file):
    with JsonDB(app.config['file_list']) as db:
        if id_file in db.db:
            filename = db.db[id_file]['storage_full_filename']
            return send_from_directory(app.config['upload_folder'],
                                       os.path.basename(filename),
                                       attachment_filename=os.path.basename(db.db[id_file]['real_full_filename']),
                                       as_attachment=True)
        else:
            return abort(404)


@app.route('/ls', methods=['GET'])
def ls():
    clean_files(app.config['file_list'])
    files_list_infos = {}
    with JsonDB(app.config['file_list']) as db:
        for k, v in db.db.iteritems():
            files_list_infos[k] = infos_file(k)
    return jsonify(files_list_infos)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(app.config['port']), debug=True)
