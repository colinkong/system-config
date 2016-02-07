#!/usr/bin/env python3
"""
Wrapper for 'wine' command

Use '-reset' to clean '.wine' junk
"""

import glob
import os
import signal
import shutil
import sys

import syslib

if sys.version_info < (3, 0) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.0, < 4.0).')


class Options(object):
    """
    Options class
    """

    def __init__(self):
        self._args = None
        self.parse(sys.argv)

    def get_wine(self):
        """
        Return wine Command class object.
        """
        return self._wine

    @staticmethod
    def _reset():
        if 'HOME' in os.environ:
            directory = os.path.join(os.environ['HOME'], '.wine')
            if os.path.isdir(directory):
                print('Removing "{0:s}"...'.format(directory))
                try:
                    shutil.rmtree(directory)
                except OSError:
                    pass

    def _signal_ignore(self, sig, frame):
        pass

    def _signal_trap(self):
        signal.signal(signal.SIGINT, self._signal_ignore)
        signal.signal(signal.SIGTERM, self._signal_ignore)

    def parse(self, args):
        """
        Parse arguments
        """
        self._wine = syslib.Command('wine')

        if len(args) > 1:
            if args[1].endswith('.bat'):
                self._wine.set_flags(['cmd', '/c'])
            elif args[1].endswith('.msi'):
                self._wine.set_flags(['cmd', '/c', 'start'])
            elif args[1] == '-reset':
                self._reset()
                raise SystemExit(0)
        self._wine.set_args(args[1:])

        self._signal_trap()
        os.environ['WINEDEBUG'] = '-all'


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
        except (syslib.SyslibError, SystemExit) as exception:
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

        wine = options.get_wine()
        xrandr = syslib.Command('xrandr')
        xrandr.run(filter='^  ', mode='batch')
        resolution = 0
        for line in xrandr.get_output():
            if '*' in line:
                break
            resolution += 1

        wine.run()
        xrandr.run(filter='^  ', mode='batch')
        resolution = 0
        for line in xrandr.get_output():
            if '*' in line:
                break
            resolution += 1
        if resolution != resolution:
            xrandr.set_args(['-s', str(resolution)])
            xrandr.run(mode='batch')


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
