#!/usr/bin/env python3
"""
Open files using default application.
"""

import sys
if sys.version_info < (3, 0) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ": Requires Python version (>= 3.0, < 4.0).")
if __name__ == "__main__":
    sys.path = sys.path[1:] + sys.path[:1]

import argparse
import glob
import os
import signal

import syslib


class Options(syslib.Dump):


    def __init__(self, args):
        self._parseArgs(args[1:])


    def getFiles(self):
        """
        Return list of files.
        """
        return self._args.files


    def _parseArgs(self, args):
        parser = argparse.ArgumentParser(description="Open files using default application.")

        parser.add_argument("files", nargs=1, metavar="file", help="File to open.")

        self._args = parser.parse_args(args)


class Open(syslib.Dump):


    def __init__(self, options):
        self._files = options.getFiles()


    def run(self):
        for file in self._files:
            prefix = file.split(":", 1)[0]
            extension = file.rsplit(".", 1)[-1]

            if os.path.isdir(file):
                self._spawn("xdesktop", file)

            elif prefix in ( "http", "https", "ftp" ):
                self._spawn("firefox", file)

            elif not os.path.isfile(file):
                print(file + ": cannot find file.")

            elif extension in ( "mp3", "ogg", "wav" ):
                self._spawn("audacity", file)

            elif extension in ( "eps", "ps", "pdf" ):
                self._spawn("evince", file)

            elif extension in ( "htm", "html", "xhtml" ):
                self._spawn("firefox", file)

            elif extension in ( "jpg", "jpeg", "png" ):
                self._spawn("gimp", file)

            elif extension in ( "doc", "docx", "odf", "odg", "ods", "odt", "ppt",
                                "pptx", "xls", "xlsx" ):
                self._spawn("soffice", file)

            elif extension == "txt":
                self._spawn("xedit", file)

            else:
                print(file + ": unknown file extension.")


    def _spawn(self, program, file):
        print(file + ': opening with "' + program + '"...')
        program = syslib.Command(program, args=[ file ])
        program.run(mode="daemon")


class Main:


    def __init__(self):
        self._signals()
        if os.name == "nt":
            self._windowsArgv()
        try:
            options = Options(sys.argv)
            Open(options).run()
        except (EOFError, KeyboardInterrupt):
            sys.exit(114)
        except (syslib.SyslibError, SystemExit) as exception:
            sys.exit(exception)
        sys.exit(0)


    def _signals(self):
        if hasattr(signal, "SIGPIPE"):
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)


    def _windowsArgv(self):
        argv = []
        for arg in sys.argv:
            files = glob.glob(arg) # Fixes Windows globbing bug
            if files:
                argv.extend(files)
            else:
                argv.append(arg)
        sys.argv = argv


if __name__ == "__main__":
    if "--pydoc" in sys.argv:
        help(__name__)
    else:
        Main()
