#!/usr/bin/env python3
"""
Copy CD/DVD data as a portable ISO/BIN image file.
"""

import sys
if sys.version_info < (3, 2) or sys.version_info >= (4, 0):
    sys.exit(sys.argv[0] + ": Requires Python version (>= 3.2, < 4.0).")
if __name__ == "__main__":
    sys.path = sys.path[1:] + sys.path[:1]

import argparse
import glob
import hashlib
import os
import signal
import time

import syslib


class Options(syslib.Dump):

    def __init__(self, args):
        self._parseArgs(args[1:])

    def getDaoFlag(self):
        """
        Return dao flag
        """
        return self._args.daoFlag

    def getDevice(self):
        """
        Return device location.
        """
        return self._args.device[0]

    def getMd5Flag(self):
        """
        Return md5 flag.
        """
        return self._args.md5Flag

    def getImage(self):
        """
        Return ISO/BIN image location.
        """
        return self._image

    def getSpeed(self):
        """
        Return CD/DVD speed.
        """
        return self._args.speed[0]

    def _parseArgs(self, args):
        parser = argparse.ArgumentParser(
            description="Copy CD/DVD data as a portable ISO/BIN image file.")

        parser.add_argument("-dao", dest="daoFlag", action="store_true",
                            help="Read data/audio/video CD in disk-at-once mode.")
        parser.add_argument("-md5", dest="md5Flag", action="store_true",
                            help="Create MD5 check sum of CD/DVD.")
        parser.add_argument("-speed", nargs=1, type=int, default=[8],
                            help="Select CD/DVD spin speed.")

        parser.add_argument("device", nargs=1, metavar="device|scan",
                            help='CD/DVD device (ie "/dev/sr0" or "scan".')
        parser.add_argument("image", nargs="?", metavar="image.iso|image.bin",
                            help="ISO image file or BIN image filie for DAO mode.")

        self._args = parser.parse_args(args)

        if self._args.speed[0] < 1:
            raise SystemExit(sys.argv[0] + ": You must specific a positive integer for "
                             "CD/DVD device speed.")
        if self._args.device[0] != "scan" and not os.path.exists(self._args.device[0]):
            raise SystemExit(sys.argv[0] + ': Cannot find "' + self._args.device[0] +
                             '" CD/DVD device.')

        if self._args.image:
            self._image = self._args.image[0]
        elif self._args.daoFlag:
            self._image = "file.bin"
        else:
            self._image = "file.iso"


class Cdrom(syslib.Dump):

    def __init__(self):
        self._devices = {}
        for directory in glob.glob("/sys/block/sr*/device"):
            device = "/dev/" + os.path.basename(os.path.dirname(directory))
            model = ""
            for file in ("vendor", "model"):
                try:
                    with open(os.path.join(directory, file), errors="replace") as ifile:
                        model += " " + ifile.readline().strip()
                except IOError:
                    continue
            self._devices[device] = model

    def device(self, mount):
        if mount == "cdrom":
            rank = 0
        else:
            try:
                rank = int(mount[5:])-1
            except ValueError:
                return ""
        try:
            return sorted(self._devices.keys())[rank]
        except IndexError:
            return ""

    def getDevices(self):
        """
        Return list of devices
        """
        return self._devices


