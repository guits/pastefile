import os
import time
import hashlib
import magic
import datetime
import ConfigParser
from flask import Flask, request, send_from_directory, abort, jsonify
from werkzeug import secure_filename

config = ConfigParser.ConfigParser()
config.read('./pastefile.cfg')

app = Flask(__name__)
for section in config.sections():
    for k, v in config.items(section):
        app.config[k] = v

if app.config['port'] == 80:
    app.config['base_url'] = "http://%s" % app.config['hostname']
else:
    app.config['base_url'] = "http://%s:%s" % (app.config['hostname'],
                                               app.config['port'])


def human_readable(size):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if size < 1024.0:
            return "%2f%s" % (size, unit)
        size /= 1024.0
    return "%2f%s" % (size, 'Y')


def get_md5(filename):
    return hashlib.md5(open(filename, 'rb').read()).hexdigest()


def get_infos_file_from_md5(md5):
    with open(app.config['file_list'], 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line.split('|')[0] == md5:
            return (line.split('|')[0],
                    line.split('|')[1],
                    line.split('|')[2].rstrip('\n'))


def clean_files(file_list):
    with open(file_list, 'r') as f:
        lines = f.readlines()
    with open(file_list, 'w') as f:
        for line in lines:
            if int(line.split('|')[2]) > int(time.time() -
               int(app.config['expire'])):
                f.write("%s" % line)
            else:
                os.remove(line.split('|')[1])


def infos_file(id_file):
    infos = get_infos_file_from_md5(id_file)
    file_infos = {}
    file_infos['name'] = os.path.basename(infos[1])
    file_infos['md5'] = id_file
    file_infos['timestamp'] = infos[2]
    file_infos['expire'] = datetime.datetime.fromtimestamp(
        int(file_infos['timestamp']) +
        int(app.config['expire'])).strftime('%d-%m-%Y %H:%M:%S')
    file_infos['type'] = magic.from_file(infos[1])
    file_infos['size'] = os.stat(infos[1]).st_size
    file_infos['url'] = "%s/%s" % (app.config['base_url'], id_file)

    return file_infos


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    clean_files(app.config['file_list'])
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            tmp_full_filename = os.path.join(
                app.config['tmp_folder'], filename)
            full_filename = os.path.join(app.config['upload_folder'], filename)
            file.save(os.path.join(tmp_full_filename))
            file_md5 = get_md5(tmp_full_filename)
            with open(app.config['file_list'], 'r') as f:
                lines = f.readlines()
            for line in lines:
                md5 = line.split('|')[0]
                path = line.split('|')[1].rstrip('\n')
                os.path.basename(path)
                if md5 == file_md5 or os.path.basename(path) == filename:
                    os.remove(tmp_full_filename)
                    return abort(403)
            os.rename(tmp_full_filename, full_filename)
            with open(app.config['file_list'], 'a') as f:
                f.writelines("%s|%s|%s\n" % (file_md5,
                             full_filename, int(time.time())))
            return "%s/%s" % (app.config['base_url'], file_md5)
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
    with open(app.config['file_list'], 'r') as f:
        for line in f:
            md5 = line.split('|')[0]
            filename = line.split('|')[1].split('/')[-1]
            if md5 == id_file:
                return send_from_directory(app.config['upload_folder'],
                                           filename.rstrip('\n'))


@app.route('/ls', methods=['GET'])
def ls():
    clean_files(app.config['file_list'])
    files_list_infos = {}
    with open(app.config['file_list'], 'r') as f:
        for line in f:
            files_list_infos[line.split('|')[0]] = infos_file(
                line.split('|')[0])
    return jsonify(files_list_infos)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(app.config['port']), debug=True)
