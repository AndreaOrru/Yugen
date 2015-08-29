#!/usr/bin/env python3
"""Yugen, the subtly profound text editor."""

import curses
from curses import ascii
from curses.ascii import isctrl, isprint, unctrl
from abc import ABC, abstractmethod


class UIWindow(ABC):
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
        return

    @abstractmethod
    def line_update(self, content, line):
        return

    @abstractmethod
    def line_insert(self, content, line):
        return

    @abstractmethod
    def key_get(self):
        return


class UI(ABC):
    @abstractmethod
    def max_lines(self):
        return

    @abstractmethod
    def max_columns(self):
        return

    @abstractmethod
    def screen_update(self):
        return

    @abstractmethod
    def window_create(self, line, column, n_lines, n_columns):
        return

    @abstractmethod
    def key_get(self, ui_window_active):
        return


class Key:
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
        return not (self.meta or self.ctrl) and isprint(chr(self.key))

    def char(self):
        return chr(self.key)

    def __eq__(self, o):
        return self.meta == o.meta and self.ctrl == o.ctrl and self.key == o.key

    def __hash__(self):
        return self.key << 2 | self.ctrl << 1 | self.meta


class Buffer:
    def __init__(self, window=None, content=''):
        self._windows = {window} if window else set()
        self.content = content

    @property
    def content(self):
        return '\n'.join(self._lines)

    @content.setter
    def content(self, content):
        self._lines = content.split('\n')
        self.windows_update()

    @property
    def lines(self):
        return self._lines

    @property
    def windows(self):
        return self._windows

    @property
    def end(self):
        return len(self._lines) - 1, len(self._lines[-1])

    def char_before(self, line, column):
        if column > 0:
            return line, column - 1
        elif line > 0:
            return line - 1, len(self._lines[line-1])
        return 0, 0

    def char_after(self, line, column):
        if column < len(self._lines[line]):
            return line, column + 1
        elif line+1 < len(self._lines):
            return line + 1, 0
        return line, column

    def char_insert(self, char, line, column):
        self._lines[line] = self._lines[line][:column] + char + self._lines[line][column:]
        self._windows_line_update(self._lines[line], line)

    def char_delete(self, line, column):
        self._lines[line] = self._lines[line][:column] + self._lines[line][column+1:]
        self._windows_line_update(self._lines[line], line)

    def line_break(self, line, column):
        self._lines[line: line+1] = [self._lines[line][:column], self._lines[line][column:]]
        self._windows_line_update(self._lines[line], line)
        self._windows_line_insert(self._lines[line+1], line+1)

    def window_link(self, window):
        self._windows.add(window)
        self.window_update(window)

    def window_unlink(self, window):
        self._windows.discard(window)

    def window_update(self, window):
        for line, content in enumerate(self._lines):
            window._line_update(content, line)
            window.cursor_begin_buffer()

    def windows_update(self):
        for window in self._windows:
            self.window_update(window)

    def _windows_line_update(self, content, line):
        for window in self._windows:
            window._line_update(content, line)

    def _windows_line_insert(self, content, line):
        for window in self._windows:
            window._line_insert(content, line)


class Window:
    def __init__(self, ui, line, column, n_lines, n_columns, buffer=None):
        self._ui = ui
        self._ui_window = ui.window_create(line, column, n_lines, n_columns)
        self.buffer = buffer if buffer else Buffer(self)  # Call the setter.

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
        return self._buffer

    @buffer.setter
    def buffer(self, buffer):
        try:
            self._buffer = buffer
            self._buffer.window_link(self)
        except AttributeError:
            self._buffer = Buffer(self, buffer)

    @property
    def cursor(self):
        return self._ui_window._cursor_line, self._ui_window._cursor_column

    def cursor_set(self, line, column):
        self._ui_window.cursor_set(line, column)

    def cursor_back(self):
        return self.cursor_set(*self._buffer.char_before(*self.cursor))

    def cursor_forward(self):
        return self.cursor_set(*self._buffer.char_after(*self.cursor))

    def cursor_begin_buffer(self):
        return self.cursor_set(0, 0)

    def cursor_end_buffer(self):
        return self.cursor_set(*self._buffer.end)

    def char_insert(self, char, line=None, column=None):
        line, column = (line, column) if (line, column) != (None, None) else self.cursor
        self._buffer.char_insert(char, line, column)
        self.cursor_set(*self._buffer.char_after(line, column))

    def char_delete(self, line=None, column=None):
        line, column = (line, column) if (line, column) != (None, None) else self.cursor
        self._buffer.char_delete(*self._buffer.char_before(line, column))
        self.cursor_set(*self._buffer.char_before(line, column))

    def line_break(self, line=None, column=None):
        line, column = (line, column) if (line, column) != (None, None) else self.cursor
        self._buffer.line_break(line, column)
        self.cursor_set(*self._buffer.char_after(line, column))

    def _line_update(self, content, line):
        self._ui_window.line_update(content, line)

    def _line_insert(self, content, line):
        self._ui_window.line_insert(content, line)

    def _key_handle(self, key):
        if key.is_printable():
            self.char_insert(key.char())
        elif key in self.key_bindings:
            self.key_bindings[key]()
            return True
        return False


