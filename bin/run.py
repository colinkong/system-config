#!/usr/bin/env python3
"""
Run a command immune to terminal hangups.
"""

import argparse
import glob
import os
import signal
import sys

import syslib

if sys.version_info < (3, 3) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.3, < 4.0).')


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

    def get_log_file(self):
        """
        Return log file.
        """
        return self._args.log_file

    @staticmethod
    def _sh(command):
        try:
            with open(command.get_file(), errors='replace') as ifile:
                line = ifile.readline().rstrip('\r\n')
                if line == '#!/bin/sh':
                    shell = syslib.Command(file='/bin/sh')
                    command.set_wrapper(shell)
        except OSError:
            pass

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(description='Run a command immune to terminal hangups.')

        parser.add_argument('-q', action='store_const', const='', dest='log_file',
                            default='run.out', help="Do not create 'run.out' output file.")

        parser.add_argument('command', nargs=1, help='Command to run.')
        parser.add_argument('args', nargs='*', metavar='arg', help='Command argument.')

        my_args = []
        for arg in args:
            my_args.append(arg)
            if not arg.startswith('-'):
                break

        self._args = parser.parse_args(my_args)

        return args[len(my_args):]

    def parse(self, args):
        """
        Parse arguments
        """
        command_args = self._parse_args(args[1:])

        command = self._args.command[0]
        if os.path.isfile(command):
            self._command = syslib.Command(file=os.path.abspath(command), args=command_args)
        else:
            file = os.path.join(os.path.dirname(args[0]), command)
            if os.path.isfile(file):
                self._command = syslib.Command(file=file, args=command_args)
            else:
                self._command = syslib.Command(command, args=command_args)

        self._sh(self._command)

        if self._args.log_file:
            try:
                with open(self._args.log_file, 'wb'):
                    pass
            except OSError:
                raise SystemExit(
                    sys.argv[0] + ': Cannot create "' + self._args.log_file + '" logfile file.')


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

        options.get_command().run(logfile=options.get_log_file(), mode='daemon')


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
