import curses
from curses import ascii
from curses.ascii import isctrl, unctrl
from key import Key
from attribute import Color
from ui import UI, UIWindow


class CursesWindow(UIWindow):
    def __init__(self, ui, line, column, n_lines, n_columns):
        super(CursesWindow, self).__init__(ui, line, column, n_lines, n_columns)
        self._window = curses.newpad(self._n_lines, self._n_columns)
        self._window.keypad(True)

        self._scroll = 0
        self._drawn_cursor = self._cursor

    def cursor_hide(self):
        super(CursesWindow, self).cursor_hide()
        self._window.chgat(self._cursor[0], self._cursor[1], 1, curses.A_NORMAL)

    def refresh(self):
        if self._cursor_show:
            self._window.chgat(self._drawn_cursor[0], self._drawn_cursor[1], 1, curses.A_NORMAL)
            self._drawn_cursor = self._cursor
            self._window.chgat(self._cursor[0], self._cursor[1], 1, curses.A_REVERSE)
        self._window.noutrefresh(self._scroll, 0, self._line, self._column, self._line + self._n_lines, self._column + self._n_columns)

    def attributes_set(self, colors, properties):
        self._window.bkgd(' ', self._ui.color_pair(colors) | properties)

    def line_update(self, line, content, attributes):
        """Show the given content in the specified line."""
        self._window.move(line, 0)
        for column, (char, attribute) in enumerate(zip(content, attributes)):
            self._window.addstr(line, column, char, self._ui.color_pair(attribute[0]) | attribute[1])
        self._window.clrtoeol()

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
        super(Curses, self).__init__()
        self._screen = screen
        self._color_pair = {Color.Default: 0}
        curses.raw()
        curses.curs_set(0)

    @property
    def max_lines(self):
        """Maximum number of lines on screen."""
        return curses.LINES

    @property
    def max_columns(self):
        """Maximum number of columns on screen."""
        return curses.COLS

    def refresh(self):
        """Update the screen."""
        for window in self._ui_windows:
            window.refresh()
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
        window = CursesWindow(self, line, column, n_lines, n_columns)
        self._ui_windows.append(window)
        return window
