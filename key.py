"""Representation of keypresses."""

import curses
from curses import ascii
from curses.ascii import isprint


class Key:
    """Class representing a combination of key presses.

    Attributes:
        keys: Dictionary that maps key names to codes.
    """

    keys = {k[4:]: eval('curses.'+k) for k in dir(curses) if k[:4] == 'KEY_'}
    keys['DEL'] = ascii.DEL
    keys['TAB'] = ascii.TAB

    def __init__(self, key, ctrl=None, meta=None):
        """Initialize a Key object.

        Args:
            key: The integer ASCII value of the character corresponding to the keypress.
                Alternatively, a string in the format C-M-S-k, with C, M, S being optional
                modifier keys (Ctrl, Meta, Shift respectively) and k being a character.
                In the second case, the next arguments are ignored.
            ctrl: Ctrl modifier.
            meta: Meta modified.
        """
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
        """Return the character corresponding to the pressed key."""
        return chr(self.key)

    def __eq__(self, o):
        """Check whether two keys are equal."""
        return self.meta == o.meta and self.ctrl == o.ctrl and self.key == o.key

    def __hash__(self):
        """Return a hash value uniquely identifying a Key object."""
        return self.key << 2 | self.ctrl << 1 | self.meta
