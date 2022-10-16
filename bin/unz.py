#!/usr/bin/env python3
"""
Unpack a compressed archive using suitable tool.",
"""

import argparse
import glob
import os
import signal
import sys
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

    def get_archives(self) -> List[str]:
        """
        Return list of archive files.
        """
        return self._args.archives

    def _parse_args(self, args: List[str]) -> None:
        parser = argparse.ArgumentParser(
            description="Unpack a compressed archive using suitable tool.",
        )

        parser.add_argument(
            'archives',
            nargs='+',
            metavar='archive',
            help="Archive file.",
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
            sys.exit(exception)

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
                files = glob.glob(arg)  # Fixes Windows globbing bug
                if files:
                    argv.extend(files)
                else:
                    argv.append(arg)
            sys.argv = argv

    @classmethod
    def run(cls) -> int:
        """
        Start program
        """
        options = Options()
        os.umask(int('022', 8))

        for file in options.get_archives():
            name = os.path.basename(file)
            args = [file]
            if name.endswith('.ace'):
                command = command_mod.Command('unace', errors='stop')
            elif name.endswith('.deb'):
                command = command_mod.Command('undeb', errors='stop')
            elif name.endswith('.gpg'):
                command = command_mod.Command('ungpg', errors='stop')
            elif name.startswith('initrd'):
                command = command_mod.Command('unmkinitramfs', errors='stop')
                args = [file, '.']
            elif name.endswith('.pdf'):
                command = command_mod.Command('unpdf', errors='stop')
            elif name.endswith('.pyc'):
                command = command_mod.Command('unpyc', errors='stop')
            elif name.endswith('.sqlite'):
                command = command_mod.Command('unsqlite', errors='stop')
            elif name.endswith('.squashfs'):
                command = command_mod.Command('unsquashfs', errors='stop')
                args = ['-f', '-d', '.', file]
            elif name.endswith((
                '.tar',
                '.tar.gz',
                '.tar.bz2',
                '.tar.zst',
                '.tar.lzma',
                '.tar.xz',
                '.tar.zst',
                '.tar.lzma',
                '.tar.xz',
                '.tar.7z',
                '.tgz',
                '.tbz',
                '.tzs',
                '.tzst',
                '.tlz',
                '.txz',
                '.t7z',
            )):
                command = command_mod.Command('untar', errors='stop')
            else:
                command = command_mod.Command('un7z', errors='stop')
            cmdline = command.get_cmdline() + args
            print(f"\nRunning: {command.args2cmd(cmdline)}")
            task = subtask_mod.Task(cmdline)
            task.run()
            if task.get_exitcode():
                raise SystemExit(
                    f'{sys.argv[0]}: Error code {task.get_exitcode()} '
                    f'received from "{task.get_file()}".',
                )

        return 0


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()