class Readcd(syslib.Dump):

    def __init__(self, options):
        device = options.getDevice()
        if device == "scan":
            self._scan()
        else:
            speed = options.getSpeed()
            file = options.getImage()

            self._cdspeed(device, speed)
            if os.path.isfile(file):
                try:
                    os.remove(file)
                except OSError:
                    raise SystemExit(sys.argv[0] + ': Cannot over write "' +
                                     file + '" CD/DVD image file.')
            if options.getDaoFlag():
                self._dao(device, speed, file)
            else:
                self._tao(device, file)
            if options.getMd5sumFlag():
                print("Creating MD5 check sum of ISO file.")
                md5sum = self._md5sum(options.getFile())
                if (not md5sum):
                    raise SystemExit(sys.argv[0] + ': Cannot read "' + file + '" file.')
                else:
                    print(md5sum, options.getFile(), sep="  ")
            time.sleep(1)
            eject = syslib.Command("eject", check=False)
            if eject.isFound():
                eject.run(mode="batch")
                if eject.getExitcode():
                    raise SystemExit(sys.argv[0] + ': Error code ' + str(eject.getExitcode()) +
                                     ' received from "' + eject.getFile() + '".')

    def _cdspeed(self, device, speed):
        cdspeed = syslib.Command("cdspeed", flags=[device], check=False)
        if cdspeed.isFound():
            if speed:
                cdspeed.setArgs([str(speed)])
            cdspeed.run()
        elif speed:
            hdparm = syslib.Command(file="/sbin/hdparm", args=["-E", str(speed), device])
            hdparm.run(mode="batch")

    def _dao(self, device, speed, file):
        cdrdao = syslib.Command("cdrdao", flags=["read-cd", "--device", device, "--read-raw"])
        nice = syslib.Command("nice", args=["-20"])
        if speed:
            cdrdao.extend(["--speed", speed])
        if file.endswith(".bin"):
            cdrdao.setArgs(["--datafile", file, file[:-4] + ".toc"])
        else:
            cdrdao.setArgs(["--datafile", file, file + ".toc"])
        cdrdao.setWrapper(nice)
        cdrdao.run()
        if cdrdao.getExitcode():
            raise SystemExit(sys.argv[0] + ': Error code ' + str(cdrdao.getExitcode()) +
                             ' received from "' + cdrdao.getFile() + '".')

    def _md5sum(self, file):
        try:
            with open(file, "rb") as ifile:
                md5 = hashlib.md5()
                while True:
                    chunk = ifile.read(131072)
                    if not chunk:
                        break
                    md5.update(chunk)
        except (IOError, TypeError):
            return ""
        return md5.hexdigest()

    def _scan(self):
        cdrom = Cdrom()
        print("Scanning for CD/DVD devices...")
        devices = cdrom.getDevices()
        for key, value in sorted(devices.items()):
            print("  {0:10s}  {1:s}".format(key, value))

    def _tao(self, device, file):
        isoinfo = syslib.Command("isoinfo")
        nice = syslib.Command("nice", args=["-20"])
        dd = syslib.Command("dd", args=["if=" + device, "bs=" + str(2048*4096),
                            "count=1", "of=" + file])
        dd.run(mode="batch")
        if dd.getError()[0].endswith("Permission denied"):
            raise SystemExit(sys.argv[0] + ": Cannot read from CD/DVD device. "
                                           "Please check permissions.")
        elif not os.path.isfile(file):
            raise SystemExit(sys.argv[0] + ": Cannot find CD/DVD media. Please check drive.")
        elif dd.getExitcode():
            raise SystemExit(sys.argv[0] + ': Error code ' + str(dd.getExitcode()) +
                                           ' received from "' + dd.getFile() + '".')

        isoinfo.setArgs(["-d", "-i", file])
        isoinfo.run(filter="^Volume size is: ", mode="batch")
        if not isoinfo.hasOutput():
            raise SystemExit(sys.argv[0] + ": Cannot find TOC on CD/DVD media. "
                                           "Disk not recognised.")
        elif isoinfo.getExitcode():
            raise SystemExit(sys.argv[0] + ': Error code ' + str(isoinfo.getExitcode()) +
                                           ' received from "' + isoinfo.getFile() + '".')
        blocks = int(isoinfo.getOutput()[0].split()[-1])
        isoinfo.run(filter=" id: $")
        if isoinfo.getExitcode():
            raise SystemExit(sys.argv[0] + ': Error code ' + str(isoinfo.getExitcode()) +
                                           ' received from "' + isoinfo.getFile() + '".')

        print('Creating ISO image file "' + file + '"...')
        dd.setArgs(["if=" + device, "bs=2048", "count=" + str(blocks), "of=" + file])
        dd.setWrapper(nice)
        dd.run(filter="Input/output error| records (in|out)$")
        if not os.path.isfile(file):
            raise SystemExit(sys.argv[0] + ": Cannot find CD/DVD media. Please check drive.")
        pad = int(blocks * 2048 - syslib.FileStat(file).getSize())
        if pad > 0 and pad < 16777216:
            print(pad, "bytes flushing from CD/DVD prefetch bug...")
            with open(file, "ab") as ofile:
                ofile.write(b"\0" * pad)
        self._isosize(file, syslib.FileStat(file).getSize())

    def _isosize(self, image, size):
        if size > 734003200:
            print("\n*** {0:s}: {1:4.2f} MB ({2:5.3f} salesman's GB) ***\n".format(
                  image, size/1048576, size/1000000000))
            if size > 9400000000:
                sys.stderr.write("**WARNING** This ISO image file does not fit onto "
                                 "9.4GB/240min Duel Layer DVD media.\n")
                sys.stderr.write("        ==> Please split your data into multiple images.\n")
            elif size > 4700000000:
                sys.stderr.write("**WARNING** This ISO image file does not fit onto "
                                 "4.7GB/120min DVD media.\n")
                sys.stderr.write("        ==> Please use Duel Layer DVD media or split "
                                 "your data into multiple images.\n")
            else:
                sys.stderr.write("**WARNING** This ISO image file does not fit onto "
                                 "700MB/80min CD media.\n")
                sys.stderr.write("        ==> Please use DVD media or split your data "
                                 "into multiple images.\n")
            print()
        else:
            minutes, remainder = divmod(size, 734003200 / 80)
            seconds = remainder * 4800 / 734003200.
            print("\n*** {0:s}: {1:4.2f} MB ({2:.0f} min {3:05.2f} sec) ***\n".format(
                  image, size/1048576, minutes, seconds))
            if size > 681574400:
                sys.stderr.write("**WARNING** This ISO image file does not fit onto "
                                 "650MB/74min CD media.\n")
                sys.stderr.write("        ==> Please use 700MB/80min CD media instead.\n")


class Main:

    def __init__(self):
        self._signals()
        if os.name == "nt":
            self._windowsArgv()
        try:
            options = Options(sys.argv)
            Readcd(options)
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
            files = glob.glob(arg)  # Fixes Windows globbing bug
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
