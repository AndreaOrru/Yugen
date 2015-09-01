#!/usr/bin/env python3
"""Yugen, the subtly profound text editor."""

import curses
from curses import ascii
from curses.ascii import isctrl, isprint, unctrl
from abc import ABC, abstractmethod, abstractproperty
from attributes import Color, Property
from inspect import getmembers, isroutine
from functools import partial


class UIWindow(ABC):
    """Abstract class representing a window for a generic interface toolkit."""
    def __init__(self, ui, line, column, n_lines, n_columns):
        self._ui = ui
        self._line = line
        self._column = column
        self._n_lines = n_lines
        self._n_columns = n_columns

    @abstractmethod
    def refresh(self):
        return

    @abstractmethod
    def attributes_set(self, colors, properties):
        return

    @abstractmethod
    def cursor_draw(self, line, column):
        return

    @abstractmethod
    def cursor_hide(self):
        return

    @abstractmethod
    def line_update(self, line, content, attributes):
        """Show the given content in the specified line."""
        return

    @abstractmethod
    def line_insert(self, line, content, attributes):
        """Insert a line with the given content and move the next ones down."""
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
    def key_get(self, ui_window):
        """Wait for a keypress from a window and return it."""
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
        self._lines = content.split('\n')

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

    def char_up(self, line, column):
        if line > 0:
            return line - 1, min(column, len(self._lines[line-1]))

    def char_down(self, line, column):
        if line+1 < len(self._lines):
            return line + 1, min(column, len(self._lines[line+1]))

    def char_before(self, line, column):
        """Return the position of the character before the given one,
           or the position itself if there is not any."""
        if column > 0:
            return line, column - 1
        elif line > 0:
            return line - 1, len(self._lines[line-1])
        return line, column

    def char_after(self, line, column):
        """Return the position of the character after the given one,
           or the position itself if there is not any."""
        if column < len(self._lines[line]):
            return line, column + 1
        elif line+1 < len(self._lines):
            return line + 1, 0
        return line, column

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


class Window(ABC):
    def __init__(self, editor, line, column, n_lines, n_columns, buffer=None):
        self._ui = editor._ui
        self._ui_window = self._ui.window_create(line, column, n_lines, n_columns)
        self.buffer = buffer if buffer else Buffer(window=self)  # Call the setter.

    @property
    def buffer(self):
        """Buffer linked to the window."""
        return self._buffer

    @buffer.setter
    def buffer(self, buffer):
        self._buffer = buffer
        self._buffer.window_link(self)

    def _decorate(self, content):
        for char in content:
            yield (Color.Default, Property.Default)

    def _line_update(self, line, content):
        """Show the given content in the specified line."""
        self._ui_window.line_update(line, content, self._decorate(content))

    def _line_insert(self, line, content):
        """Insert a new line with the given content under the given line."""
        self._ui_window.line_insert(line, content, self._decorate(content))

    def _line_delete(self, line):
        """Delete the given line, move the other ones up."""
        self._ui_window.line_delete(line)


