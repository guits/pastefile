#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
from functools import partial


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
