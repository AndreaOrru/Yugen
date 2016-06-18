"""Implementation of editor's status window."""

from attribute import Color, Property
from window import Window


class StatusWindow(Window):
    """Class representing a read-only window for showing the current status."""

    def __init__(self, editor):
        """Initialize a StatusWindow object.

        Args:
            editor: Editor object to which the window belongs.
        """
        super().__init__(editor, editor._ui.max_lines-2, 0, 1, editor._ui.max_columns)
        self._ui_window.attributes_set(Color.Defaults, Property.Reversed)

    def update(self):
        line, column = self._editor.window_current.cursor
        file_name = self._editor.window_current._buffer.file_name
        self._buffer.content = '{:<15}{}'.format('({}, {})'.format(line+1, column), file_name)
        self._update()