class CommandWindow(Window):
    def __init__(self, ui):
        super(CommandWindow, self).__init__(ui, ui.max_lines() - 2, 0, 2, ui.max_columns())

        self.key_bindings[Key('C-j')] = self.evaluate

    def evaluate(self):
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
        while True:
            self._ui.screen_update()
            self._key_handle(self._ui.key_get(self._window_active._ui_window))

    def command_window_toggle(self):
        if self._window_active is self._command_window:
            self._window_active = self._windows[0]
        else:
            self._window_active = self._command_window
        self._window_active.cursor_set(*self._window_active.cursor)

    def window_create(self, line, column, n_lines, n_columns, buffer):
        window = Window(self._ui, line, column, n_lines, n_columns, buffer)
        self._window_link(window)
        return window

    def _window_link(self, window):
        if window not in self._windows:
            self._windows.append(window)

    def _window_unlink(self, window):
        try:
            self._windows.remove(window)
        except ValueError:
            pass

    def _window_welcome(self):
        window = self.window_create(0, 0, self._ui.max_lines() - 2, self._ui.max_columns(),
                                    'Welcome to Yugen, the subtly profound text editor.')
        window.cursor_end_buffer()

    def _key_handle(self, key):
        if not self._window_active._key_handle(key):
            if key in self.key_bindings:
                self.key_bindings[key]()


class CursesWindow(UIWindow):
    def __init__(self, ui, line, column, n_lines, n_columns):
        super(CursesWindow, self).__init__(ui, line, column, n_lines, n_columns)
        self._window = self._ui._screen.subpad(n_lines, n_columns, line, column)
        self._window.keypad(True)

    def key_get(self):
        key1 = self._window.getch()
        key2 = self._window.getch() if (key1 == ascii.ESC) else None

        meta = (key1 == ascii.ESC)
        key = (key2 if meta else key1)
        ctrl = isctrl(key)
        key = ord(unctrl(key)[-1].lower()) if (key < 0x20) else key

        return Key(key, ctrl, meta)

    def cursor_set(self, line, column, update_cursor=True):
        self._window.move(line, column)
        if update_cursor:
            self._cursor_line, self._cursor_column = line, column
            self._window.noutrefresh()

    def line_update(self, content, line):
        self._window.addstr(line, 0, content)
        self._window.clrtoeol()
        self.cursor_set(self._cursor_line, self._cursor_column, False)
        self._window.noutrefresh()

    def line_insert(self, content, line):
        self.cursor_set(line, 0, False)
        self._window.insertln()
        self.line_update(content, line)


class Curses(UI):
    def __init__(self, screen):
        self._screen = screen
        curses.raw()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

    def max_lines(self):
        return curses.LINES

    def max_columns(self):
        return curses.COLS

    def screen_update(self):
        curses.doupdate()

    def window_create(self, line, column, n_lines, n_columns):
        return CursesWindow(self, line, column, n_lines, n_columns)

    def key_get(self, ui_window_active):
        return ui_window_active.key_get()


if __name__ == '__main__':
    def main(stdscr):
        editor = Editor(Curses(stdscr))
        editor.run()
    curses.wrapper(main)
