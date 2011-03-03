Logging Daemon Runner
=====================

Controller for a callable running as background process.

Based on the runner from python-daemon, an implementation of PEP 3143:
  http://pypi.python.org/pypi/python-daemon

PEP 3143 can be found at:
  http://www.python.org/dev/peps/pep-3143

Note that this module requires the python-daemon package.
On Debian-based systems it can be installed by running
  apt-get install python-daemon

Usage
-----

An example of how to use the runner can be found in the example.py file.

To run the example just do:
  python example.py start

To stop the process do:
  python example.py stop

And to restart:
  python example.py restart
