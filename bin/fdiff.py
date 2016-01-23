#!/usr/bin/env python3
"""
Show summary of differences between two directories recursively.
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

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(
            description='Show summary of differences between two directories recursively.')

        parser.add_argument('directories', nargs=2, metavar='directory',
                            help='Directory to compare.')

        self._args = parser.parse_args(args)

    def get_directory_1(self):
        """
        Return directory 1.
        """
        return self._args.directories[0]

    def get_directory_2(self):
        """
        Return directory 2.
        """
        return self._args.directories[1]


class Diff(object):
    """
    Difference class
    """

    def __init__(self, options):
        self._diffdir(options.get_directory_1(), options.get_directory_2())

    def _diffdir(self, directory1, directory2):
        try:
            files1 = sorted([os.path.join(directory1, x) for x in os.listdir(directory1)])
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            raise SystemExit(sys.argv[0] + ': Cannot open "' + directory1 + '" directory.')

        try:
            files2 = sorted([os.path.join(directory2, x) for x in os.listdir(directory2)])
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            raise SystemExit(sys.argv[0] + ': Cannot open "' + directory2 + '" directory.')

        for file in files1:
            if os.path.isdir(file):
                if os.path.isdir(os.path.join(directory2, os.path.basename(file))):
                    self._diffdir(file, os.path.join(directory2, os.path.basename(file)))
                else:
                    print('only ', file + os.sep)
            elif os.path.isfile(file):
                if os.path.isfile(os.path.join(directory2, os.path.basename(file))):
                    self._difffile(file, os.path.join(directory2, os.path.basename(file)))
                else:
                    print('only ', file)

        for file in files2:
            if os.path.isdir(file):
                if not os.path.isdir(os.path.join(directory1, os.path.basename(file))):
                    print('only ', file + os.sep)
            elif os.path.isfile(file):
                if not os.path.isfile(os.path.join(directory1, os.path.basename(file))):
                    print('only ', file)

    def _difffile(self, file1, file2):
        fileStat1 = syslib.FileStat(file1)
        fileStat2 = syslib.FileStat(file2)

        if (fileStat1.get_size() != fileStat2.get_size()):
            print('diff ', file1 + '  ' + file2)
        elif (fileStat1.get_time() != fileStat2.get_time()):
            try:
                ifile1 = open(file1, 'rb')
            except OSError:
                print('diff ', file1 + '  ' + file2)
                return
            try:
                ifile2 = open(file2, 'rb')
            except OSError:
                print('diff ', file1 + '  ' + file2)
                return
            for _ in range(0, fileStat1.get_size(), 131072):
                chunk1 = ifile1.read(131072)
                chunk2 = ifile2.read(131072)
                if chunk1 != chunk2:
                    print('diff ', file1 + '  ' + file2)
                    return
            ifile1.close()
            ifile2.close()


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
            Diff(options)
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
