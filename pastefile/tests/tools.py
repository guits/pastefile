#!/usr/bin/python

import os
import pastefile.app as flaskr
from pastefile import utils


def write_random_file(filename):
    "Write file with a random content and return the md5"
    rnd_str = os.urandom(1024)
    with open(filename, 'w+') as f:
        f.writelines(rnd_str)
    return utils.get_md5(filename)
