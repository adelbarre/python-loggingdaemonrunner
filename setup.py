#!/usr/bin/env python

from distutils.core import setup

files = ["examples.py"]

setup(name='loggingdaemonrunner',
        version='0.1',
        description='Logging daemon runner library',
        author='Tarak Blah',
        author_email='tblah@web.de',
        packages=['loggingdaemonrunner'],
        package_data = {'' : files },
        url = '', 
        platforms = ['any'],
        license = "GPL-3",
        classifiers = [
            'License :: OSI Approved :: GNU General Public License 3 (GPL-3)',
            'Development Status :: 4 - Beta',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Programming Language :: Python'],
        long_description = """A daemon runner class that supports logging from
stdout and stderr to a logfile.
"""
     )
