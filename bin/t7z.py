#!/usr/bin/env python3
"""
Make a compressed archive in TAR.7Z format.
"""

import argparse
import glob
import os
import shutil
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
        return self._archive

    def get_files(self) -> List[str]:
        """
        Return list of files.
        """
        return self._files

    def _parse_args(self, args: List[str]) -> None:
        parser = argparse.ArgumentParser(
            description="Make a compressed archive in TAR format.",
        )

        parser.add_argument(
            'archive',
            nargs=1,
            metavar='file.tar.7z|file.t7z',
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

        if Path(self._args.archive[0]).is_dir():
            self._archive = f'{Path(self._args.archive[0]).resolve()}.tar.7z'
        else:
            self._archive = self._args.archive[0]
        if '.tar.7z' not in self._archive and '.t7z' not in self._archive:
            raise SystemExit(
                f'{sys.argv[0]}: Unsupported "{self._archive}" archive format.'
            )

        if self._args.files:
            self._files = self._args.files
        else:
            self._files = os.listdir()


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
        archive = options.get_archive()
        os.umask(0o022)

        tar = command_mod.Command('tar', errors='stop')
        tar.set_args(['cf', '-'] + options.get_files())
        tar.extend_args(['--owner=0:0', '--group=0:0', '--sort=name'])
        task: subtask_mod.Task = subtask_mod.Batch(
            tar.get_cmdline() + ['--help'],
        )
        task.run(pattern='--xattrs')
        if task.has_output():
            tar.extend_args(['--xattrs', '--xattrs-include=*'])

        unpacker = command_mod.Command('7z', errors='stop')
        unpacker.set_args([
            'a',
            '-m0=lzma2',
            '-mmt=2',
            '-mx=9',
            '-myx=9',
            '-md=128m',
            '-mfb=256',
            '-ms=on',
            '-si',
            '-y',
            archive+'.part'
        ])
        task = subtask_mod.Task(
            tar.get_cmdline() + ['|'] + unpacker.get_cmdline()
        )

        task.run()
        try:
            if task.get_exitcode():
                raise OSError
            shutil.move(archive+'.part', archive)
        except OSError as exception:
            raise SystemExit(
                f'{sys.argv[0]}: Cannot create "{archive}" archive file.',
            ) from exception

        return 0


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
