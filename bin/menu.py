#!/usr/bin/env python3
"""
Menu for launching software
"""

import argparse
import glob
import os
import signal
import sys
from pathlib import Path
from typing import List

import jinja2  # type: ignore

import command_mod
import config_mod
import file_mod
import subtask_mod


class Options:
    """
    Options class
    """

    def __init__(self) -> None:
        self._args: argparse.Namespace = None
        self.parse(sys.argv)

    def get_view_flag(self) -> bool:
        """
        Return view flag.
        """
        return self._args.view_flag

    def get_menus(self) -> List[str]:
        """
        Return menu names.
        """
        return self._args.menus

    def _parse_args(self, args: List[str]) -> None:
        parser = argparse.ArgumentParser(
            description="Menu for launching software",
        )

        parser.add_argument(
            '-v',
            dest='view_flag',
            action='store_true',
            help="Show TCL file.",
        )
        parser.add_argument(
            'menus',
            nargs='*',
            metavar='menu',
            default=['main'],
            help="Menu name.",
        )

        self._args = parser.parse_args(args)

    def parse(self, args: List[str]) -> None:
        """
        Parse arguments
        """
        self._parse_args(args[1:])


class Menu:
    """
    Menu class
    """

    def __init__(self, options: Options) -> None:
        self._view_flag = options.get_view_flag()
        self._menus = options.get_menus()

        template = f"{sys.argv[0].rsplit('.py', 1)[0]}.tcl.jinja2"
        with open(template, encoding='utf-8', errors='replace') as ifile:
            self._template = jinja2.Template(ifile.read())

        self._config_file = Path(sys.argv[0]).with_suffix('.yaml')
        self._status_file = Path(
            Path.home(),
            '.config',
            Path(sys.argv[0]).with_suffix('.json').name,
        )
        if self._status_file.is_file():
            file = self._status_file
        else:
            file = self._config_file

        data = config_mod.Data()
        data.read(file)
        self._config = next(data.get())

    @staticmethod
    def check_software(checks: List[str]) -> bool:
        """
        Return True if software found.
        """
        if not checks:
            return True

        for check in checks:
            if Path(check).is_file():
                return True
            for directory in os.environ.get('PATH', '').split(os.pathsep):
                if Path(directory).parent.glob('*/*/{check}'):
                    return True
        return False

    def generate(self, menu: str) -> List[str]:
        """
        Render template and return lines.
        """
        items = self._config.get(f'menu_{menu}')
        if not items:
            raise SystemExit(
                f"{sys.argv[0]}: Cannot find in menu.yaml: {menu}",
            )

        config: dict = {'buttons': []}
        config['title'] = menu
        for item in items:
            if self.check_software(item.get('checks')):
                config['buttons'].append(item['button'])

        lines = self._template.render(config).split('\n')

        return lines

    def open(self) -> None:
        """
        Open menus
        """
        wish = command_mod.Command('wish', errors='stop')
        tmpdir = file_mod.FileUtil.tmpdir(Path('.cache', 'menu'))

        for menu in self._menus:
            path = Path(tmpdir, f'{menu}.tcl')
            try:
                with path.open('w', encoding='utf-8', newline='\n') as ofile:
                    for line in self.generate(menu):
                        if self._view_flag:
                            print(line)
                        print(line, file=ofile)
            except OSError as exception:
                raise SystemExit(
                    f'{sys.argv[0]}: Cannot create "{path}" file.',
                ) from exception

            subtask_mod.Background(wish.get_cmdline() + [path]).run()

        if self._menus == ['main']:
            self.update(self._config_file, self._status_file)

    @classmethod
    def update(cls, config_file: Path, status_file: Path) -> None:
        """
        Update status file
        """
        data = config_mod.Data()
        data.read(config_file)
        config = next(data.get())

        for menu in [x for x in config if x.startswith('menu')]:
            found = []
            for item in config[menu]:
                check = item.get('check')
                if check:
                    if not cls.check_software(check):
                        continue
                    del item['check']
                found.append(item)
            config[menu] = found

        if status_file.is_file():
            data.read(status_file)
            status = next(data.get())
            if config == status:
                return
            print("Updating status file:", status_file)
        else:
            print("Writing status file:", status_file)

        data.set([config])
        data.write(status_file, compact=True)


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

        Menu(options).open()

        return 0


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