class TextWindow(Window):
    """Class representing a text-editing window."""
    def __init__(self, editor, line, column, n_lines, n_columns, buffer=None):
        self._cursor_line = 0
        self._cursor_column = 0
        self._target_column = 0

        super(TextWindow, self).__init__(editor, line, column, n_lines, n_columns, buffer)

        self.key_bindings = {
            Key('UP'):    self.cursor_up,
            Key('DOWN'):  self.cursor_down,
            Key('LEFT'):  self.cursor_back,
            Key('RIGHT'): self.cursor_forward,
            Key('C-j'):   self.line_break,
            Key('M-i'):   self.cursor_up,
            Key('M-k'):   self.cursor_down,
            Key('M-j'):   self.cursor_back,
            Key('M-l'):   self.cursor_forward,
            Key('DEL'):   self.char_delete,
            Key('M-b'):   self.cursor_begin_buffer,
            Key('M-e'):   self.cursor_end_buffer,
        }

    @property
    def cursor(self):
        """Position of the cursor."""
        return self._cursor_line, self._cursor_column

    def cursor_set(self, line, column):
        """Set the position of the cursor."""
        self._cursor_line = line
        self._cursor_column = column
        self.cursor_draw()

    def cursor_up(self):
        self.cursor_set(*self._buffer.char_up(self._cursor_line, self._target_column))

    def cursor_down(self):
        self.cursor_set(*self._buffer.char_down(self._cursor_line, self._target_column))

    def cursor_back(self):
        """Move the cursor back by one character."""
        self.cursor_set(*self._buffer.char_before(*self.cursor))
        self._target_column = self._cursor_column

    def cursor_forward(self):
        """Move the cursor forward by one character."""
        self.cursor_set(*self._buffer.char_after(*self.cursor))
        self._target_column = self._cursor_column

    def cursor_begin_buffer(self):
        """Move the cursor to the beginning of the buffer."""
        self.cursor_set(0, 0)

    def cursor_end_buffer(self):
        """Move the cursor to the end of the buffer."""
        self.cursor_set(*self._buffer.end)

    def cursor_draw(self):
        self._ui_window.cursor_draw(self._cursor_line, self._cursor_column)

    def cursor_hide(self):
        self._ui_window.cursor_hide()

    def char_insert(self, char, line=None, column=None):
        """Insert a character at the given position."""
        line, column = (line, column) if (line, column) != (None, None) else self.cursor
        self._buffer.char_insert(char, line, column)
        self.cursor_set(*self._buffer.char_after(line, column))

    def char_delete(self, line=None, column=None):
        """Delete the character at the given position."""
        line, column = (line, column) if (line, column) != (None, None) else self.cursor
        before = self._buffer.char_before(line, column)
        self._buffer.char_delete(*before)
        self.cursor_set(*before)

    def line_break(self, line=None, column=None):
        """Break the given line in two lines at the given column."""
        line, column = (line, column) if (line, column) != (None, None) else self.cursor
        self._buffer.line_break(line, column)
        self.cursor_set(*self._buffer.char_after(line, column))

    def _key_handle(self, key):
        """Handle the given keypress. Return True if it was handled, False otherwise."""
        if key.is_printable():
            self.char_insert(key.char())
        elif key in self.key_bindings:
            self.key_bindings[key]()
            return True
        return False


class StatusWindow(Window):
    def __init__(self, editor):
        super(StatusWindow, self).__init__(editor, editor._ui.max_lines() - 2, 0, 1, editor._ui.max_columns())
        self._ui_window.attributes_set(Color.Default, Property.Reversed)

    def update(self, cursor):
        self._buffer.content = '({},{})'.format(cursor[0] + 1, cursor[1])


class CommandWindow(TextWindow):
    """Class representing the command window."""
    def __init__(self, editor):
        super(CommandWindow, self).__init__(editor, editor._ui.max_lines() - 1, 0, 1, editor._ui.max_columns())
        self._editor = editor

        self._scope = self._build_scope(lambda: self._editor.window_editing.buffer)
        self._scope.update(self._build_scope(lambda: self._editor.window_editing))
        self._scope.update(self._build_scope(lambda: self._editor))

        self.key_bindings[Key('C-j')] = self.evaluate

    def _build_scope(self, get_instance):
        cls = type(get_instance())
        scope = dict(getmembers(cls, lambda x: isroutine(x) and x.__name__[0] != '_'))
        scope = {n: partial(self._interactive, get_instance, f) for (n, f) in scope.items()}
        return scope

    def _interactive(self, get_instance, function, *args, **kwargs):
        return function(get_instance(), *args, **kwargs)

    def evaluate(self):
        """Evaluate the content of the command window."""
        try:
            try:
                self._buffer.content = str(eval(self._buffer.content, self._scope))
            except SyntaxError:
                exec(self._buffer.content, self._scope)
                self._buffer.content = ''
        except Exception as exception:
            self._buffer.content = str(exception)

        self.cursor_end_buffer()


