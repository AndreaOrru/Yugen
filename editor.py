"""Generic editor functionalities."""

from attribute import Color, Property
from key import Key
from inspect import getmembers, isroutine
from functools import partial


class Buffer:
    """Class representing a text buffer.

    Buffer is a container for text. Every Buffer is associated with
    zero or more Window objects that display the text.
    If the buffer's content changes in any way, all the windows receive
    notifications about the change.
    A Buffer can be associated to one file.
    """

    def __init__(self, content='', window=None):
        """Initialize a Buffer object.

        Args:
            content: String containing the initial text of the buffer. (default '')
            window: Window object to be linked to the buffer. (default None)
        """
        self._lines = content.split('\n')
        self._windows = {window} if window else set()
        self._file_name = None

    @property
    def content(self):
        """String containing the buffer's text."""
        return '\n'.join(self._lines)

    @content.setter
    def content(self, content):
        self._lines = content.split('\n')
        self._windows_update()

    @property
    def lines(self):
        """List of strings, one per line in the buffer's text.
        Does not include newlines.
        """
        return self._lines

    def file_open(self, file_name):
        self._file_name = file_name
        self.content = open(file_name, 'r').read()

    def file_write(self, file_name=None):
        if file_name is None:
            file_name = self._file_name
        elif self._file_name is None:
            self._file_name = file_name
        open(file_name, 'w').write(self.content)

    @property
    def windows(self):
        """Set of Window objects linked to the buffer (read-only)."""
        return self._windows

    def window_link(self, window):
        """Link a window to the buffer.

        Args:
            window: Window object to be linked.
        """
        self._windows.add(window)
        window._update()

    def window_unlink(self, window):
        """Unlink a window from the buffer.

        Args:
            window: Window object to unlink.
        """
        self._windows.discard(window)

    def _windows_update(self):
        """Update the content of the linked windows."""
        for window in self._windows:
            window._update()

    def _windows_line_update(self, line):
        """Notify all the linked windows that a line has been changed.

        Args:
            line: Index of the modified line.
        """
        for window in self._windows:
            window._line_update(line)

    def _windows_line_insert(self, line):
        """Notify all the linked windows that a line has been inserted.

        Args:
            line: Index of the inserted line.
        """
        for window in self._windows:
            window._line_insert(line)

    def _windows_line_delete(self, line):
        """Notify all the linked windows that a line has been deleted.

        Args:
            line: Index of the deleted line.
        """
        for window in self._windows:
            window._line_delete(line)

    @property
    def end(self):
        """Coordinates of the last character in the buffer (read-only)."""
        return len(self._lines) - 1, len(self._lines[-1])

    def char_above(self, line, column):
        """Get the coordinates of the character above the given one.

        Args:
            line: Index of the character's line.
            column: Index of the character's column.

        Returns:
            (line, column): Coordinates corresponding to the character above.
            None: If there are no characters above the given one.
        """
        if line > 0:
            return line-1, min(column, len(self._lines[line-1]))

    def char_below(self, line, column):
        """Get the coordinates of the character below the given one.

        Args:
            line: Index of the character's line.
            column: Index of the character's column.

        Returns:
            (line, column): Coordinates corresponding to the character below.
            None: If there are no characters below the given one.
        """
        if line+1 < len(self._lines):
            return line+1, min(column, len(self._lines[line+1]))

    def char_before(self, line, column):
        """Get the coordinates of the character before the given one.

        Args:
            line: Index of the character's line.
            column: Index of the character's column.

        Returns:
            (line, column): Coordinates corresponding to the previous character.
            None: If there are no characters before the given one.
        """
        if column > 0:
            return line, column - 1
        elif line > 0:
            return line-1, len(self._lines[line-1])

    def char_after(self, line, column):
        """Get the coordinates of the character after the given one.

        Args:
            line: Index of the character's line.
            column: Index of the character's column.

        Returns:
            (line, column): Coordinates corresponding to the next character.
            None: If there are no characters after the given one.
        """
        if column < len(self._lines[line]):
            return line, column + 1
        elif line+1 < len(self._lines):
            return line + 1, 0

    def char_insert(self, char, line, column):
        """Insert a character at the given position, moving the other characters accordingly.

        Args:
            char: Charactere to insert.
            line: Index of the line where to insert the character.
            column: Index of the line where to insert the character.
        """
        self._lines[line] = self._lines[line][:column] + char + self._lines[line][column:]
        self._windows_line_update(line)

    def char_delete(self, line, column):
        """Delete the character at the given position, moving the other characters accordingly.
        If the character is at the end of the line, merge the line with the next one.

        Args:
            line: Index of the line where to delete a character.
            column: Index of the line where to delete a character.
        """
        if column == len(self._lines[line]):
            self._lines[line: line+2] = [self._lines[line] + self._lines[line+1]]
            self._windows_line_update(line)
            self._windows_line_delete(line+1)
        else:
            self._lines[line] = self._lines[line][:column] + self._lines[line][column+1:]
            self._windows_line_update(line)

    def line_break(self, line, column):
        """Break a line in two lines at the given column.

        Args:
            line: Index of the line to break.
            column: Index of the column where to break the line.
        """
        self._lines[line: line+1] = [self._lines[line][:column], self._lines[line][column:]]
        self._windows_line_update(line)
        self._windows_line_insert(line+1)


