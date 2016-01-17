#!/usr/bin/env python3
"""
Wrapper for GNOME/KDE/XFCE desktop file manager
"""

import glob
import os
import signal
import sys

import ck_desktop
import syslib

if sys.version_info < (3, 0) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.0, < 4.0).')

# pylint: disable=no-self-use,too-few-public-methods


class Options(object):
    """
    Options class
    """

    def __init__(self, args):
        self._desktop = ck_desktop.Desktop().detect()
        if self._desktop == 'gnome':
            self._xdesktop = syslib.Command('nautilus')
        elif self._desktop == 'kde':
            self._xdesktop = syslib.Command('dolphin')
        elif self._desktop == 'xfce':
            self._xdesktop = syslib.Command('thunar')
        else:
            self._xdesktop = syslib.Command('xterm')
        self._xdesktop.set_args(args[1:])

    def get_xdesktop(self):
        """
        Return xdesktop Command class object.
        """
        return self._xdesktop


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
            options.get_xdesktop().run(mode='exec')
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
