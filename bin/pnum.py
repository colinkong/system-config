#!/usr/bin/env python3
"""
Renumber picture/video files into a numerical series.
"""

import argparse
import glob
import os
import signal
import sys
from pathlib import Path
from typing import List

import config_mod
import file_mod


class Options:
    """
    Options class
    """

    def __init__(self) -> None:
        self._args: argparse.Namespace = None
        self.parse(sys.argv)

    def get_directories(self) -> List[str]:
        """
        Return list of directories.
        """
        return self._args.directories

    def get_order(self) -> str:
        """
        Return order method.
        """
        return self._args.order

    def get_reset_flag(self) -> bool:
        """
        Return per directory number reset flag
        """
        return self._args.reset_flag

    def get_start(self) -> int:
        """
        Return start number.
        """
        return self._args.start[0]

    def _parse_args(self, args: List[str]) -> None:
        parser = argparse.ArgumentParser(
            description="Renumber picture files into a numerical series.",
        )

        parser.add_argument(
            '-time',
            action='store_const',
            const='time',
            dest='order',
            default='file',
            help="Sort using modification time.",
        )
        parser.add_argument(
            '-noreset',
            dest='reset_flag',
            action='store_false',
            help="Use same number sequence for all directories.",
        )
        parser.add_argument(
            '-start',
            nargs=1,
            type=int,
            default=[1],
            help="Select number to start from.",
        )
        parser.add_argument(
            'directories',
            nargs='+',
            metavar='directory',
            help="Directory containing picture/video files.",
        )

        self._args = parser.parse_args(args)

    def parse(self, args: List[str]) -> None:
        """
        Parse arguments
        """
        self._parse_args(args[1:])

        for path in [Path(x) for x in self._args.directories]:
            if not path.is_dir():
                raise SystemExit(
                    f'{sys.argv[0]}: Picture directory '
                    f'"{path}" does not exist.',
                )


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
    def _sorted(
        options: Options,
        file_stats: List[file_mod.FileStat],
    ) -> List[file_mod.FileStat]:
        order = options.get_order()
        if order == 'time':
            file_stats = sorted(
                file_stats,
                key=lambda s: (s.get_time(), s.get_file())
            )
        else:
            file_stats = sorted(file_stats, key=lambda s: s.get_file())
        return file_stats

    def run(self) -> int:
        """
        Start program
        """
        options = Options()

        startdir = os.getcwd()
        reset_flag = options.get_reset_flag()
        number = options.get_start()
        config = config_mod.Config()
        images_extensions = (
            config.get('image_extensions') + config.get('video_extensions')
        )

        for path in [Path(x) for x in options.get_directories()]:
            if reset_flag:
                number = options.get_start()
            if path.is_dir():
                os.chdir(path)
                file_stats = []
                for file in glob.glob('*.*'):
                    if Path(file).suffix.lower() in images_extensions:
                        file_stats.append(file_mod.FileStat(file))
                newfiles = []
                for file_stat in self._sorted(options, file_stats):
                    extension = Path(file_stat.get_file()).suffix
                    extension = extension.lower().replace('.jpeg', '.jpg')
                    newfile = f'pic{number:05d}{extension}'
                    newfiles.append(newfile)
                    try:
                        Path(file_stat.get_file()).replace(
                            f'pnum.tmp-{newfile}'
                        )
                    except OSError as exception:
                        raise SystemExit(
                            f'{sys.argv[0]}: Cannot rename '
                            f'"{file_stat.get_file()}" image file.',
                        ) from exception
                    number += 1
                for file in newfiles:
                    try:
                        Path(f'pnum.tmp-{file}').replace(file)
                    except OSError as exception:
                        raise SystemExit(
                            f'{sys.argv[0]}: Cannot rename to '
                            f'"{file}" image file.',
                        ) from exception
                os.chdir(startdir)

        return 0


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
