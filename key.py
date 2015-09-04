import curses
from curses import ascii
from curses.ascii import isprint


class Key:
    """Class representing a key combination."""

    keys = {k[4:]: eval('curses.'+k) for k in dir(curses) if k[:4] == 'KEY_'}
    keys['DEL'] = ascii.DEL

    def __init__(self, key, ctrl=None, meta=None):
        # key is a string:
        try:
            self.ctrl = 'C-' in key
            self.meta = 'M-' in key
            key = key.upper() if ('S-' in key) else key
            key = key.split('-')[-1]
            self.key = Key.keys[key] if (key in Key.keys) else ord(key)
        # key is an integer:
        except TypeError:
            self.key = key
            self.ctrl = ctrl
            self.meta = meta

    def is_printable(self):
        """Return True if the key corresponds to a printable character, False otherwise."""
        return not (self.meta or self.ctrl) and isprint(chr(self.key))

    def char(self):
        """Return the key character."""
        return chr(self.key)

    def __eq__(self, o):
        return self.meta == o.meta and self.ctrl == o.ctrl and self.key == o.key

    def __hash__(self):
        return self.key << 2 | self.ctrl << 1 | self.meta
