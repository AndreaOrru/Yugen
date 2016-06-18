"""Implementation of editor's text windows."""

import re

from attribute import Color, Property
from key import Key
from window import Window


class TextWindow(Window):
    """Class representing a window for text editing.

    It supports a cursor and the modification of text.
    """
    def __init__(self, *args, **kwargs):
        """Initialize a TextWindow object.

        See parent constructor (Window.__init__) for details.
        """
        self.__cursor = (0, 0)
        self._target_column = 0

        super().__init__(*args, **kwargs)

        self.key_bindings = {
            Key('C-j'): self.line_break,
            Key('M-i'): self.cursor_up,
            Key('M-k'): self.cursor_down,
            Key('M-j'): self.cursor_back,
            Key('M-l'): self.cursor_forward,
            Key('DEL'): self.char_delete_before,
            Key('DC'):  self.char_delete,
            Key('C-d'): self.char_delete,
            Key('M-b'): self.cursor_begin,
            Key('M-e'): self.cursor_end,
        }

    def _format(self, line):
        """Format a line of the buffer for visualization.
        Overrides Window._format.

        Args:
            line: Index of the buffer line to be formatted.

        Returns:
            (content, attributes): Tuple containing the characters to be
                printed, and attributes for each character.
        """
        content, attributes = super()._format(line)

        for m in re.finditer(r"return", content):
            attributes[m.start(): m.end()] = [((Color.LightGreen, Color.Black), Property.Default)] * len(m.group())

        for m in re.finditer(r"def\b", content):
            attributes[m.start(): m.end()] = [((Color.LightRed, Color.Black), Property.Default)] * len(m.group())

        return content, attributes

    def _update(self):
        """Reload the window from its associated buffer.
        Overrides Window._update.
        """
        super()._update()
        self.cursor_begin()

    @property
    def cursor(self):
        """Position of the cursor."""
        return self.__cursor

    @cursor.setter
    def cursor(self, cursor):
        self.__cursor = cursor
        self._ui_window.cursor = cursor[0], cursor[1]

    def cursor_up(self):
        """Move the cursor up one line to reach the target column."""
        cursor = self._buffer.char_above(self.cursor[0], self._target_column)
        self.cursor = cursor if cursor else self.cursor

    def cursor_down(self):
        """Move the cursor down one line to reach the target column."""
        cursor = self._buffer.char_below(self.cursor[0], self._target_column)
        self.cursor = cursor if cursor else self.cursor

    def cursor_back(self):
        """Move the cursor back by one character and reset the target column."""
        cursor = self._buffer.char_before(*self.cursor)
        self.cursor = cursor if cursor else self.cursor
        self._target_column = self.cursor[1]

    def cursor_forward(self):
        """Move the cursor forward by one character and reset the target column."""
        cursor = self._buffer.char_after(*self.cursor)
        self.cursor = cursor if cursor else self.cursor
        self._target_column = self.cursor[1]

    def cursor_begin(self):
        """Move the cursor to the beginning of the buffer."""
        self.cursor = (0, 0)

    def cursor_end(self):
        """Move the cursor to the end of the buffer."""
        self.cursor = self._buffer.end

    def char_insert(self, char):
        """Insert a character at the current position, updating
        the buffer and the cursor accordingly.

        Args:
            char: Charactere to insert.
        """
        self._buffer.char_insert(char, *self.cursor)
        self.cursor_forward()

    def char_delete(self):
        """Delete the character at the current position, updating
        the buffer and the cursor accordingly.
        """
        try:
            self._buffer.char_delete(*self.cursor)
            self.cursor = self.cursor[0], min(self.cursor[1], len(self._buffer.lines[self.cursor[0]]))
        except IndexError:
            pass

    def char_delete_before(self):
        """Delete the character at the preceding position, updating
        the buffer and the cursor accordingly.
        """
        before = self._buffer.char_before(*self.cursor)
        if before:
            self._buffer.char_delete(*before)
            self.cursor = before

    def line_break(self):
        """Break a line in two lines at the current position."""
        self._buffer.line_break(*self.cursor)
        self.cursor = self._buffer.char_after(*self.cursor)

    def key_handle(self, key):
        """Try to handle the given keypress.

        Args:
            key: Key object representing the keys pressed.

        Returns:
            True if handled, False otherwise.
        """
        if key.is_printable():
            self.char_insert(key.char())
        else:
            try:
                self.key_bindings[key]()
            except KeyError:
                return False
        return True
