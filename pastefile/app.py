#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from flask import Flask, request, abort, jsonify
from flask import render_template
from pastefile import utils
from pastefile import controller


app = Flask("pastefile")
LOG = logging.getLogger(app.config['LOGGER_NAME'])
LOG.setLevel(logging.DEBUG)
hdl_stream = logging.StreamHandler()
hdl_stream.setLevel(logging.INFO)
formatter_stream = logging.Formatter('%(message)s')
hdl_stream.setFormatter(formatter_stream)
LOG.addHandler(hdl_stream)


try:
    app.config.from_envvar('PASTEFILE_SETTINGS')
    app.config['instance_path'] = app.instance_path
except RuntimeError:
    LOG.error('PASTEFILE_SETTINGS envvar is not set')
    exit(1)

try:
    if os.environ['TESTING'] == 'TRUE':
        hdl_file = logging.FileHandler(filename=app.config['LOG'])
        hdl_file.setLevel(logging.DEBUG)
        formatter_file = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        hdl_file.setFormatter(formatter_file)
        LOG.addHandler(hdl_file)
except KeyError:
    pass


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        controller.clean_files(dbfile=app.config['FILE_LIST'],
                               expire=app.config['EXPIRE'])
        return controller.upload_file(request=request, config=app.config)
    else:
        # In case no file, return help
        return abort(404)


@app.route('/<id_file>/infos', methods=['GET'])
def display_file_infos(id_file):
    file_infos = controller.get_file_info(id_file=id_file,
                                          config=app.config,
                                          env=request.environ)
    if not file_infos:
        return abort(404)
    return jsonify(file_infos)


@app.route('/<id_file>', methods=['GET', 'DELETE'])
def get_or_delete_file(id_file):
    if request.method == 'GET':
        return controller.get_file(request=request,
                                   id_file=id_file,
                                   config=app.config)
    if request.method == 'DELETE':
        try:
            if 'delete' in app.config['DISABLED_FEATURE']:
                LOG.info("[delete] Tried to call delete but this url is disabled")
                return 'Administrator disabled the delete option.\n'
        except (KeyError, TypeError):
            pass
        return controller.delete_file(request=request,
                                      id_file=id_file,
                                      dbfile=app.config['FILE_LIST'])


@app.route('/ls', methods=['GET'])
def list_all_files():
    try:
        if 'ls' in app.config['DISABLED_FEATURE']:
            LOG.info("[LS] Tried to call /ls but this url is disabled")
            return 'Administrator disabled the /ls option.\n'
    except (KeyError, TypeError):
        pass

    controller.clean_files(dbfile=app.config['FILE_LIST'],
                           expire=app.config['EXPIRE'])

    return jsonify(controller.get_all_files(request=request, config=app.config))


@app.errorhandler(404)
def page_not_found(e):
    # request.method == 'GET'
    base_url = utils.build_base_url(env=request.environ)

    helps = (
      ("Upload a file:", "curl %s -F file=@**filename**" % base_url),
      ("View all uploaded files:", "curl %s/ls" % base_url),
      ("Get infos about one file:", "curl %s/**file_id**/infos" % base_url),
      ("Get a file:", "curl -JO %s/**file_id**" % base_url),
      ("Delete a file:", "curl -XDELETE %s/**id**" % base_url),
      ("Create an alias for cli usage", 'pastefile() { curl -F file=@"$1" %s; }' % base_url),
    )
    context = {'user_agent': request.headers.get('User-Agent', ''),
               'helps': helps}
    return render_template('404.html', **context), 404
