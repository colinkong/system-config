#!/usr/bin/env python3
"""
Unpack a compressed archive in TAR.GZ format.
"""

import argparse
import glob
import os
import signal
import sys
import tarfile

if sys.version_info < (3, 2) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.2, < 4.0).')

# pylint: disable=no-self-use,too-few-public-methods


class Options(object):
    """
    Options class
    """

    def __init__(self, args):
        self._parse_args(args[1:])

    def get_archives(self):
        """
        Return list of archives.
        """
        return self._args.archives

    def get_view_flag(self):
        """
        Return view flag.
        """
        return self._args.viewFlag

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(
            description='Unpack a compressed archive in TAR.GZ format.')

        parser.add_argument('-v', dest='viewFlag', action='store_true',
                            help='Show contents of archive.')

        parser.add_argument('archives', nargs='+', metavar='file.tar.gz|file.tgz',
                            help='Archive file.')

        self._args = parser.parse_args(args)

        for archive in self._args.archives:
            if not archive.endswith('.tar.gz') and not archive.endswith('.tgz'):
                raise SystemExit(sys.argv[0] + ': Unsupported "' + archive + '" archive format.')


class Unpack(object):
    """
    Unpack class
    """

    def __init__(self, options):
        os.umask(int('022', 8))
        for archive in options.get_archives():
            print(archive + ':')
            try:
                self._archive = tarfile.open(archive, 'r:gz')
            except IOError:
                raise SystemExit(sys.argv[0] + ': Cannot open "' + archive + '" archive file.')
            if options.get_view_flag():
                self._view()
            else:
                self._unpack()

    def _unpack(self):
        for file in self._archive.getnames():
            print(file)
            if os.path.isabs(file):
                raise SystemExit(sys.argv[0] + ': Unsafe to extract file with absolute path '
                                               'outside of current directory.')
            elif file.startswith(os.pardir):
                raise SystemExit(sys.argv[0] + ': Unsafe to extract file with relative path '
                                               'outside of current directory.')
            try:
                self._archive.extract(self._archive.getmember(file))
            except (IOError, OSError):
                raise SystemExit(sys.argv[0] + ': Unable to create "' + file + '" extracted.')
            if not os.path.isfile(file):
                if not os.path.isdir(file):
                    if not os.path.islink(file):
                        raise SystemExit(
                            sys.argv[0] + ': Cannot create extracted "' + file + '" file.')

    def _view(self):
        self._archive.list()


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
            Unpack(options)
        except (EOFError, KeyboardInterrupt):
            sys.exit(114)
        except SystemExit as exception:
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
