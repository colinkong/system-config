#!/usr/bin/env python3
"""
Convert filename to uppercase.
"""

import sys
if sys.version_info < (3, 2) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.2, < 4.0).')
if __name__ == '__main__':
    sys.path = sys.path[1:] + sys.path[:1]

import argparse
import glob
import os
import signal

import syslib


class Options(syslib.Dump):

    def __init__(self, args):
        self._parseArgs(args[1:])

    def getFiles(self):
        """
        Return list of files.
        """
        return self._args.files

    def _parseArgs(self, args):
        parser = argparse.ArgumentParser(description='Convert filename to uppercase.')

        parser.add_argument('files', nargs='+', metavar='file', help='File to change.')

        self._args = parser.parse_args(args)


class Upper(syslib.Dump):

    def __init__(self, options):
        for file in options.getFiles():
            if not os.path.isfile(file):
                if not os.path.isdir(file):
                    raise SystemExit(sys.argv[0] + ': Cannot find "' + file + '" file.')
            if os.sep not in file:
                newfile = file.upper()
            elif file.endswith(os.sep):
                newfile = os.path.join(os.path.dirname(file), os.path.basename(file[:-1]).upper())
            else:
                newfile = os.path.join(os.path.dirname(file), os.path.basename(file).upper())
            if newfile != file:
                print('Converting filename "' + file + '" to uppercase...')
                if os.path.isfile(newfile):
                    raise SystemExit(
                        sys.argv[0] + ': Cannot rename over existing "' + newfile + '" file.')
                try:
                    os.rename(file, newfile)
                except OSError:
                    raise SystemExit(
                        sys.argv[0] + ': Cannot rename "' + file + '" file to "' + newfile + '".')


class Main:

    def __init__(self):
        self._signals()
        if os.name == 'nt':
            self._windowsArgv()
        try:
            options = Options(sys.argv)
            Upper(options)
        except (EOFError, KeyboardInterrupt):
            sys.exit(114)
        except SystemExit as exception:
            sys.exit(exception)
        sys.exit(0)

    def _signals(self):
        if hasattr(signal, 'SIGPIPE'):
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    def _windowsArgv(self):
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
