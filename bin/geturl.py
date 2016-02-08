#!/usr/bin/env python3
"""
Multi-threaded download accelerator.
"""

import argparse
import glob
import os
import shutil
import signal
import sys

import syslib

if sys.version_info < (3, 3) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.3, < 4.0).')


class Options(object):
    """
    Options class
    """

    def __init__(self):
        self._args = None
        self.parse(sys.argv)

    def get_threads(self):
        """
        Return number of threads.
        """
        return self._args.threads[0]

    def get_urls(self):
        """
        Return list of urls.
        """
        return self._args.urls

    def get_aria2c(self):
        """
        Return aria2c Command class object.
        """
        return self._aria2c

    @staticmethod
    def _set_libraries(command):
        libdir = os.path.join(os.path.dirname(command.get_file()), 'lib')
        if os.path.isdir(libdir):
            if syslib.info.get_system() == 'linux':
                if 'LD_LIBRARY_PATH' in os.environ:
                    os.environ['LD_LIBRARY_PATH'] = (
                        libdir + os.pathsep + os.environ['LD_LIBRARY_PATH'])
                else:
                    os.environ['LD_LIBRARY_PATH'] = libdir

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(description='Multi-threaded download accelerator.')

        parser.add_argument('-threads', nargs=1, type=int, default=[4],
                            help='Number of threads. Default is 4.')

        parser.add_argument('urls', nargs='+', metavar='url|file.url',
                            help='URL or file containing URLs.')

        self._args = parser.parse_args(args)

    def parse(self, args):
        """
        Parse arguments
        """
        self._parse_args(args[1:])

        self._aria2c = syslib.Command('aria2c')
        self._aria2c.set_flags(['--file-allocation=none', '--remote-time=true'])
        self._set_libraries(self._aria2c)

        if self._args.threads[0] < 1:
            raise SystemExit(sys.argv[0] + ': You must specific a positive integer for '
                             'number of threads.')


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
    def _get_local(directory, files_local):
        if files_local:
            if not os.path.isdir(directory):
                try:
                    os.mkdir(directory)
                except OSError:
                    raise SystemExit(
                        sys.argv[0] + ': Cannot create "' + directory + '" directory.')
            for file in files_local:
                print('file://' + file)
                try:
                    shutil.copy2(file, os.path.join(directory, os.path.basename(file)))
                except OSError:
                    raise SystemExit(sys.argv[0] + ': Cannot find "' + file + '" file.')

    @staticmethod
    def _get_remote(aria2c, files_remote):
        if files_remote:
            for file in files_remote:
                aria2c.append_arg(file.replace('https://', 'http://'))
            aria2c.run()
            if aria2c.get_exitcode():
                raise SystemExit(sys.argv[0] + ': Error code ' + str(aria2c.get_exitcode()) +
                                 ' received from "' + aria2c.get_file() + '".')

    def run(self):
        """
        Start program
        """
        self._options = Options()

        os.umask(int('022', 8))
        aria2c = self._options.get_aria2c()

        for url in self._options.get_urls():
            files_local = []
            files_remote = [url]
            if url.endswith('.url') and os.path.isfile(url):
                directory = url[:-4]
                files_remote = []
                aria2c.set_args(['--max-concurrent-downloads=' + str(self._options.get_threads()),
                                 '--dir=' + directory, '-Z'])
                try:
                    with open(url, errors='replace') as ifile:
                        for line in ifile:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                if line.startswith('file://'):
                                    if line not in files_local:
                                        files_local.append(line.replace('file://', '', 1))
                                elif line not in files_remote:
                                    files_remote.append(line)
                except OSError:
                    raise SystemExit(sys.argv[0] + ': Cannot read "' + url + '" URL file.')
            elif os.path.isdir(url):
                raise SystemExit(sys.argv[0] + ': Cannot process "' + url + '" directory.')
            else:
                aria2c.set_args(['--split=' + str(self._options.get_threads())])

            self._get_local(directory, files_local)
            self._get_remote(aria2c, files_remote)


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
