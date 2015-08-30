#!/usr/bin/env python3
"""Yugen, the subtly profound text editor."""

import curses
from curses import ascii
from curses.ascii import isctrl, isprint, unctrl
from abc import ABC, abstractmethod, abstractproperty


class UIWindow(ABC):
    """Abstract class representing a window for a generic interface toolkit."""
    def __init__(self, ui, line, column, n_lines, n_columns):
        self._ui = ui
        self._line = line
        self._column = column
        self._n_lines = n_lines
        self._n_columns = n_columns
        self._cursor_line = 0
        self._cursor_column = 0

    @abstractmethod
    def cursor_set(self, line, column):
        """Set the position of the cursor."""
        return

    @abstractmethod
    def line_update(self, line, content):
        """Show the given content in the specified line."""
        return

    @abstractmethod
    def line_insert(self, line, content):
        """Insert a new line with the given content under the given line."""
        return

    @abstractmethod
    def line_delete(self, line):
        """Delete the given line, move the other ones up."""
        return

    @abstractmethod
    def key_get(self):
        """Wait for a keypress from inside the window and return it."""
        return


class UI(ABC):
    """Abstract class representing a generic interface toolkit."""

    @abstractproperty
    def max_lines(self):
        """Maximum number of lines on screen."""
        return

    @abstractproperty
    def max_columns(self):
        """Maximum number of columns on screen."""
        return

    @abstractmethod
    def screen_update(self):
        """Update the screen."""
        return

    @abstractmethod
    def window_create(self, line, column, n_lines, n_columns):
        """Create a new window."""
        return

    @abstractmethod
    def key_get(self, ui_window_active):
        """Wait for a keypress and return it."""
        return


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


class Buffer:
    """Class representing a text buffer."""
    def __init__(self, content='', window=None):
        self._windows = {window} if window else set()
        self.content = content

    @property
    def content(self):
        """Content of the buffer."""
        return '\n'.join(self._lines)

    @content.setter
    def content(self, content):
        self._lines = content.split('\n')
        self.windows_update()

    @property
    def lines(self):
        """Content of the buffer (in lines)."""
        return self._lines

    @property
    def windows(self):
        """Windows that are linked to the buffer."""
        return self._windows

    @property
    def end(self):
        """Line and column of the last character in the buffer."""
        return len(self._lines) - 1, len(self._lines[-1])

    def char_before(self, line, column):
        """Return the position of the character before the given one,
           or None if there is not one."""
        if column > 0:
            return line, column - 1
        elif line > 0:
            return line - 1, len(self._lines[line-1])

    def char_after(self, line, column):
        """Return the position of the character after the given one,
           or None if there is not one."""
        if column < len(self._lines[line]):
            return line, column + 1
        elif line+1 < len(self._lines):
            return line + 1, 0

    def char_insert(self, char, line, column):
        """Insert a character at the given position, and update the line."""
        self._lines[line] = self._lines[line][:column] + char + self._lines[line][column:]
        self._windows_line_update(line, self._lines[line])

    def char_delete(self, line, column):
        """Delete the character at the given position and update.
           If the character is a newline, merge the two consecutive lines."""
        if column == len(self._lines[line]):
            self._lines[line: line+2] = [self._lines[line] + self._lines[line+1]]
            self._windows_line_update(line, self.lines[line])
            self._windows_line_delete(line+1)
        else:
            self._lines[line] = self._lines[line][:column] + self._lines[line][column+1:]
            self._windows_line_update(line, self._lines[line])

    def line_break(self, line, column):
        """Break the given line in two lines at the given column."""
        self._lines[line: line+1] = [self._lines[line][:column], self._lines[line][column:]]
        self._windows_line_update(line, self._lines[line])
        self._windows_line_insert(line+1, self._lines[line+1])

    def window_link(self, window):
        """Link the given window to the buffer."""
        self._windows.add(window)
        self.window_update(window)

    def window_unlink(self, window):
        """Unlink the given window from the buffer."""
        self._windows.discard(window)

    def window_update(self, window):
        """Update the content of the given window."""
        for line, content in enumerate(self._lines):
            window._line_update(line, content)
            window.cursor_begin_buffer()

    def windows_update(self):
        """Update the content of the linked windows."""
        for window in self._windows:
            self.window_update(window)

    def _windows_line_update(self, line, content):
        """Update the given line to show the given content in the linked windows."""
        for window in self._windows:
            window._line_update(line, content)

    def _windows_line_insert(self, line, content):
        """Insert a line at the given position to show the given content in the linked windows."""
        for window in self._windows:
            window._line_insert(line, content)

    def _windows_line_delete(self, line):
        """Delete the given line from the linked windows."""
        for window in self._windows:
            window._line_delete(line)


