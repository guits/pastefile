#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import os
import tempfile
import logging
from functools import partial

LOG = logging.getLogger(__name__)


def build_base_url(env=None):
    """Build a base url from an app environment.
       return http://mypastefileurl.foo"""
    return "%s://%s" % (env['wsgi.url_scheme'], env['HTTP_HOST'])


def human_readable(size):
    """Take a float number and convert it with appropriate unit
       example 1024 -> 1K"""
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if size < 1024.0:
            return "%2f%s" % (size, unit)
        size /= 1024.0
    return "%.2f%s" % (size, 'Y')


def get_md5(filename, chunksize=2**15, bufsize=-1):
    "Return md5sum of a file"
    _sum = hashlib.md5()
    with open(filename, 'rb', bufsize) as f:
        for chunk in iter(partial(f.read, chunksize), b''):
            _sum.update(chunk)
    return _sum.hexdigest()


def write_tmpfile_to_disk(file, dest_dir):
    "Write file from request to a specific location and return the md5"

    if not file:
        raise IOError('No file')

    fd, tmp_full_filename = tempfile.mkstemp(prefix='processing-',
                                             dir=dest_dir)
    os.close(fd)
    try:
        file.save(tmp_full_filename)
    except IOError as e:
        LOG.error("Can't save tmp file: %s" % e)
        raise IOError(e)
    file_md5 = get_md5(tmp_full_filename)
    return file_md5, tmp_full_filename
