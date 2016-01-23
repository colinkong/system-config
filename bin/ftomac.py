#!/usr/bin/env python3
"""
Converts file to '\r' newline format.
"""

import argparse
import glob
import os
import signal
import sys

import syslib

if sys.version_info < (3, 3) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.3, < 4.0).')

# pylint: disable=no-self-use,too-few-public-methods


class Options(object):
    """
    Options class
    """

    def __init__(self, args):
        self._parse_args(args[1:])

    def get_files(self):
        """
        Return list of files.
        """
        return self._args.files

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(description='Converts file to "\\r" newline format.')

        parser.add_argument('files', nargs='+', metavar='file', help='File to change.')

        self._args = parser.parse_args(args)


class ToMac(object):
    """
    To MAC format class
    """

    def __init__(self, options):
        for file in options.get_files():
            if not os.path.isfile(file):
                raise SystemExit(sys.argv[0] + ': Cannot find "' + file + '" file.')
            print('Converting "' + file + '" file to "\\r" newline format...')
            try:
                with open(file, errors='replace') as ifile:
                    tmpfile = file + '-tmp' + str(os.getpid())
                    try:
                        with open(tmpfile, 'w', newline='\r') as ofile:
                            for line in ifile:
                                print(line.rstrip('\r\n'), file=ofile)
                    except OSError:
                        raise SystemExit(sys.argv[0] + ': Cannot create "' + tmpfile + '" file.')
                    except UnicodeDecodeError:
                        os.remove(tmpfile)
                        raise SystemExit(
                            sys.argv[0] + ': Cannot convert "' + file + '" binary file.')
            except OSError:
                raise SystemExit(sys.argv[0] + ': Cannot read "' + file + '" file.')
            try:
                os.rename(tmpfile, file)
            except OSError:
                os.remove(tmpfile)
                raise SystemExit(sys.argv[0] + ': Cannot update "' + file + '" file.')


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
            ToMac(options)
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