class Window:
    """Class representing a text-editing window."""
    def __init__(self, ui, line, column, n_lines, n_columns, buffer=None):
        self._ui = ui
        self._ui_window = ui.window_create(line, column, n_lines, n_columns)
        self.buffer = buffer if buffer else Buffer(window=self)  # Call the setter.

        self.key_bindings = {
            Key('LEFT'):  self.cursor_back,
            Key('RIGHT'): self.cursor_forward,
            Key('C-j'):   self.line_break,
            Key('M-j'):   self.cursor_back,
            Key('M-l'):   self.cursor_forward,
            Key('DEL'):   self.char_delete,
        }

    @property
    def buffer(self):
        """Buffer linked to the window."""
        return self._buffer

    @buffer.setter
    def buffer(self, buffer):
        self._buffer = buffer
        self._buffer.window_link(self)

    @property
    def cursor(self):
        """Position of the cursor."""
        return self._ui_window._cursor_line, self._ui_window._cursor_column

    def cursor_set(self, line, column):
        """Set the position of the cursor."""
        self._ui_window.cursor_set(line, column)

    def cursor_back(self):
        """Move the cursor back by one character."""
        try:
            self.cursor_set(*self._buffer.char_before(*self.cursor))
        except TypeError:
            pass

    def cursor_forward(self):
        """Move the cursor forward by one character."""
        try:
            self.cursor_set(*self._buffer.char_after(*self.cursor))
        except TypeError:
            pass

    def cursor_begin_buffer(self):
        """Move the cursor to the beginning of the buffer."""
        self.cursor_set(0, 0)

    def cursor_end_buffer(self):
        """Move the cursor to the end of the buffer."""
        self.cursor_set(*self._buffer.end)

    def char_insert(self, char, line=None, column=None):
        """Insert a character at the given position."""
        line, column = (line, column) if (line, column) != (None, None) else self.cursor
        self._buffer.char_insert(char, line, column)
        self.cursor_set(*self._buffer.char_after(line, column))

    def char_delete(self, line=None, column=None):
        """Delete the character at the given position."""
        line, column = (line, column) if (line, column) != (None, None) else self.cursor
        try:
            self.cursor_set(*self._buffer.char_before(line, column))
            self._buffer.char_delete(*self._buffer.char_before(line, column))
        except TypeError:
            pass

    def line_break(self, line=None, column=None):
        """Break the given line in two lines at the given column."""
        line, column = (line, column) if (line, column) != (None, None) else self.cursor
        self._buffer.line_break(line, column)
        self.cursor_set(*self._buffer.char_after(line, column))

    def _line_update(self, line, content):
        """Show the given content in the specified line."""
        self._ui_window.line_update(line, content)

    def _line_insert(self, line, content):
        """Insert a new line with the given content under the given line."""
        self._ui_window.line_insert(line, content)

    def _line_delete(self, line):
        """Delete the given line, move the other ones up."""
        self._ui_window.line_delete(line)

    def _key_handle(self, key):
        """Handle the given keypress. Return True if it was handled, False otherwise."""
        if key.is_printable():
            self.char_insert(key.char())
        elif key in self.key_bindings:
            self.key_bindings[key]()
            return True
        return False


class CommandWindow(Window):
    """Class representing the command window."""
    def __init__(self, ui):
        super(CommandWindow, self).__init__(ui, ui.max_lines() - 2, 0, 2, ui.max_columns())

        self.key_bindings[Key('C-j')] = self.evaluate

    def evaluate(self):
        """Evaluate the content of the command window."""
        try:
            try:
                self._buffer.content = str(eval(self._buffer.content))
            except SyntaxError:
                exec(self._buffer.content)
                self._buffer.content = ''
        except Exception as exception:
            self._buffer.content = str(exception)

        self.cursor_end_buffer()


