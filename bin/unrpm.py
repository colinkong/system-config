#!/usr/bin/env python3
"""
Unpack a compressed archive in RPM format.
"""

import argparse
import glob
import os
import signal
import sys

import syslib

if sys.version_info < (3, 2) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.2, < 4.0).')


class Options(object):
    """
    Options class
    """

    def __init__(self):
        self._args = None
        self.parse(sys.argv)

    def get_archives(self):
        """
        Return list of archive files.
        """
        return self._args.archives

    def get_cpio(self):
        """
        Return cpio Command class object.
        """
        return self._cpio

    def get_rpm2cpio(self):
        """
        Return rpm2cpio Command class object.
        """
        return self._rpm2cpio

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(description='Unpack a compressed archive in RPM format.')

        parser.add_argument('-v', dest='view_flag', action='store_true',
                            help='Show contents of archive.')

        parser.add_argument('archives', nargs='+', metavar='file.rpm',
                            help='Archive file.')

        self._args = parser.parse_args(args)

    def parse(self, args):
        """
        Parse arguments
        """
        self._parse_args(args[1:])

        self._rpm2cpio = syslib.Command('rpm2cpio')
        self._cpio = syslib.Command('cpio')
        if self._args.view_flag:
            self._cpio.set_args(['-idmt', '--no-absolute-filenames'])
        else:
            self._cpio.set_args(['-idmv', '--no-absolute-filenames'])


class Main(object):
    """
    Main class
    """

    def __init__(self):
        try:
            self.config()
            sys.exit(self.run())
        except (EOFError, KeyboardInterrupt):
            sys.exit(114)
        except SystemExit as exception:
            sys.exit(exception)

    @staticmethod
    def config():
        """
        Configure program
        """
        if hasattr(signal, 'SIGPIPE'):
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        if os.name == 'nt':
            argv = []
            for arg in sys.argv:
                files = glob.glob(arg)  # Fixes Windows globbing bug
                if files:
                    argv.extend(files)
                else:
                    argv.append(arg)
            sys.argv = argv

    @staticmethod
    def run():
        """
        Start program
        """
        options = Options()

        os.umask(int('022', 8))
        cpio = options.get_cpio()
        rpm2cpio = options.get_rpm2cpio()

        for archive in options.get_archives():
            if not os.path.isfile(archive):
                raise SystemExit(sys.argv[0] + ': Cannot find "' + archive + '" archive file.')
            print(archive + ':')
            rpm2cpio.set_args([archive])
            rpm2cpio.run(pipes=[cpio])
            if rpm2cpio.get_exitcode():
                raise SystemExit(sys.argv[0] + ': Error code ' + str(rpm2cpio.get_exitcode()) +
                                 ' received from "' + rpm2cpio.get_file() + '".')


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