class Window:
    """Class representing a generic window inside the editor.

    Window is a buffer displayer. Every Window is associated with
    only one Buffer object.
    Windows respond to buffer's change notifications and update
    themselves accordingly.
    """

    def __init__(self, editor, line, column, n_lines, n_columns, buffer=None):
        """Initialize a Window object.

        Args:
            editor: Editor object to which the window belongs.
            line: Index of the vertical position of the window in the editor.
            column: Index of the horizontal position of the window in the editor.
            n_lines: Window's height.
            n_columns: Window's width.
            buffer: Initial buffer to display. (default None: create empty buffer)
        """
        self._editor = editor
        self._ui_window = editor._ui.window_create(line, column, n_lines, n_columns)
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
        """Generate attributes for the text to display.

        Args:
            content: Text to display.

        Yields:
            (Color, Property): Attributes for a character.
        """
        for char in content:
            yield (Color.Default, Property.Default)

    def _update(self):
        for line in range(len(self._buffer.lines)):
            self._line_update(line)

    def _line_update(self, line):
        """Update a buffer line in the user interface.

        Args:
            line: Index of the buffer line to be updated.
        """
        content = self._buffer.lines[line]
        self._ui_window.line_update(line, content, self._decorate(content))

    def _line_insert(self, line):
        """Insert a new buffer line in the user interface.

        Args:
            line: Index of the buffer line to be inserted.
        """
        content = self._buffer.lines[line]
        self._ui_window.line_insert(line, content, self._decorate(content))

    def _line_delete(self, line):
        """Delete a buffer line from the user interface.

        Args:
            line: Index of the buffer line to be deleted.
        """
        self._ui_window.line_delete(line)


class TextWindow(Window):
    """Class representing a window for text editing.

    It supports a cursor and the modification of text.
    """

    def __init__(self, *args, **kwargs):
        """Initialize a TextWindow object.

        See parent constructor (Window.__init__) for details.
        """
        super().__init__(*args, **kwargs)

        self._cursor_line = 0
        self._cursor_column = 0
        self._target_column = 0

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
            Key('DEL'):   self.char_delete_before,
            Key('DC'):    self.char_delete,
            Key('M-b'):   self.cursor_begin,
            Key('M-e'):   self.cursor_end,
        }

    def _update(self):
        super()._update()
        self.cursor_begin()

    @property
    def cursor(self):
        """Position of the cursor."""
        return self._cursor_line, self._cursor_column

    @cursor.setter
    def cursor(self, cursor):
        self._cursor_line, self._cursor_column = cursor
        self._ui_window.cursor = cursor

    def cursor_up(self):
        """Move the cursor up one line to reach the target column."""
        self.cursor = self._buffer.char_above(self._cursor_line, self._target_column)

    def cursor_down(self):
        """Move the cursor down one line to reach the target column."""
        self.cursor = self._buffer.char_below(self._cursor_line, self._target_column)

    def cursor_back(self):
        """Move the cursor back by one character and reset the target column."""
        cursor = self._buffer.char_before(*self.cursor)
        self.cursor = cursor if cursor else self.cursor
        self._target_column = self._cursor_column

    def cursor_forward(self):
        """Move the cursor forward by one character and reset the target column."""
        cursor = self._buffer.char_after(*self.cursor)
        self.cursor = cursor if cursor else self.cursor
        self._target_column = self._cursor_column

    def cursor_begin(self):
        """Move the cursor to the beginning of the buffer."""
        self.cursor = 0, 0

    def cursor_end(self):
        """Move the cursor to the end of the buffer."""
        self.cursor = self._buffer.end

    def char_insert(self, char):
        self._buffer.char_insert(char, *self.cursor)
        self.cursor_forward()

    def char_delete(self):
        try:
            self._buffer.char_delete(*self.cursor)
            self.cursor = self._cursor_line, min(self._cursor_column, len(self._buffer.lines[self._cursor_line]))
        except IndexError:
            pass

    def char_delete_before(self):
        before = self._buffer.char_before(*self.cursor)
        if before:
            self._buffer.char_delete(*before)
            self.cursor = before

    def line_break(self):
        self._buffer.line_break(*self.cursor)
        self.cursor = self._buffer.char_after(*self.cursor)

    def key_handle(self, key):
        if key.is_printable():
            self.char_insert(key.char())
        else:
            try:
                self.key_bindings[key]()
            except KeyError:
                return False
        return True


