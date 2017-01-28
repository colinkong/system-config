#!/usr/bin/env python3
"""
Wait for task to finish then launch command.
"""

import argparse
import glob
import os
import signal
import sys
import time

import command_mod
import subtask_mod
import task_mod

if sys.version_info < (3, 2) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.2, < 4.0).')


class Options(object):
    """
    Options class
    """

    def __init__(self):
        self._args = None
        self.parse(sys.argv)

    def get_command(self):
        """
        Return command Command class object.
        """
        return self._command

    def get_pid(self):
        """
        Return process ID.
        """
        return self._pid

    def get_pname(self):
        """
        Return process command name.
        """
        return self._pname

    def get_user(self):
        """
        Return user name.
        """
        return self._args.user

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(
            description='Wait for task to finish then launch command.')

        parser.add_argument(
            '-a',
            dest='user',
            action='store_const',
            const='<all>',
            default='',
            help='Monitor any user"s process.'
        )
        parser.add_argument(
            'task',
            nargs=1,
            metavar='pid|pname',
            help='Process ID or name.'
        )
        parser.add_argument(
            'command',
            nargs=1,
            help='Command name.'
        )
        parser.add_argument(
            'commandArgs',
            nargs='*',
            metavar='arg',
            help='Command arguments.'
        )

        self._args = parser.parse_args(args[:2])

    def parse(self, args):
        """
        Parse arguments
        """
        self._parse_args(args[1:])

        self._pid = 0
        self._pname = ''
        try:
            self._pid = int(self._args.task[0])
        except ValueError:
            self._pname = self._args.task[0]

        self._command = command_mod.Command(
            self._args.command[0],
            args=args[3:],
            errors='stop'
        )


class Main(object):
    """
    Main class
    """

    def __init__(self):
        try:
            self.config()
            sys.exit(self.run())
        except (EOFError, KeyboardInterrupt):
            sys.exit(114)
        except SystemExit as exception:
            sys.exit(exception)

    @staticmethod
    def config():
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

    @staticmethod
    def run():
        """
        Start program
        """
        options = Options()

        user = options.get_user()
        pname = options.get_pname()

        if pname:
            while task_mod.Tasks.factory(user).haspname(pname):
                time.sleep(1)
        else:
            pid = options.get_pid()
            while pid in task_mod.Tasks.factory(user).get_pids():
                time.sleep(1)
        subtask_mod.Exec(options.get_command().get_cmdline()).run()


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
