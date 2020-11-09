#!/usr/bin/env python3
"""
Wrapper for "helm" command

"""

import getpass
import glob
import os
import shutil
import signal
import sys

import command_mod
import subtask_mod


class Main:
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
    def _cache():
        tmpdir = os.path.join('/tmp', getpass.getuser())
        for cache in ('cache', 'repository/cache'):
            directory = os.path.join(tmpdir, '.cache', 'helm', cache)
            try:
                os.makedirs(directory)
            except FileExistsError:
                pass
        os.chmod(tmpdir, int('700', 8))

        helm_directory = os.path.join(os.environ['HOME'], '.helm')
        if not os.path.isdir(os.path.join(helm_directory, 'repository')):
            try:
                os.makedirs(os.path.join(helm_directory, 'repository'))
            except OSError:
                return

        for cache in ('cache', 'repository/cache'):
            link = os.path.join(helm_directory, cache)
            if not os.path.islink(link):
                cache_directory = os.path.join(tmpdir, '.cache', 'helm', cache)
                try:
                    if not os.path.isdir(cache_directory):
                        os.makedirs(cache_directory)
                    if os.path.exists(link):
                        shutil.rmtree(link)
                    os.symlink(cache_directory, link)
                except OSError:
                    pass

    @classmethod
    def run(cls):
        """
        Start program
        """
        cls._cache()

        helm = command_mod.Command('helm', errors='stop')
        helm.set_args(sys.argv[1:])
        subtask_mod.Exec(helm.get_cmdline()).run()


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
