from abc import ABC, abstractmethod, abstractproperty


class UIWindow(ABC):
    def __init__(self, ui, line, column, n_lines, n_columns):
        self._ui = ui
        self._line = line
        self._column = column
        self._n_lines = n_lines
        self._n_columns = n_columns

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
