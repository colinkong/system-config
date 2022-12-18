#!/usr/bin/env python3
"""
Re-format JSON file.
"""

import argparse
import glob
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

    def get_files(self) -> List[str]:
        """
        Return list of files.
        """
        return self._args.files

    def _parse_args(self, args: List[str]) -> None:
        parser = argparse.ArgumentParser(description="re-format JSON file.")

        parser.add_argument(
            'files',
            nargs='+',
            metavar='file',
            help="File to change.",
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
        options = Options()

        for path in [Path(x) for x in options.get_files()]:
            if not path.is_file():
                raise SystemExit(f'{sys.argv[0]}: Cannot find "{path}" file.')
            print(f'Re-formatting "{path}" JSON file...')

            lines = []
            try:
                with path.open(encoding='utf-8', errors='replace') as ifile:
                    for line in ifile:
                        lines.append(line.strip())
            except OSError as exception:
                raise SystemExit(
                    f'{sys.argv[0]}: Cannot read "{path}" file.',
                ) from exception

            command = command_mod.Command(
                'json_reformat',
                args=['-s'],
                errors='stop'
            )
            task = subtask_mod.Batch(command.get_cmdline())
            task.run(stdin=lines)
            if task.has_error():
                for line in task.get_error():
                    print(line, file=sys.stderr)
                raise SystemExit(task.get_exitcode())

            path_new = Path(f'{path}.part')
            try:
                with path_new.open(
                    'w',
                    encoding='utf-8',
                    newline='\n',
                ) as ofile:
                    for line in task.get_output():
                        print(line, file=ofile)
            except OSError as exception:
                raise SystemExit(
                    f'{sys.argv[0]}: Cannot create "{path_new}" file.',
                ) from exception
            try:
                path_new.replace(path)
            except OSError as exception:
                raise SystemExit(
                    f'{sys.argv[0]}: Cannot rename '
                    f'"{path_new}" file to "{path}".',
                ) from exception

        return 0


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