class Editor:
    """Class representing the editor."""
    def __init__(self, ui):
        self._ui = ui
        self._command_window = CommandWindow(ui)
        self._windows = list()
        self._window_welcome()
        self._window_active = self._windows[0]

        self.key_bindings = {
            Key('M-q'): quit,
            Key('M-x'): self.command_window_toggle,
        }

    def run(self):
        """Run the editor."""
        while True:
            self._ui.screen_update()
            self._key_handle(self._ui.key_get(self._window_active._ui_window))

    def command_window_toggle(self):
        """Switch the focus to and from the command window."""
        if self._window_active is self._command_window:
            self._window_active = self._windows[0]
        else:
            self._window_active = self._command_window
        self._window_active.cursor_set(*self._window_active.cursor)

    def window_create(self, line, column, n_lines, n_columns, buffer):
        """Create a new text window."""
        window = Window(self._ui, line, column, n_lines, n_columns, buffer)
        self._window_link(window)
        return window

    def _window_link(self, window):
        """Link a window to the editor."""
        if window not in self._windows:
            self._windows.append(window)

    def _window_unlink(self, window):
        """Unlink a window from the editor."""
        try:
            self._windows.remove(window)
        except ValueError:
            pass

    def _window_welcome(self):
        """Show a welcome window."""
        window = self.window_create(0, 0, self._ui.max_lines() - 2, self._ui.max_columns(),
                                    Buffer('Welcome to Yugen, the subtly profound text editor.'))
        window.cursor_end_buffer()

    def _key_handle(self, key):
        """Handle the given keypress."""
        if not self._window_active._key_handle(key):
            if key in self.key_bindings:
                self.key_bindings[key]()


class CursesWindow(UIWindow):
    """Class representing a window in curses."""
    def __init__(self, ui, line, column, n_lines, n_columns):
        super(CursesWindow, self).__init__(ui, line, column, n_lines, n_columns)
        self._window = self._ui._screen.subpad(n_lines, n_columns, line, column)
        self._window.keypad(True)

    def cursor_set(self, line, column, update_cursor=True):
        """Set the position of the cursor."""
        self._window.move(line, column)
        if update_cursor:
            self._cursor_line, self._cursor_column = line, column
            self._window.noutrefresh()

    def line_update(self, line, content):
        """Show the given content in the specified line."""
        self._window.addstr(line, 0, content)
        self._window.clrtoeol()
        self.cursor_set(self._cursor_line, self._cursor_column, False)
        self._window.noutrefresh()

    def line_insert(self, line, content):
        """Insert a new line with the given content under the given line."""
        self.cursor_set(line, 0, False)
        self._window.insertln()
        self.line_update(line, content)

    def line_delete(self, line):
        """Delete the given line, move the other ones up."""
        self.cursor_set(line, 0, False)
        self._window.deleteln()
        self.cursor_set(self._cursor_line, self._cursor_column, False)

    def key_get(self):
        """Wait for a keypress from inside the window and return it."""
        key1 = self._window.getch()
        key2 = self._window.getch() if (key1 == ascii.ESC) else None

        meta = (key1 == ascii.ESC)
        key = (key2 if meta else key1)
        ctrl = isctrl(key)
        key = ord(unctrl(key)[-1].lower()) if (key < 0x20) else key

        return Key(key, ctrl, meta)


class Curses(UI):
    """Class representing the curses toolkit."""
    def __init__(self, screen):
        self._screen = screen
        curses.raw()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

    def max_lines(self):
        """Maximum number of lines on screen."""
        return curses.LINES

    def max_columns(self):
        """Maximum number of columns on screen."""
        return curses.COLS

    def screen_update(self):
        """Update the screen."""
        curses.doupdate()

    def window_create(self, line, column, n_lines, n_columns):
        """Create a new window."""
        return CursesWindow(self, line, column, n_lines, n_columns)

    def key_get(self, ui_window_active):
        """Wait for a keypress and return it."""
        return ui_window_active.key_get()


if __name__ == '__main__':
    def main(stdscr):
        editor = Editor(Curses(stdscr))
        editor.run()
    curses.wrapper(main)
