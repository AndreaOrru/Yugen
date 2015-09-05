from abc import ABC, abstractmethod, abstractproperty


class UIWindow(ABC):
    def __init__(self, ui, line, column, n_lines, n_columns):
        self._ui = ui
        self._line = line
        self._column = column
        self._n_lines = n_lines
        self._n_columns = n_columns

        self._cursor_show = False
        self._cursor = (0, 0)

    @property
    def cursor(self):
        return self._cursor

    @cursor.setter
    def cursor(self, cursor):
        self._cursor = cursor

    def cursor_show(self):
        self._cursor_show = True

    def cursor_hide(self):
        self._cursor_show = False

    @abstractmethod
    def attributes_set(self, colors, properties):
        return

    @abstractmethod
    def line_update(self, line, content, attributes):
        return

    @abstractmethod
    def line_insert(self, line, content, attributes):
        return

    @abstractmethod
    def line_delete(self, line):
        return

    @abstractmethod
    def refresh(self):
        return

    @abstractmethod
    def key_get(self):
        return


class UI(ABC):
    @abstractmethod
    def __init__(self):
        self._ui_windows = list()

    @abstractproperty
    def max_lines(self):
        return

    @abstractproperty
    def max_columns(self):
        return

    @abstractmethod
    def refresh(self):
        return

    @abstractmethod
    def window_create(self, line, column, n_lines, n_columns):
        return
