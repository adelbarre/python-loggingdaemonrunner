#!/usr/bin/env python

from distutils.core import setup

setup(name='loggingdaemonrunner',
        version='0.1',
        description='Logging daemon runner library',
        author='Tarak Blah',
        author_email='tblah@web.de',
        packages=['loggingdaemonrunner'],
        url='http://github.com/tarak/python-loggingdaemonrunner',
        license="BSD",
        classifiers=[
            'License :: OSI Approved :: BSD License',
            'Environment :: No Input/Output (Daemon)',
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Programming Language :: Python'],
        long_description="""A daemon runner class that supports the
redirection of sys.stdin and sys.stderr to a logging.logger.
""")
