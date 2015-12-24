#!/usr/bin/python

import os
from pastefile import utils


def write_random_file(filename):
    "Write file with a random content and return the md5"
    rnd_str = os.urandom(1024)
    return write_file(filename=filename, content=rnd_str)

def write_file(filename, content):
    "Write file on disk and return the md5"
    with open(filename, 'w+') as f:
        f.writelines(content)
    return utils.get_md5(filename)
