#!/usr/bin/env python3
"""
Wrapper for 'eclipse' command (Ecilpse IDE for Java EE Developers)
"""

import glob
import os
import signal
import sys
from pathlib import Path

import command_mod
import subtask_mod


class Main:
    """
    Main class
    """

    def __init__(self) -> None:
        try:
            self.config()
            sys.exit(self.run())
        except (EOFError, KeyboardInterrupt):
            sys.exit(114)
        except SystemExit as exception:
            sys.exit(exception)  # type: ignore

    @staticmethod
    def config() -> None:
        """
        Configure program
        """
        if hasattr(signal, 'SIGPIPE'):
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        if os.name == 'nt':
            argv = []
            for arg in sys.argv:
                files = sorted(glob.glob(arg))  # Fixes Windows globbing bug
                if files:
                    argv.extend(files)
                else:
                    argv.append(arg)
            sys.argv = argv

    @staticmethod
    def run() -> int:
        """
        Start program
        """
        eclipse = command_mod.Command('eclipse', errors='stop')
        if len(sys.argv) == 1:
            java = command_mod.Command(Path('bin', 'java'), errors='stop')
            args = [
                '-vm',
                java.get_file(),
                '-vmargs',
                '-Xms2048m',
                '-Xmx2048m',
                '-XX:PermSize=8192m',
                '-XX:MaxPermSize=8192m',
                '-XX:-UseCompressedOops',
            ]
        else:
            args = sys.argv[1:]

        pattern = "^$|: dbind-WARNING|: Ignoring option"
        subtask_mod.Background(eclipse.get_cmdline() + args).run(
            pattern=pattern
        )

        return 0


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
