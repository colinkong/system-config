#!/usr/bin/env python3
"""
Copy CD/DVD data as a portable ISO/BIN image file.
"""

import argparse
import glob
import hashlib
import os
import signal
import sys
import time

import command_mod
import file_mod
import subtask_mod

if sys.version_info < (3, 3) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.3, < 4.0).')


class Options(object):
    """
    Options class
    """

    def __init__(self):
        self._args = None
        self.parse(sys.argv)

    def get_disk_at_once_flag(self):
        """
        Return dao flag
        """
        return self._args.dao_flag

    def get_device(self):
        """
        Return device location.
        """
        return self._args.device[0]

    def get_md5_flag(self):
        """
        Return md5 flag.
        """
        return self._args.md5_flag

    def get_image(self):
        """
        Return ISO/BIN image location.
        """
        return self._image

    def get_speed(self):
        """
        Return CD/DVD speed.
        """
        return self._args.speed[0]

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(
            description='Copy CD/DVD data as a portable ISO/BIN image file.')

        parser.add_argument(
            '-dao',
            dest='dao_flag',
            action='store_true',
            help='Read data/audio/video CD in disk-at-once mode.'
        )
        parser.add_argument(
            '-md5',
            dest='md5_flag',
            action='store_true',
            help='Create MD5 check sum of CD/DVD.'
        )
        parser.add_argument(
            '-speed',
            nargs=1,
            type=int,
            default=[8],
            help='Select CD/DVD spin speed.'
        )
        parser.add_argument(
            'device',
            nargs=1,
            metavar='device|scan',
            help='CD/DVD device (ie "/dev/sr0" or "scan".'
        )
        parser.add_argument(
            'image',
            nargs='?',
            metavar='image.iso|image.bin',
            help='ISO image file or BIN image filie for DAO mode.'
        )

        self._args = parser.parse_args(args)

    def parse(self, args):
        """
        Parse arguments
        """
        self._parse_args(args[1:])

        if self._args.speed[0] < 1:
            raise SystemExit(
                sys.argv[0] + ': You must specific a positive integer for '
                'CD/DVD device speed.'
            )
        if (
                self._args.device[0] != 'scan' and
                not os.path.exists(self._args.device[0])
        ):
            raise SystemExit(
                sys.argv[0] + ': Cannot find "' + self._args.device[0] +
                '" CD/DVD device.'
            )

        if self._args.image:
            self._image = self._args.image[0]
        elif self._args.dao_flag:
            self._image = 'file.bin'
        else:
            self._image = 'file.iso'


