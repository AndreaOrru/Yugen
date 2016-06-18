"""Generic editor functionalities."""

from buffer import Buffer
from command_window import CommandWindow
from key import Key
from status_window import StatusWindow
from text_window import TextWindow


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
            self._status_window.update()
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
        """TextWindow currently being edited (read-only)."""
        return self._windows[0]

    @property
    def window_focused(self):
        """Window on which the cursor is."""
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
        """Try to handle the given keypress.
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
