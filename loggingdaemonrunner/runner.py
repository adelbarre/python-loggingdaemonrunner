# -*- coding: utf-8 -*-

# A version of daemon/runner.py -
# part of python-daemon, an implementation of PEP 3143,
# that supports the redirection of sys.stdin and sys.stderr
# to a logging.logger.
#
# Based on:
# Recipe 577442: logging support for python daemon (Python)
# See: http://code.activestate.com/recipes/577442/
#
# Copyright © 2011 Tarak Blah <tblah@web.de>
# Copyright © 2009–2010 Ben Finney <ben+python@benfinney.id.au>
# Copyright © 2007–2008 Robert Niederreiter, Jens Klein
# Copyright © 2003 Clark Evans
# Copyright © 2002 Noah Spurrier
# Copyright © 2001 Jürgen Hermann
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Python Software Foundation License, version 2 or
# later as published by the Python Software Foundation.
# No warranty expressed or implied. See the file LICENSE.PSF-2 for details.

""" Logging daemon runner library."""

import sys
import os
import signal

from daemon import DaemonContext
from daemon.runner import DaemonRunnerInvalidActionError
from daemon.runner import DaemonRunnerStartFailureError
from daemon.runner import DaemonRunnerStopFailureError
from daemon.runner import emit_message
from daemon.runner import make_pidlockfile
from daemon.runner import is_pidfile_stale


def openFilesFromLoggers(loggers):
    "returns  open files used by file-based handlers of the specified loggers"
    openFiles = []
    for logger in loggers:
        for handler in logger.handlers:
            if hasattr(handler, 'stream') and \
               hasattr(handler.stream, 'fileno'):
                openFiles.append(handler.stream)
    return openFiles


class FileLikeLogger:
    "wraps a logging.Logger into a file like object"

    def __init__(self, logger):
        self.logger = logger

    def write(self, str):
        str = str.rstrip()
        if str:
            for line in str.split('\n'):
                self.logger.critical(line)

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()

    def close(self):
        for handler in self.logger.handlers:
            handler.close()


class DaemonApp(object):
    """ An application to daemonize.

        The `app` has the following attributes:

        * `stdin_path`: Filesystem path to open and replace `sys.stdin`.

        * `stdout_logger`, `stderr_logger`: Loggers to redirect
           the existing `sys.stdout` and `sys.stderr`.

        * `pidfile_path`: Absolute filesystem path to a file that
          will be used as the PID file for the daemon. If
          ``None``, no PID file will be used.

        * `pidfile_timeout`: Used as the default acquisition
          timeout value supplied to the runner's PID lock file.

        * `run`: Callable that will be invoked when the daemon is
          started.

        """
    def __init__(self, run, pidfile_path, pidfile_timeout=60,
                 stderr_logger=None, stdin_path=os.devnull,
                 stdout_logger=None):
        self.pidfile_path = pidfile_path
        self.pidfile_timeout = pidfile_timeout
        self.run = run
        self.stderr_logger = stderr_logger
        self.stdin_path = stdin_path
        self.stdout_logger = stdout_logger


