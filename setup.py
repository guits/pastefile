#!/usr/bin/env python

from setuptools import setup

setup(name='pastefile',
      version='0.1',
      description=('Python-Flask written daemon to share a file via http'),
      author='guits',
      author_email='guillaume@abrioux.info',
      url='https://github.com/guits/pastefile',
      packages=['pastefile'],
      scripts=['pastefile-run.py'],
     )
