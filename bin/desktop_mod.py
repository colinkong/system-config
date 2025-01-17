#!/usr/bin/env python3
"""
Python graphical desktop module

Copyright GPL v2: 2013-2024 By Dr Colin Kong
"""

import functools
import getpass
import os
import subprocess
import sys
from pathlib import Path
from typing import List

RELEASE = '2.8.1'
VERSION = 20241026


class _System:

    @staticmethod
    def is_windows() -> bool:
        """
        Return True if running on Windows.
        """
        if os.name == 'posix':
            if os.uname()[0].startswith('cygwin'):
                return True
        elif os.name == 'nt':
            return True

        return False

    @staticmethod
    def _locate_program(program: str) -> str:
        for path in [
            Path(x, program)
            for x in os.environ['PATH'].split(os.pathsep)
        ]:
            if path.is_file():
                break
        else:
            return None
        return str(path)

    @classmethod
    def run_program(cls, command: List[str]) -> List[str]:
        """
        Run program in batch mode and return list of lines.
        """
        program = cls._locate_program(command[0])
        lines: List[str] = []
        if not program:
            return lines

        try:
            with subprocess.Popen(
                [program] + command[1:],
                shell=False,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            ) as child:
                while True:
                    try:
                        bline = child.stdout.readline()
                    except (KeyboardInterrupt, OSError):
                        break
                    if not bline:
                        break
                    line = bline.decode(errors='replace')
                    lines.append(line.rstrip('\n'))
        except OSError:
            return []

        return lines


class Desktop:
    """
    Desktop class
    """

    @staticmethod
    def has_xfce() -> bool:
        """
        Return true if running XFCE desktop
        """
        if 'DISPLAY' in os.environ:
            if os.environ.get('XDG_CURRENT_DESKTOP') == 'XFCE':
                return True
            if os.environ.get('XDG_MENU_PREFIX', '').startswith('xfce-'):
                return True
            if os.environ.get('DESKTOP_SESSION') == 'xfce':
                return True
        return False

    @staticmethod
    def has_gnome() -> bool:
        """
        Return true if running Gnome desktop
        """
        if 'DISPLAY' in os.environ:
            if os.environ.get('XDG_CURRENT_DESKTOP') == 'GNOME':
                return True
            if os.environ.get('XDG_MENU_PREFIX', '').startswith('gnome-'):
                return True
            if os.environ.get('XDG_SESSION_DESKTOP', '').startswith('gnome'):
                return True
            if os.environ.get('DESKTOP_SESSION', '') == 'gnome':
                return True
        return False

    @staticmethod
    def has_kde() -> bool:
        """
        Return true if running KDE desktop
        """
        if 'DISPLAY' in os.environ:
            if os.environ.get('XDG_CURRENT_DESKTOP') == 'KDE':
                return True
            if os.environ.get('XDG_SESSION_DESKTOP', '').startswith('KDE'):
                return True
            if os.environ.get('DESKTOP_SESSION', '') in ('kde', 'plasma'):
                return True
        return False

    @staticmethod
    def has_cinnamon() -> bool:
        """
        Return true if running Cinnamon desktop
        """
        if 'DISPLAY' in os.environ:
            if os.environ.get('XDG_CURRENT_DESKTOP') == 'X-Cinnamon':
                return True
            if os.environ.get('CINNAMON_VERSION', ''):
                return True
        return False

    @staticmethod
    def has_mate() -> bool:
        """
        Return true if running Mate desktop
        """
        if 'DISPLAY' in os.environ:
            if os.environ.get('XDG_CURRENT_DESKTOP') == 'MATE':
                return True
        return False

    @staticmethod
    def has_macos() -> bool:
        """
        Return true if running MacOS desktop
        """
        if os.name == 'posix' and os.uname()[0] == 'Darwin':
            return True
        return False

    @staticmethod
    def guess_running() -> str:
        """
        Guess desktop based on session user is running. Return name or Unknown.
        """
        if 'DISPLAY' in os.environ:
            command = ['ps', '-o', 'args', '-u', getpass.getuser()]
            lines = _System.run_program(command)
            names = set(Path(line.split()[0]).name for line in lines)

            if 'xfce4-session' in names:
                return 'xfce'
            if (set(
                ['gnome-panel', 'gnome-session', 'gnome-session-binary']
            ) & names):
                return 'gnome'
            if 'startkde' in names:
                return 'kde'

        return 'Unknown'

    @staticmethod
    def guess_installed() -> str:
        """
        Guess desktop based on what is installed. Return name or Unknown.
        """
        if 'DISPLAY' in os.environ:
            desktops = [
                ('cinnamon', 'cinnamon'),
                ('gnome-panel', 'gnome'),
                ('gnome-session', 'gnome'),
                ('gnome-session-binary', 'gnome'),
                ('marco', 'mate'),
                ('startkde', 'kde'),
                ('xfce4-session', 'xfce'),
            ]
            for program, name in desktops:
                for directory in os.environ['PATH'].split(os.pathsep):
                    path = Path(directory, program)
                    if path.is_file():
                        return name

        return 'Unknown'

    @classmethod
    @functools.lru_cache(maxsize=1)
    def detect(cls) -> str:
        """
        Return desktop name or Unknown)
        """
        name = 'Unknown'
        if cls.has_xfce():
            name = 'xfce'
        elif cls.has_gnome():
            name = 'gnome'
        elif cls.has_kde():
            name = 'kde'
        elif cls.has_cinnamon():
            name = 'cinnamon'
        elif cls.has_mate():
            name = 'mate'
        elif cls.has_macos():
            name = 'macos'
        elif not _System.is_windows():
            name = cls.guess_running()
            if name == 'Unknown':
                name = cls.guess_installed()

        return name


if __name__ == '__main__':
    if sys.argv[-1] in ('-v', '-V', '-version', '--version'):
        print(f"Python graphical desktop module {RELEASE} ({VERSION})")
    else:
        help(__name__)