class Cdrom(object):
    """
    CDROM class
    """

    def __init__(self):
        self._devices = {}
        self.detect()

    def get_devices(self):
        """
        Return list of devices
        """
        return self._devices

    def detect(self):
        """
        Detect devices
        """
        for directory in glob.glob('/sys/block/sr*/device'):
            device = '/dev/' + os.path.basename(os.path.dirname(directory))
            model = ''
            for file in ('vendor', 'model'):
                try:
                    with open(
                        os.path.join(directory, file),
                        errors='replace'
                    ) as ifile:
                        model += ' ' + ifile.readline().strip()
                except OSError:
                    continue
            self._devices[device] = model


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
    def _cdspeed(device, speed):
        cdspeed = command_mod.Command('cdspeed', errors='ignore')
        if cdspeed.is_found():
            if speed:
                cdspeed.set_args([device, str(speed)])
            # If CD/DVD spin speed change fails its okay
            subtask_mod.Task(cdspeed.get_cmdline()).run()
        elif speed and os.path.isfile('/sbin/hdparm'):
            hdparm = command_mod.Command('/sbin/hdparm', errors='ignore')
            hdparm.set_args(['-E', str(speed), device])
            subtask_mod.Batch(hdparm.get_cmdline()).run()

    @staticmethod
    def _dao(device, speed, file):
        cdrdao = command_mod.Command('cdrdao', errors='stop')

        cdrdao.set_args(['read-cd', '--device', device, '--read-raw'])
        if speed:
            cdrdao.extend_args(['--speed', speed])
        if file.endswith('.bin'):
            cdrdao.extend_args(['--datafile', file, file[:-4] + '.toc'])
        else:
            cdrdao.extend_args(['--datafile', file, file + '.toc'])

        nice = command_mod.Command('nice', args=['-20'], errors='stop')
        task = subtask_mod.Task(nice.get_cmdline() + cdrdao.get_cmdline())
        task.run()
        if task.get_exitcode():
            raise SystemExit(
                sys.argv[0] + ': Error code ' + str(task.get_exitcode()) +
                ' received from "' + cdrdao.get_file() + '".'
            )

    @staticmethod
    def _md5sum(file):
        try:
            with open(file, 'rb') as ifile:
                md5 = hashlib.md5()
                while True:
                    chunk = ifile.read(131072)
                    if not chunk:
                        break
                    md5.update(chunk)
        except (OSError, TypeError):
            return ''
        return md5.hexdigest()

    @staticmethod
    def _scan():
        cdrom = Cdrom()
        print('Scanning for CD/DVD devices...')
        devices = cdrom.get_devices()
        for key, value in sorted(devices.items()):
            print('  {0:10s}  {1:s}'.format(key, value))

    def _tao(self, device, file):
        isoinfo = command_mod.Command('isoinfo', errors='stop')

        command = command_mod.Command('dd', errors='stop')
        command.set_args(
            ['if=' + device, 'bs=' + str(2048*4096), 'count=1', 'of=' + file])
        task = subtask_mod.Batch(command.get_cmdline())
        task.run()
        if task.get_error()[0].endswith('Permission denied'):
            raise SystemExit(
                sys.argv[0] + ': Cannot read from CD/DVD device. '
                'Please check permissions.'
            )
        elif not os.path.isfile(file):
            raise SystemExit(
                sys.argv[0] +
                ': Cannot find CD/DVD media. Please check drive.'
            )
        elif task.get_exitcode():
            raise SystemExit(
                sys.argv[0] + ': Error code ' + str(task.get_exitcode()) +
                ' received from "' + task.get_file() + '".'
            )

        isoinfo.set_args(['-d', '-i', file])
        task = subtask_mod.Batch(isoinfo.get_cmdline())
        task.run(pattern='^Volume size is: ')
        if not task.has_output():
            raise SystemExit(
                sys.argv[0] + ': Cannot find TOC on CD/DVD media. '
                'Disk not recognised.'
            )
        elif task.get_exitcode():
            raise SystemExit(
                sys.argv[0] + ': Error code ' + str(task.get_exitcode()) +
                ' received from "' + task.get_file() + '".'
            )
        blocks = int(task.get_output()[0].split()[-1])

        task2 = subtask_mod.Task(isoinfo.get_cmdline())
        task2.run(pattern=' id: $')
        if task2.get_exitcode():
            raise SystemExit(
                sys.argv[0] + ': Error code ' + str(task2.get_exitcode()) +
                ' received from "' + task2.get_file() + '".'
            )

        print('Creating ISO image file "' + file + '"...')
        command.set_args(
            ['if=' + device, 'bs=2048', 'count=' + str(blocks), 'of=' + file])

        nice = command_mod.Command('nice', args=['-20'], errors='stop')
        task2 = subtask_mod.Task(nice.get_cmdline() + command.get_cmdline())
        task2.run(pattern='Input/output error| records (in|out)$')

        if not os.path.isfile(file):
            raise SystemExit(
                sys.argv[0] + ': Cannot find CD/DVD media. '
                'Please check drive.'
            )
        pad = int(blocks * 2048 - file_mod.FileStat(file).get_size())
        if pad > 0 and pad < 16777216:
            print(pad, 'bytes flushing from CD/DVD prefetch bug...')
            with open(file, 'ab') as ofile:
                ofile.write(b'\0' * pad)
        self._isosize(file, file_mod.FileStat(file).get_size())

    @staticmethod
    def _isosize(image, size):
        if size > 734003200:
            print(
                "\n*** {0:s}: {1:4.2f} MB ({2:5.3f} "
                "salesman's GB) ***\n".format(
                    image, size/1048576, size/1000000000)
                )
            if size > 9400000000:
                sys.stderr.write(
                    '**WARNING** This ISO image file does not fit onto '
                    '9.4GB/240min Duel Layer DVD media.\n'
                )
                sys.stderr.write(
                    '        ==> Please split your data into '
                    'multiple images.\n'
                )
            elif size > 4700000000:
                sys.stderr.write(
                    '**WARNING** This ISO image file does not fit onto '
                    '4.7GB/120min DVD media.\n'
                )
                sys.stderr.write(
                    '        ==> Please use Duel Layer DVD media or split '
                    'your data into multiple images.\n'
                )
            else:
                sys.stderr.write(
                    '**WARNING** This ISO image file does not fit onto '
                    '700MB/80min CD media.\n'
                )
                sys.stderr.write(
                    '        ==> Please use DVD media or split your data '
                    'into multiple images.\n'
                )
            print()
        else:
            minutes, remainder = divmod(size, 734003200 / 80)
            seconds = remainder * 4800 / 734003200.
            print(
                '\n*** {0:s}: {1:4.2f} MB ({2:.0f} min '
                '{3:05.2f} sec) ***\n'.format(
                    image, size/1048576, minutes, seconds)
            )
            if size > 681574400:
                sys.stderr.write(
                    '**WARNING** This ISO image file does not fit onto '
                    '650MB/74min CD media.\n'
                )
                sys.stderr.write(
                    '        ==> Please use 700MB/80min CD media instead.\n')

    def run(self):
        """
        Start program
        """
        options = Options()

        device = options.get_device()
        if device == 'scan':
            self._scan()
        else:
            speed = options.get_speed()
            file = options.get_image()

            self._cdspeed(device, speed)
            if os.path.isfile(file):
                try:
                    os.remove(file)
                except OSError:
                    raise SystemExit(
                        sys.argv[0] + ': Cannot over write "' + file +
                        '" CD/DVD image file.'
                    )
            if options.get_disk_at_once_flag():
                self._dao(device, speed, file)
            else:
                self._tao(device, file)
            if options.get_md5_flag():
                print('Creating MD5 check sum of ISO file.')
                md5sum = self._md5sum(file)
                if not md5sum:
                    raise SystemExit(
                        sys.argv[0] + ': Cannot read "' + file + '" file.')
                else:
                    print(md5sum, file, sep='  ')
            time.sleep(1)
            eject = command_mod.Command('eject', errors='ignore')
            if eject.is_found():
                task = subtask_mod.Batch(eject.get_cmdline())
                task.run()
                if task.get_exitcode():
                    raise SystemExit(
                        sys.argv[0] + ': Error code ' +
                        str(task.get_exitcode()) + ' received from "' +
                        task.get_file() + '".'
                    )


if __name__ == '__main__':
    if '--pydoc' in sys.argv:
        help(__name__)
    else:
        Main()