class StatusWindow(Window):
    def __init__(self, editor):
        super().__init__(editor, editor._ui.max_lines-2, 0, 1, editor._ui.max_columns)
        self._ui_window.attributes_set(Color.Default, Property.Reversed)


class CommandWindow(TextWindow):
    """Class representing the command window."""
    def __init__(self, editor):
        super().__init__(editor, editor._ui.max_lines-1, 0, 1, editor._ui.max_columns)
        self._editor = editor

        self._scope = self._build_scope(lambda: self._editor.window_current.buffer)
        self._scope.update(self._build_scope(lambda: self._editor.window_current))
        self._scope.update(self._build_scope(lambda: self._editor))

        self.key_bindings[Key('C-j')] = lambda: [self.evaluate(), self._editor.command_window_toggle()]

    def _build_scope(self, get_instance):
        cls = type(get_instance())
        scope = dict(getmembers(cls, lambda x: isroutine(x) and x.__name__[0] != '_'))
        scope = {n: partial(self._interactive, get_instance, f) for (n, f) in scope.items()}
        return scope

    def _interactive(self, get_instance, function, *args, **kwargs):
        return function(get_instance(), *args, **kwargs)

    def evaluate(self):
        try:
            try:
                result = eval(self._buffer.content, self._scope, globals())
                self._buffer.content = '' if (result is None) else str(result)
            except SyntaxError:
                exec(self._buffer.content, self._scope, globals())
                self._buffer.content = ''
        except Exception as exception:
            self._buffer.content = str(exception)

        self.cursor_end()


class Editor:
    """Class representing the whole editor.

    Editor has exactly one StatusWindow and one CommandWindow. It can
    contain one or more TextWindow.
    """

    def __init__(self, ui):
        """Initialize an Editor object.

        Args:
            ui: UI object representing the user interface.
        """
        self._ui = ui

        self._windows = list()
        self._window_welcome()
        self.window_focused = self._windows[0]  # Call setter.

        self._status_window = StatusWindow(self)
        self._command_window = CommandWindow(self)

        self.key_bindings = {
            Key('M-q'): quit,
            Key('M-x'): self.command_window_toggle,
        }

    def _run(self):
        """Start the execution loop."""
        while True:
            self._ui.refresh()
            self.key_handle(self._window_focused._ui_window.key_get())

    def command_window_toggle(self):
        """Switch the focus to and from the command window."""
        if self.window_focused is self._command_window:
            self.window_focused = self.window_current
        else:
            self.window_focused = self._command_window

    @property
    def window_current(self):
        """Window currently being edited (read-only)."""
        return self._windows[0]

    @property
    def window_focused(self):
        return self._window_focused

    @window_focused.setter
    def window_focused(self, window):
        try:
            self._window_focused._ui_window.cursor_hide()
        except AttributeError:
            pass
        self._window_focused = window
        self._window_focused._ui_window.cursor_show()

    def window_add(self, window):
        """Add a window to the editor.

        Args:
            window: Window object to be added to the editor.
        """
        if window not in self._windows:
            self._windows.append(window)

    def window_remove(self, window):
        """Remove a window from the editor.

        Args:
            window: Window object to be removed from the editor.
        """
        try:
            self._windows.remove(window)
        except ValueError:
            pass

    def _window_welcome(self):
        """Create and show the welcome window."""
        window = TextWindow(self, 0, 0, self._ui.max_lines-2, self._ui.max_columns,
                            Buffer('Welcome to Yugen, the subtly profound text editor.'))
        window.cursor_end()
        self.window_add(window)

    def key_handle(self, key):
        """Handle the given keypress.
        Gives priority to lower levels in the hierarchy, i.e.
        window keybindings are checked before global ones.

        Args:
            key: Key object representing the keys pressed.
        """
        if not self._window_focused.key_handle(key):
            try:
                self.key_bindings[key]()
            except KeyError:
                pass
