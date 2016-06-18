"""Implementation of editor's command windows."""

from functools import partial, update_wrapper
from inspect import getmembers, isdatadescriptor, isfunction, isroutine

from key import Key
from text_window import TextWindow


class CommandWindow(TextWindow):
    """Class representing the command window for running commands, displaying results,
    and executing code.
    """
    def __init__(self, editor):
        """Initialize a CommandWindow object.

        Args:
            editor: Editor object to which the window belongs.
        """
        super().__init__(editor, editor._ui.max_lines-1, 0, 1, editor._ui.max_columns)

        self._scope = self._build_scope(lambda: self._editor.window_current.buffer)
        self._scope.update(self._build_scope(lambda: self._editor.window_current))
        self._scope.update(self._build_scope(lambda: self._editor))
        # self._scope.update(self._build_scope(lambda: self))

        self.key_bindings[Key('C-j')] = lambda: [self.evaluate(), self._editor.command_window_toggle()]

    def _build_scope(self, get_instance):
        """Build a scope (dictionary) with wrappers of the public methods and properties
        contained in the class of the object returned by get_instance.

        Wrappers in the scope call get_instance to get the value of self.

        Args:
            get_instance: Function returning the instance to be used as self.

        Returns:
            Dictionary containing the built scope.
        """
        obj = get_instance()
        cls = type(obj)

        methods = {n: x for (n, x) in getmembers(cls) if n[0] != '_' and isroutine(x)}
        scope = {n: update_wrapper(partial(self._method, get_instance, f), f) for (n, f) in methods.items()}

        functions = {n: x for (n, x) in getmembers(obj) if n[0] != '_' and isfunction(x)}
        scope.update(functions)

        properties = {n: x for (n, x) in getmembers(cls) if n[0] != '_' and isdatadescriptor(x)}
        scope.update({n: update_wrapper(partial(self._get_set, get_instance, p), p) for (n, p) in properties.items()})

        return scope

    @staticmethod
    def _method(get_instance, method, *args, **kwargs):
        """Wrapper to methods. Call the method using the result of get_instance
        as the parameter self, and *args, **kwargs as the other arguments.

        Args:
            get_instance: Function returning the instance to be used as self.
            method: Method of the class to call.
            *args, **kwargs: Arguments for the method.

        Returns:
            Whatever method returns.
        """
        return method(get_instance(), *args, **kwargs)

    @staticmethod
    def _get_set(get_instance, descriptor, *args):
        """Wrapper to properties. If called with no *args, acts as a getter,
        otherwise as a setter (with *args as the new value).

        Args:
            get_instance: Function returning the instance to be used as self.
            descriptor: Descriptor of the property.
            *args: None for getter, new value for setter.

        Returns:
            None if setting, value of the property if getting.
        """
        if args:
            descriptor.fset(get_instance(), args[0] if len(args) == 1 else args)
        else:
            return descriptor.fget(get_instance())

    @staticmethod
    def help(x):
        """Return the docstring of an object.

        Args:
            x: The object.

        Returns:
            x's docstring.
        """
        return x.__doc__

    def evaluate(self):
        """Evaluate the content of the command window as Python code.
        Shows the output on the command window itself.
        """
        # try:
        try:
            result = eval(self._buffer.content, self._scope, globals())
            self._buffer.content = '' if (result is None) else str(result)
        except SyntaxError:
            exec(self._buffer.content, self._scope, globals())
            self._buffer.content = ''
        # except Exception as exception:
        #     self._buffer.content = str(exception)

        self.cursor_end()
