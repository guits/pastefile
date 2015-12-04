#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                        help="specify config file,"
                             "default: /etc/pastefile.cfg",
                        default='/etc/pastefile.cfg')

    args = parser.parse_args()
    os.environ["PASTEFILE_SETTINGS"] = args.config

if __name__ == '__main__':
    parse_args()
    from pastefile.app import app
    app.run(host='0.0.0.0', port=int(app.config['DEBUG_PORT']), debug=True)
