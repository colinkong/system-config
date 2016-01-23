#!/usr/bin/env python3
"""
Unmount file system securely mounted with SSH protocol.
"""

import argparse
import glob
import os
import signal
import sys

import syslib

if sys.version_info < (3, 2) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.2, < 4.0).')

# pylint: disable=no-self-use,too-few-public-methods


class Options(object):
    """
    Options class
    """

    def __init__(self, args):
        self._parse_args(args[1:])

        self._directories = []
        for directory in args[1:]:
            self._directories.append(os.path.abspath(directory))

    def get_directories(self):
        """
        Return list of directories.
        """
        return self._args.directories

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(
            description='Unmount file system securely mounted with SSH protocol.')

        parser.add_argument('directories', nargs='+', metavar='localpath',
                            help='Local directory.')
        self._args = parser.parse_args(args)


class Unmount(object):
    """
    Unmount class
    """

    def __init__(self, options):
        self._directories = options.get_directories()
        self._mount = syslib.Command('mount')
        self._fusermount = syslib.Command('fusermount')

    def run(self):
        """
        Run command
        """
        for directory in self._directories:
            self._mount.run(filter=' ' + directory + ' type fuse.sshfs ', mode='batch')
            if not self._mount.has_output():
                raise SystemExit(sys.argv[0] + ': "' + directory + '" is not a mount point.')
            elif self._mount.get_exitcode():
                raise SystemExit(sys.argv[0] + ': Error code ' + str(self._mount.get_exitcode()) +
                                 ' received from "' + self._mount.get_file() + '".')
            self._fusermount.set_args(['-u', directory])
            self._fusermount.run()


class Main(object):
    """
    Main class
    """

    def __init__(self):
        self._signals()
        if os.name == 'nt':
            self._windows_argv()
        try:
            options = Options(sys.argv)
            Unmount(options).run()
        except (EOFError, KeyboardInterrupt):
            sys.exit(114)
        except (syslib.SyslibError, SystemExit) as exception:
            sys.exit(exception)
        sys.exit(0)

    def _signals(self):
        if hasattr(signal, 'SIGPIPE'):
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    def _windows_argv(self):
        argv = []
        for arg in sys.argv:
            files = glob.glob(arg)  # Fixes Windows globbing bug
            if files:
                argv.extend(files)
            else:
                argv.append(arg)
        sys.argv = argv


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