class LoggingDaemonRunner(object):
    """ Controller for a callable running in a separate background process.

        The first command-line argument is the action to take:

        * 'start': Become a daemon and call `app.run()`.
        * 'stop': Exit the daemon process specified in the PID file.
        * 'restart': Stop, then start.

        """

    start_message = "started with pid %(pid)d"

    def _addLoggerFiles(self):
        "adds all files related to loggers_preserve to files_preserve"
        for logger in [self.stdout_logger, self.stderr_logger]:
            if logger:
                self.loggers_preserve.append(logger)
        loggerFiles = openFilesFromLoggers(self.loggers_preserve)
        self.daemon_context.files_preserve.extend(loggerFiles)

    def __init__(self, app):
        """ Set up the parameters of a new runner.

            The `app` argument must have the following attributes:

            * `stdin_path`: Filesystem path to open and replace `sys.stdin`.

            * `stdout_logger`, `stderr_logger`: Loggers to redirect
               the existing `sys.stdout` and `sys.stderr`.

            * `pidfile_path`: Absolute filesystem path to a file that
              will be used as the PID file for the daemon. If
              ``None``, no PID file will be used.

            * `pidfile_timeout`: Used as the default acquisition
              timeout value supplied to the runner's PID lock file.

            * `run`: Callable that will be invoked when the daemon is
              started.

            """
        self.parse_args()
        self.app = app
        self.daemon_context = DaemonContext()
        self.daemon_context.stdin = open(app.stdin_path, 'r')
        self.stdout_logger = app.stdout_logger
        self.stderr_logger = app.stderr_logger
        self.daemon_context.files_preserve = []
        self.loggers_preserve = []

        self.pidfile = None
        if app.pidfile_path is not None:
            self.pidfile = make_pidlockfile(
                app.pidfile_path, app.pidfile_timeout)
        self.daemon_context.pidfile = self.pidfile

    def _usage_exit(self, argv):
        """ Emit a usage message, then exit.
            """
        progname = os.path.basename(argv[0])
        usage_exit_code = 2
        action_usage = "|".join(self.action_funcs.keys())
        message = "usage: %(progname)s %(action_usage)s" % vars()
        emit_message(message)
        sys.exit(usage_exit_code)

    def open(self):
        self._addLoggerFiles()
        self.daemon_context.open()
        if self.stdout_logger:
            fileLikeObj = FileLikeLogger(self.stdout_logger)
            sys.stdout = fileLikeObj
        if self.stderr_logger:
            fileLikeObj = FileLikeLogger(self.stderr_logger)
            sys.stderr = fileLikeObj

    def parse_args(self, argv=None):
        """ Parse command-line arguments.
            """
        if argv is None:
            argv = sys.argv

        min_args = 2
        if len(argv) < min_args:
            self._usage_exit(argv)

        self.action = argv[1]
        if self.action not in self.action_funcs:
            self._usage_exit(argv)

    def _start(self):
        """ Open the daemon context and run the application.
            """
        if is_pidfile_stale(self.pidfile):
            self.pidfile.break_lock()

        try:
            self.open()
        except daemon.pidlockfile.AlreadyLocked:
            pidfile_path = self.pidfile.path
            raise DaemonRunnerStartFailureError(
                "PID file %(pidfile_path)r already locked" % vars())

        pid = os.getpid()
        message = self.start_message % vars()
        emit_message(message)

        self.app.run()

    def _terminate_daemon_process(self):
        """ Terminate the daemon process specified in the current PID file.
            """
        pid = self.pidfile.read_pid()
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError, exc:
            raise DaemonRunnerStopFailureError(
                "Failed to terminate %(pid)d: %(exc)s" % vars())

    def _stop(self):
        """ Exit the daemon process specified in the current PID file.
            """
        if not self.pidfile.is_locked():
            pidfile_path = self.pidfile.path
            raise DaemonRunnerStopFailureError(
                "PID file %(pidfile_path)r not locked" % vars())

        if is_pidfile_stale(self.pidfile):
            self.pidfile.break_lock()
        else:
            self._terminate_daemon_process()

    def _restart(self):
        """ Stop, then start.
            """
        self._stop()
        self._start()

    action_funcs = {
        'start': _start,
        'stop': _stop,
        'restart': _restart,
        }

    def _get_action_func(self):
        """ Return the function for the specified action.

            Raises ``DaemonRunnerInvalidActionError`` if the action is
            unknown.

            """
        try:
            func = self.action_funcs[self.action]
        except KeyError:
            raise DaemonRunnerInvalidActionError(
                "Unknown action: %(action)r" % vars(self))
        return func

    def do_action(self):
        """ Perform the requested action.
            """
        func = self._get_action_func()
        func(self)
