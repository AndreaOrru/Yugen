"""Implementation of editor's buffers."""


class Buffer:
    """Class representing a text buffer.

    Buffer is a container for text. Every Buffer is associated with
    zero or more Window objects that display the text.
    If the buffer's content changes in any way, all the windows receive
    notifications about the change.
    A Buffer can be associated with one file.
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

    @property
    def file_name(self):
        return self._file_name

    def file_open(self, file_name):
        """Open a file in the buffer.

        Args:
            file_name: Path of the file to open.
        """
        self._file_name = file_name
        self.content = open(file_name, 'r').read()

    def file_write(self, file_name=None):
        """Write the buffer in a file. Set the path as the buffer path
        if no file was previously associated to the buffer.

        Args:
            file_name: Path of the file to write. (default None: buffer path)
        """
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
            char: Character to insert.
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
