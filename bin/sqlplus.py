#!/usr/bin/env python3
"""
Wrapper for "sqlplus" command
"""

import os
import signal
import sys
from pathlib import Path

import command_mod
import file_mod
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
        if os.linesep != '\n':
            def _open(file, *args, **kwargs):  # type: ignore
                if 'newline' not in kwargs and args and 'b' not in args[0]:
                    kwargs['newline'] = '\n'
                return open(str(file), *args, **kwargs)
            Path.open = _open  # type: ignore

    @staticmethod
    def run() -> None:
        """
        Start program
        """
        name = Path(sys.argv[0]).stem

        # Re-direct $HOME/oradiag_<user> to /tmp/<user>/oradiag_<user>
        os.environ['HOME'] = file_mod.FileUtil.tmpdir()

        command = command_mod.Command(name, errors='stop')
        command.set_args(sys.argv[1:])
        subtask_mod.Exec(command.get_cmdline()).run()


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
