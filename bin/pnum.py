#!/usr/bin/env python3
"""
Renumber picture files into a numerical series.
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

    def get_directories(self):
        """
        Return list of directories.
        """
        return self._args.directories

    def get_order(self):
        """
        Return order method.
        """
        return self._args.order

    def get_reset_flag(self):
        """
        Return per directory number reset flag
        """
        return self._args.resetFlag

    def get_start(self):
        """
        Return start number.
        """
        return self._args.start[0]

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(
            description='Renumber picture files into a numerical series.')

        parser.add_argument('-ctime', action='store_const', const='ctime', dest='order',
                            default='file', help='Sort using file creation time.')
        parser.add_argument('-mtime', action='store_const', const='mtime', dest='order',
                            default='file', help='Sort using file modification time.')
        parser.add_argument('-noreset', dest='resetFlag', action='store_false',
                            help='Use same number sequence for all directories.')
        parser.add_argument('-start', nargs=1, type=int, default=[1],
                            help='Select number to start from.')

        parser.add_argument('directories', nargs='+', metavar='directory',
                            help='Directory containing picture files.')

        self._args = parser.parse_args(args)

        for directory in self._args.directories:
            if not os.path.isdir(directory):
                raise SystemExit(
                    sys.argv[0] + ': Picture directory "' + directory + '" does not exist.')


class Renumber(object):
    """
    Re-number images class
    """

    def __init__(self, options):
        startdir = os.getcwd()
        resetFlag = options.get_reset_flag()
        number = options.get_start()

        for directory in options.get_directories():
            if resetFlag:
                number = options.get_start()
            if os.path.isdir(directory):
                os.chdir(directory)
                fileStats = []
                for file in glob.glob('*.*'):
                    if (file.split('.')[-1].lower() in (
                            'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pcx', 'svg', 'tif', 'tiff')):
                        fileStats.append(syslib.FileStat(file))
                newfiles = []
                mypid = os.getpid()
                for fileStat in self._sorted(options, fileStats):
                    newfile = 'pic{0:05d}.{1:s}'.format(
                        number, fileStat.get_file().split('.')[-1].lower().replace('jpeg', 'jpg'))
                    newfiles.append(newfile)
                    try:
                        os.rename(fileStat.get_file(), str(mypid) + '-' + newfile)
                    except OSError:
                        raise SystemExit(sys.argv[0] + ': Cannot rename "' + fileStat.get_file() +
                                         '" image file.')
                    number += 1
                for file in newfiles:
                    try:
                        os.rename(str(mypid) + '-' + file, file)
                    except OSError:
                        raise SystemExit(
                            sys.argv[0] + ': Cannot rename to "' + file + '" image file.')
                os.chdir(startdir)

    def _sorted(self, options, fileStats):
        order = options.get_order()
        if order == 'mtime':
            fileStats = sorted(fileStats, key=lambda s: s.get_time())
        elif order == 'ctime':
            fileStats = sorted(fileStats, key=lambda s: s.get_time_create())
        else:
            fileStats = sorted(fileStats, key=lambda s: s.get_file())
        return fileStats


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
            Renumber(options)
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
