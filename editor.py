"""Generic editor functionalities."""


class Editor:
    """Class representing the whole editor.

    Editor has exactly one StatusWindow and one CommandWindow. It can
    contain one or more TextWindow.
    """

    def __init__(self, ui):
        self._ui = ui

        self._text_windows = list()
        self._status_window = StatusWindow(self)
        self._command_window = CommandWindow(self)

        self.key_bindings = {
            Key('M-q'): quit,
        }

    def _run(self):
        """Start the execution loop."""
        while True:
            self._ui.screen_update()
            self.key_handle(self._window_focused.key_get())

    @property
    def window_current(self):
        """TextWindow currently being edited (read-only)."""
        return self._text_windows[0]


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


class Buffer:
    """Class representing a text buffer.

    Buffer is a container for text. Every Buffer is associated with
    zero or more Window objects that display the text.
    If the buffer's content changes in any way, all the windows receive
    notifications about the change.
    """

    def __init__(self, content='', window=None):
        """Initialize a Buffer object.

        Args:
            content: String containing the initial text of the buffer. (default '')
            window: Window object to be linked to the buffer. (default None)
        """
        self._lines = content.split('\n')
        self._windows = {window} if window else set()

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

    @property
    def windows(self):
        """Set of Window objects linked to the buffer (read-only)."""
        return self._windows

    def window_link(self, window: 'Window'):
        """Link a window to the buffer.

        Args:
            window: Window object to be linked.
        """
        self._windows.add(window)
        window._update()

    def window_unlink(self, window: 'Window'):
        """Unlink a window from the buffer.

        Args:
            window: Window object to unlink.
        """
        self._windows.discard(window)

    def _windows_update(self):
        """Update the content of the linked windows."""
        for window in self._windows:
            window._update()

    def _windows_line_update(self, line: 'Line'):
        """Notify all the linked windows that a line has been changed.

        Args:
            line: Index of the modified line.
        """
        for window in self._windows:
            window._line_update(line)

    def _windows_line_insert(self, line: 'Line'):
        """Notify all the linked windows that a line has been inserted.

        Args:
            line: Index of the inserted line.
        """
        for window in self._windows:
            window._line_insert(line)

    def _windows_line_delete(self, line: 'Line'):
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

    def char_above(self, line: 'Line', column: 'Column'):
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

    def char_below(self, line: 'Line', column: 'Column'):
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

    def char_before(self, line: 'Line', column: 'Column'):
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
            return line_1, len(self._lines[line-1])

    def char_after(self, line: 'Line', column: 'Column'):
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

    def char_insert(self, char: 'Character', line: 'Line', column: 'Column'):
        """Insert a character at the given position, moving the other characters accordingly.

        Args:
            char: Charactere to insert.
            line: Index of the line where to insert the character.
            column: Index of the line where to insert the character.
        """
        self._lines[line] = self._lines[line][:column] + char + self._lines[line][column:]
        self._windows_line_update(line)

    def char_delete(self, line: 'Line', column: 'Column'):
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

    def line_break(self, line: 'Line', column: 'Column'):
        """Break a line in two lines at the given column.

        Args:
            line: Index of the line to break.
            column: Index of the column where to break the line.
        """
        self._lines[line: line+1] = [self._lines[line][:column], self._lines[line][column:]]
        self._windows_line_update(line)
        self._windows_line_insert(line+1)
