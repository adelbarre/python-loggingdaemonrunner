import logging
import logging.handlers
import time

from loggingdaemonrunner.runner import DaemonApp, LoggingDaemonRunner
from optparse import OptionParser

__version__='0.1.0'


def getRotatingFileLogger(name, filePath, logLevel=logging.DEBUG, format=None,
                          maxBytes=1048576, backupCount=6):
    format = format or '%(asctime)s - %(message)s'
    my_logger = logging.getLogger(name)
    my_logger.setLevel(logLevel)
    handler = logging.handlers.RotatingFileHandler(
                  filePath, maxBytes=maxBytes, backupCount=backupCount)
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    my_logger.addHandler(handler)
    return my_logger


def hello_world():
    while True:
        print "Hello world!"
        time.sleep(10)


if __name__ == '__main__':
    usage = "usage: %prog [options] start|stop|restart"
    version = "%prog " + __version__
    parser = OptionParser(usage, version=version)
    parser.add_option("-d", "--debug", dest="debug",
                      action="store_true", default=True,
                      help="Print debug information")
    stderr_logger = getRotatingFileLogger('stderr', 'stderr.log')
    stdout_logger = getRotatingFileLogger('stdout', 'stdout.log')
    app = DaemonApp(run=hello_world, pidfile_path="/tmp/example.pid",
                    stderr_logger=stderr_logger, stdout_logger=stdout_logger)
    d = LoggingDaemonRunner(app, parser)
    d.do_action()
