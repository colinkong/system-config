#!/usr/bin/env python3
"""
Generate 'index.xhtml' & 'index.fsum' files plus '.../fsum' cache files
"""

import glob
import logging
import os
import re
import shutil
import signal
import sys
from pathlib import Path
from typing import List

import command_mod
import file_mod
import logging_mod
import subtask_mod

logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging_mod.ColoredFormatter())
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)


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

    @classmethod
    def _checksum(cls) -> None:
        fsum = command_mod.Command('fsum', errors='stop')
        files = glob.glob('*')
        if 'index.fsum' in files:
            files.remove('index.fsum')
            fsum.set_args(['-R', '-update=index.fsum'] + files)
        else:
            fsum.set_args(['-R'] + files)
        task = subtask_mod.Batch(fsum.get_cmdline())

        task.run()
        cls._write_fsums(task.get_output())

        task.run()
        time_new = 0
        try:
            lines = []
            path = Path('index.fsum')
            if path.is_file():
                with path.open(
                    encoding='utf-8',
                    errors='replace',
                ) as ifile:
                    for line in ifile:
                        lines.append(line.rstrip('\r\n'))
                if lines == task.get_output():
                    return

            logger.info("Writing checksums: index.fsum")

            path_new = Path('index.fsum.part')
            with path_new.open(
                'w',
                encoding='utf-8',
                newline='\n',
            ) as ofile:
                for line in task.get_output():
                    time_new = max(
                        time_new,
                        int(line.split(' ', 1)[0].rsplit('/', 1)[-1])
                    )
                    print(line, file=ofile)
            os.utime('index.fsum.part', (time_new, time_new))
            path_new.replace(path)
        except OSError as exception:
            raise SystemExit(
                f'{sys.argv[0]}: Cannot create "index.fsum" file.',
            ) from exception

    @staticmethod
    def _checkfile(
        directory: str = os.curdir,
    ) -> None:
        """
        Look for bad files like core dumps
        (don't followlinks & onerror do nothing)
        """
        isbadfile = re.compile(r'^core([.]\d+)?$')

        error = False
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = Path(root, file).resolve()
                if isbadfile.search(file):
                    print("Error: Found bad file:", file_path)
                    error = True
                try:
                    if Path(file_path).stat().st_size == 0:
                        print("Error: Found zero size file:", file_path)
                        error = True
                except OSError:
                    print("Error: Found broken link:", file_path)
                    error = True
        if error:
            raise SystemExit(1)

    @staticmethod
    def _create_directory(path: Path) -> None:
        if not path.is_dir():
            try:
                path.mkdir()
            except OSError as exception:
                raise SystemExit(
                    f'{sys.argv[0]}: Cannot create "{path}" directory.',
                ) from exception

    @classmethod
    def _set_time(cls, directory_path: Path) -> None:
        """
        Fix directory and symbolic link modified times.
        """
        paths = list(directory_path.iterdir())
        for path in paths:
            if path.is_symlink():
                link_stat = file_mod.FileStat(path, follow_symlinks=False)
                file_stat = file_mod.FileStat(path)
                file_time = file_stat.get_time()
                if file_time != link_stat.get_time():
                    try:
                        os.utime(
                            path,
                            (file_time, file_time),
                            follow_symlinks=False,
                        )
                    except NotImplementedError:
                        pass
            elif path.is_dir():
                cls._set_time(path)

        if paths:
            newest = file_mod.FileUtil.newest([str(x) for x in paths])
            file_stat = file_mod.FileStat(newest)
            file_time = file_stat.get_time()
            if file_time != file_mod.FileStat(directory_path).get_time():
                os.utime(directory_path, (file_time, file_time))

    @classmethod
    def _write_fsums(cls, lines: List[str]) -> None:
        fsums: dict = {}
        for line in lines:
            checksum, file = line.split('  ', 1)
            path = Path(file).parent
            if path.name == '...':
                path = path.parent
                file = Path(file).name
                if file == 'fsum':
                    continue
            else:
                file = f'../{Path(file).name}'
            if path not in fsums:
                fsums[path] = []
            fsums[path].append(f'{checksum}  {file}')

        for directory in sorted(fsums):
            directory_path = Path(directory, '...')
            cls._create_directory(directory_path)
            path = Path(directory_path, 'fsum')

            time_new = 0
            try:
                lines = []
                if path.is_file():
                    with path.open(
                        encoding='utf-8',
                        errors='replace',
                    ) as ifile:
                        for line in ifile:
                            lines.append(line.rstrip('\r\n'))
                    if lines == fsums[directory]:
                        continue

                logger.info("Writing checksums: %s", path)
                path_new = Path(f'{path}.part')
                with path_new.open(
                    'w',
                    encoding='utf-8',
                    newline='\n',
                ) as ofile:
                    for line in fsums[directory]:
                        time_new = max(
                            time_new,
                            int(line.split(' ', 1)[0].rsplit('/', 1)[-1])
                        )
                        print(line, file=ofile)
                os.utime(path_new, (time_new, time_new))
                shutil.move(path_new, path)
            except OSError as exception:
                raise SystemExit(
                    f'{sys.argv[0]}: Cannot create "{file}" file.',
                ) from exception

    @classmethod
    def run(cls) -> int:
        """
        Start program
        """
        cls._checkfile()
        cls._checksum()
        cls._set_time(Path.cwd())

        return 0


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
