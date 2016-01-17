#!/usr/bin/env python3
"""
Set file access mode.
"""

import argparse
import glob
import os
import re
import signal
import sys

import syslib

if sys.version_info < (3, 2) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.2, < 4.0).')

# pylint: disable=no-self-use,too-few-public-methods


class Options(object):
    """
    Options class
    """

    def __init__(self, args):
        self._parse_args(args[1:])

        mode = self._args.mode
        if mode == 'r':
            self._xmod = int('500', 8)
            self._fmod = int('400', 8)
        elif mode == 'rg':
            self._xmod = int('550', 8)
            self._fmod = int('440', 8)
        elif mode == 'ra':
            self._xmod = int('555', 8)
            self._fmod = int('444', 8)
        elif mode == 'w':
            self._xmod = int('700', 8)
            self._fmod = int('600', 8)
        elif mode == 'wg':
            self._xmod = int('750', 8)
            self._fmod = int('640', 8)
        elif mode == 'wa':
            self._xmod = int('755', 8)
            self._fmod = int('644', 8)
        else:
            self._xmod = int('755', 8)
            self._fmod = int('644', 8)

    def get_files(self):
        """
        Return list of files.
        """
        return self._args.files

    def get_fmod(self):
        """
        Return file permission mode.
        """
        return self._fmod

    def get_recursive_flag(self):
        """
        Return recursive flag.
        """
        return self._args.recursiveFlag

    def get_xmod(self):
        """
        Return executable permission mode.
        """
        return self._xmod

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(description='Set file access mode.')

        parser.add_argument('-R', dest='recursiveFlag', action='store_true',
                            help='Set mod of directories recursively.')
        parser.add_argument('-r', dest='mode', action='store_const', const='r',
                            help='Set read-only permission for user.')
        parser.add_argument('-rg', dest='mode', action='store_const', const='rg',
                            help='Set read-only permission for user and group.')
        parser.add_argument('-ra', dest='mode', action='store_const', const='ra',
                            help='Set read-only permission for everyone.')
        parser.add_argument('-w', dest='mode', action='store_const', const='w',
                            help='Set read-write permission for user.')
        parser.add_argument('-wg', dest='mode', action='store_const', const='wg',
                            help='Set read-write permission for user and read for group.')
        parser.add_argument('-wa', dest='mode', action='store_const', const='wa',
                            help='Set read-write permission for user and read for others.')

        parser.add_argument('files', nargs='+', metavar='file', help='File or directory.')

        self._args = parser.parse_args(args)


class Setmod(object):
    """
    Set mod class
    """

    def __init__(self, options):
        #   127 ELF,      202 254 186 190      207 250 237 254      206 250 237 254
        #  linux/sunos   macos-x86/x86_64       macos-x86_64           macos-x86
        self._exe_magics = (
            b'\177ELF', b'\312\376\272\276', b'\317\372\355\376', b'\316\372\355\376')
        self._is_exe_ext = re.compile(
            '[.](bat|cmd|com|dll|exe|ms[ip]|psd|s[olh]|s[ol][.].*|tcl)$', re.IGNORECASE)
        self._is_not_exe_ext = re.compile(
            '[.](7z|[acfo]|ace|asr|avi|bak|blacklist|bmp|bz2|cpp|crt|css|dat|deb|diz|doc|'
            'docx|f77|f90|gif|gz|h|hlp|htm|html|ico|ini|installed|ism|iso|jar|java|jpg|'
            'jpeg|js|json|key|lic|lib|list|log|mov|mp[34g]|mpeg|obj|od[fgst]|ogg|opt|pdf|'
            'png|ppt|pptx|rar|reg|rpm|swf|tar|txt|url|wsdl|xhtml|xls|xlsx|xml|xs[dl]|'
            'xvid|zip)$', re.IGNORECASE)
        self._setmod(options, options.get_files())

    def _setmod(self, options, files):
        fmod = options.get_fmod()
        xmod = options.get_xmod()
        recursiveFlag = options.get_recursive_flag()

        for file in sorted(files):
            if not os.path.islink(file):
                if os.path.isdir(file):
                    try:
                        os.chmod(file, xmod)
                    except OSError:
                        print('Permission denied:', file + os.sep)
                    if recursiveFlag:
                        try:
                            self._setmod(options, [os.path.join(file, x) for x in os.listdir(file)])
                        except PermissionError:
                            pass
                elif os.path.isfile(file):
                    try:
                        try:
                            with open(file, 'rb') as ifile:
                                magic = ifile.read(4)
                        except IOError:
                            os.chmod(file, fmod)
                            with open(file, 'rb') as ifile:
                                magic = ifile.read(4)
                        if magic.startswith(b'#!') or magic in self._exe_magics:
                            os.chmod(file, xmod)
                        elif self._is_exe_ext.search(file):
                            os.chmod(file, xmod)
                        elif self._is_not_exe_ext.search(file):
                            os.chmod(file, fmod)
                        elif os.access(file, os.X_OK):
                            os.chmod(file, xmod)
                        else:
                            os.chmod(file, fmod)
                    except OSError:
                        print('Permission denied:', file)
                else:
                    raise SystemExit(sys.argv[0] + ': Cannot find "' + file + '" file.')


class Main(object):
    """
    Main class
    """

    def __init__(self):
        self._signals()
        if os.name == 'nt':
            self._windows_argv()
        try:
            options = Options(sys.argv)
            Setmod(options)
        except (EOFError, KeyboardInterrupt):
            sys.exit(114)
        except (syslib.SyslibError, SystemExit) as exception:
            sys.exit(exception)
        sys.exit(0)

    def _signals(self):
        if hasattr(signal, 'SIGPIPE'):
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    def _windows_argv(self):
        argv = []
        for arg in sys.argv:
            files = glob.glob(arg)  # Fixes Windows globbing bug
            if files:
                argv.extend(files)
            else:
                argv.append(arg)
        sys.argv = argv


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
