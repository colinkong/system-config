#!/usr/bin/env python3
"""
Python X-windows desktop module

Copyright GPL v2: 2013-2016 By Dr Colin Kong

Version 2.0.1 (2016-03-05)
"""

import os
import sys

if sys.version_info < (3, 0) or sys.version_info >= (4, 0):
    sys.exit(__file__ + ': Requires Python version (>= 3.0, < 4.0).')


class Desktop(object):
    """
    Desktop class
    """

    def __init__(self):
        self._type = 'Unknown'

    @staticmethod
    def has_xfce():
        """
        Return true if running XFCE
        """
        keys = os.environ.keys()
        if 'XDG_MENU_PREFIX' in keys and os.environ['XDG_MENU_PREFIX'] == 'xfce-':
            return True
        elif 'XDG_CURRENT_DESKTOP' in keys and os.environ['XDG_CURRENT_DESKTOP'] == 'XFCE':
            return True
        elif 'XDG_DATA_DIRS' in keys and '/xfce' in os.environ['XDG_DATA_DIRS']:
            return True
        return False

    @staticmethod
    def has_gnome():
        """
        Return true if running Gnome
        """
        keys = os.environ.keys()
        if 'DESKTOP_SESSION' in keys and 'gnome' in os.environ['DESKTOP_SESSION']:
            return True
        elif 'GNOME_DESKTOP_SESSION_ID' in keys:
            return True
        return False

    @staticmethod
    def has_kde():
        """
        Return true if running KDE
        """
        keys = os.environ.keys()
        if 'DESKTOP_SESSION' in keys and 'kde' in os.environ['DESKTOP_SESSION']:
            return True
        return False

    def detect(self):
        """
        Return desktop name (xfce, gnome, kde)
        """
        if not self._type:
            if self.has_xfce():
                self._type = 'xfce'
            elif self.has_gnome():
                self._type = 'gnome'
            elif self.has_kde():
                self._type = 'kde'

        return self._type


if __name__ == '__main__':
    help(__name__)
