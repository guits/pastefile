#!/usr/bin/python

import os
import pastefile.app as flaskr


def write_random_file(filename):
    "Write file with a random content and return the md5"
    rnd_str = os.urandom(1024)
    with open(filename, 'w+') as f:
        f.writelines(rnd_str)
    return flaskr.get_md5(filename)
