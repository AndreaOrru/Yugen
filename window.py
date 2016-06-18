"""Implementation of editor's windows."""

from buffer import Buffer
from attribute import Color, Property


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

    def _format(self, line):
        """Format a line of the buffer for visualization.

        Args:
            line: Index of the buffer line to be formatted.

        Returns:
            (content, attributes): Tuple containing the characters to be
                printed, and attributes for each character.
        """
        content = self._buffer.lines[line]
        return content, [(Color.Defaults, Property.Default)] * len(content)

    def _update(self):
        """Reload the window from its associated buffer."""
        for line in range(len(self._buffer.lines)):
            self._line_update(line)

    def _line_update(self, line):
        """Update a buffer line in the user interface.

        Args:
            line: Index of the buffer line to be updated.
        """
        content, attributes = self._format(line)
        self._ui_window.line_update(line, content, attributes)

    def _line_insert(self, line):
        """Insert a new buffer line in the user interface.

        Args:
            line: Index of the buffer line to be inserted.
        """
        content, attributes = self._format(line)
        self._ui_window.line_insert(line, content, attributes)

    def _line_delete(self, line):
        """Delete a buffer line from the user interface.

        Args:
            line: Index of the buffer line to be deleted.
        """
        self._ui_window.line_delete(line)
