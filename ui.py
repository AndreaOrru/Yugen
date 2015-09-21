"""Abstract classes representing UI toolkit elements."""

from abc import ABC, abstractmethod, abstractproperty


class UIWindow(ABC):
    """Class representing a window in the user interface toolkit."""

    def __init__(self, ui, line, column, n_lines, n_columns):
        """Initialize an UIWindow object.

        Args:
            ui: UI object representing the user interface.
            line: Index of the vertical position of the window in the UI.
            column: Index of the horizontal position of the window in the UI.
            n_lines: Window's height.
            n_columns: Window's width.
        """
        self._ui = ui
        self._line = line
        self._column = column
        self._n_lines = n_lines
        self._n_columns = n_columns

        self._cursor_show = False
        self._cursor = (0, 0)

    @property
    def cursor(self):
        """Position of the cursor."""
        return self._cursor

    @cursor.setter
    def cursor(self, cursor):
        self._cursor = cursor

    def cursor_show(self):
        """Enable the cursor."""
        self._cursor_show = True

    def cursor_hide(self):
        """Disable the cursor."""
        self._cursor_show = False

    @abstractmethod
    def attributes_set(self, colors, properties):
        """Set the defaults attributes for the window.

        Args:
            colors: Default Color object for the window.
            properties: Default Property object for the window.
        """
        return

    @abstractmethod
    def line_update(self, line, content, attributes):
        """Update a line.

        Args:
            line: Index of the line to be updated.
            content: New content of the line.
            attributes: List of attributes, one for each char in content.
        """
        return

    @abstractmethod
    def line_insert(self, line, content, attributes):
        """Insert a line.

        Args:
            line: Index of the line to be inserted.
            content: New content of the line.
            attributes: List of attributes, one for each char in content.
        """
        return

    @abstractmethod
    def line_delete(self, line):
        """Delete a line.

        Args:
            line: Index of the line to be deleted.
        """
        return

    @abstractmethod
    def refresh(self):
        """Refresh the content of the window."""
        return

    @abstractmethod
    def key_get(self):
        """Wait for a keypress from inside the window and return it.

        Returns:
            Key object representing the keypress.
        """
        return


class UI(ABC):
    """Class representing the user interface toolkit."""

    @abstractmethod
    def __init__(self):
        """Initialize an UI object."""
        self._ui_windows = list()

    @abstractproperty
    def max_lines(self):
        """Maximum number of lines in the UI."""
        return

    @abstractproperty
    def max_columns(self):
        """Maximum number of columns in the UI."""
        return

    @abstractmethod
    def refresh(self):
        """Refresh the UI."""
        return

    @abstractmethod
    def window_create(self, line, column, n_lines, n_columns):
        """Create a new window.

        Args:
            line: Index of the vertical position of the window in the UI.
            column: Index of the horizontal position of the window in the UI.
            n_lines: Window's height.
            n_columns: Window's width.
        """
        return
