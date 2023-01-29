#!/usr/bin/env python3
"""
Make a compressed archive using suitable tool.
"""

import argparse
import os
import signal
import sys
from pathlib import Path
from typing import List

import command_mod
import subtask_mod


class Options:
    """
    Options class
    """

    def __init__(self) -> None:
        self._args: argparse.Namespace = None
        self.parse(sys.argv)

    def get_archive(self) -> str:
        """
        Return archive location.
        """
        return self._args.archive[0]

    def get_files(self) -> List[str]:
        """
        Return list of files.
        """
        return self._args.files

    def _parse_args(self, args: List[str]) -> None:
        parser = argparse.ArgumentParser(
            description="Make a compressed archive using suitable tool.",
        )

        parser.add_argument(
            'archive',
            nargs=1,
            metavar='archive',
            help="Archive file.",
        )
        parser.add_argument(
            'files',
            nargs='*',
            metavar='file',
            help="File or directory.",
        )

        self._args = parser.parse_args(args)

    def parse(self, args: List[str]) -> None:
        """
        Parse arguments
        """
        self._parse_args(args[1:])


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

    @classmethod
    def run(cls) -> None:
        """
        Start program
        """
        options = Options()
        path = Path(options.get_archive())

        name = path.name
        if name.endswith(('.tar.7z', '.t7z')):
            command = command_mod.Command('t7z', errors='stop')
        elif name.endswith(('.tar.xz', '.txz')):
            command = command_mod.Command('txz', errors='stop')
        elif name.endswith(('.tar.lzma', '.tlz')):
            command = command_mod.Command('tlz', errors='stop')
        elif name.endswith(('.tar.zst', '.tar.zstd', '.tzs', '.tzst')):
            command = command_mod.Command('tzs', errors='stop')
        elif name.endswith(('.tar.bz2', '.tbz')):
            command = command_mod.Command('tbz', errors='stop')
        elif name.endswith(('.tar.g2', '.tgz')):
            command = command_mod.Command('tgz', errors='stop')
        elif path.suffix in ('.7z', '.tar', '.zip'):
            command = command_mod.Command(path.suffix[1:4], errors='stop')
        else:
            raise SystemExit(
                f"{sys.argv[0]}: Unable to make unsupported archive format:"
                f"{name}"
            )

        command.set_args([path] + options.get_files())
        subtask_mod.Exec(command.get_cmdline()).run()


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