class Editor:
    """Class representing the editor."""
    def __init__(self, ui):
        self._ui = ui

        self._windows = list()
        self._window_welcome()
        self._window_focus = self._windows[0]

        self._status_window = StatusWindow(self)
        self._command_window = CommandWindow(self)

        self.key_bindings = {
            Key('M-q'): quit,
            Key('M-x'): self.command_window_toggle,
        }

    def run(self):
        """Run the editor."""
        while True:
            self._status_window.update(self._windows[0].cursor)
            self._ui.screen_update()
            self._key_handle(self._ui.key_get(self._window_focus._ui_window))

    def command_window_toggle(self):
        """Switch the focus to and from the command window."""
        self._window_focus.cursor_hide()
        if self._window_focus is self._command_window:
            self._window_focus = self.window_editing
        else:
            self._window_focus = self._command_window
        self._window_focus.cursor_draw()

    @property
    def window_editing(self):
        return self._windows[0]

    def window_create(self, line, column, n_lines, n_columns, buffer):
        """Create a new text window."""
        window = TextWindow(self, line, column, n_lines, n_columns, buffer)
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
        if not self._window_focus._key_handle(key):
            if key in self.key_bindings:
                self.key_bindings[key]()


class CursesWindow(UIWindow):
    """Class representing a window in curses."""
    def __init__(self, ui, line, column, n_lines, n_columns):
        super(CursesWindow, self).__init__(ui, line, column, n_lines, n_columns)
        self._window = curses.newpad(self._n_lines, self._n_columns)
        self._window.keypad(True)

        self._cursor_column = 0
        self._cursor_line = 0
        self._scroll = 0

    def refresh(self):
        self._window.noutrefresh(self._scroll, 0, self._line, self._column, self._line + self._n_lines, self._column + self._n_columns)

    def attributes_set(self, colors, properties):
        super(CursesWindow, self).attributes_set(colors, properties)
        self._window.bkgd(' ', self._ui.color_pair(colors) | properties)
        self.refresh()

    def cursor_draw(self, line, column):
        if line >= self._scroll + self._n_lines:
            self._scroll += line - (self._scroll + self._n_lines) + 1
        elif line < self._scroll:
            self._scroll -= self._scroll - line

        self._window.chgat(self._cursor_line, self._cursor_column, 1, curses.A_NORMAL)
        self._cursor_line, self._cursor_column = line, column
        self._window.chgat(self._cursor_line, self._cursor_column, 1, curses.A_REVERSE)
        self.refresh()

    def cursor_hide(self):
        self._window.chgat(self._cursor_line, self._cursor_column, 1, curses.A_NORMAL)
        self.refresh()

    def line_update(self, line, content, attributes):
        """Show the given content in the specified line."""
        for column, (char, attribute) in enumerate(zip(content, attributes)):
            self._window.addstr(line, column, char, self._ui.color_pair(attribute[0]) | attribute[1])
        self._window.clrtoeol()
        self.refresh()

    def line_insert(self, line, content, attributes):
        """Insert a line with the given content and move the next ones down."""
        height, width = self._window.getmaxyx()
        if line >= height:
            self._window.resize(height*2, width)

        self._window.move(line, 0)
        self._window.insertln()
        self.line_update(line, content, attributes)

    def line_delete(self, line):
        """Delete the given line, move the other ones up."""
        self._window.move(line, 0)
        self._window.deleteln()
        self.refresh()

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
        self._color_pair = {Color.Default: 0}
        curses.raw()
        curses.curs_set(0)

    def max_lines(self):
        """Maximum number of lines on screen."""
        return curses.LINES

    def max_columns(self):
        """Maximum number of columns on screen."""
        return curses.COLS

    def screen_update(self):
        """Update the screen."""
        curses.doupdate()

    def color_pair(self, attribute):
        try:
            n = self._color_pair[attribute]
        except KeyError:
            n = len(self._color_pair)
            curses.init_pair(n, *attribute)
            self._color_pair[attribute] = n
        return curses.color_pair(n)

    def window_create(self, line, column, n_lines, n_columns):
        """Create a new window."""
        return CursesWindow(self, line, column, n_lines, n_columns)

    def key_get(self, ui_window):
        """Wait for a keypress from a window and return it."""
        return ui_window.key_get()


if __name__ == '__main__':
    def main(stdscr):
        editor = Editor(Curses(stdscr))
        editor.run()
    curses.wrapper(main)
