#!/usr/bin/env python3
"""Subtly profound text editor."""


import curses
import curses.ascii
from threading import Timer


def main(stdscr):
    """Get the ball rolling."""
    global mini_window

    curses.raw()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)

    stdscr.hline(curses.LINES - 2, 0, curses.ACS_HLINE, curses.COLS)
    stdscr.refresh()

    mini_window = MiniWindow(stdscr)
    TextWindow(stdscr, curses.LINES - 2, curses.COLS, 0, 0, (0, 3)).loop()


class Window:
    """Autonomous text editing window."""
    def __init__(self, parent, height, width, y, x, borders=(0, 0), content=''):
        self.parent = parent
        self.window = parent.subwin(height, width, y, x)
        self.borders = borders
        self.window.move(borders[0], borders[1])
        self.window.keypad(1)
        self.content = content.split('\n')

        self.reading = True
        self.scope = globals()
        self.scope.update({n: eval('s.'+n, {'s': self}) for n in dir(self)})

    def coords(self):
        y, x = self.window.getyx()
        row, col = (y + self.borders[0], x + self.borders[1])
        return y, x, row, col

    def write(self, c):
        """Insert a character where the cursor is."""
        y, x, row, col = self.coords()

        self.window.addch(y, x, c)
        if col < len(self.content[row]):
            self.window.insch(self.content[row][col])

        self.content[row] = self.content[row][:col] + chr(c) + self.content[row][col:]

    def write_newline(self):
        """Insert a newline where the cursor is."""
        y, x, row, col = self.coords()

        self.window.addch(y, x, curses.ascii.NL)
        self.window.insertln()
        self.window.insstr(y+1, self.borders[1], self.content[row][col:])

        self.content[row: row+1] = [self.content[row][:col], self.content[row][col:]]

    def move_horizontal(self, d):
        """Move the cursor left (d = -1) or right (d = 1), adjusting the vertical position if needed."""
        y, x, row, col = self.coords()

        if (d == -1 and col > 0) or (d == 1 and col < len(self.content[row])):
            self.window.move(y, x + d)
        elif (d == -1 and row > 0) or (d == 1 and row+1 < len(self.content)):
            self.window.move(y + d, len(self.content[row + d]))

    def delete(self):
        """Delete the character immediately before the cursor."""
        y, x, row, col = self.coords()

        self.move_horizontal(-1)
        if col > 0:
            self.content[row] = self.content[row][:col-1] + self.content[row][col:]
            self.window.delch()
        elif row > 0:
            self.content[row-1: row+1] = [self.content[row-1] + self.content[row]]

    def save_file(self):
        """Prompt in minibuffer for the name of the file where to save."""
        def save_file_callback(file_name):
            open(file_name, 'w').write('\n'.join(self.content))
            return file_name
        mini_window.prompt(self, 'Save as:  ', "Saved as '{}'.", save_file_callback)

    def evaluate(self):
        """Prompt in minibuffer for a Python expression to evaluate."""
        mini_window.prompt(self, 'Evaluate:  ', '{}', lambda x: eval(x, self.scope))

    def execute(self):
        """Prompt in minibuffer for Python code to execute."""
        mini_window.prompt(self, 'Execute:  ', 'OK.', lambda x: exec(x, self.scope))

    def switch_command(self, k, c):
        if curses.ascii.isprint(k):   # Printable character.
            self.write(k)
        elif k == curses.ascii.NL:    # Newline.
            self.write_newline()
        elif k == curses.ascii.DEL:   # Backspace.
            self.delete()

        elif k == curses.KEY_LEFT:    # Left arrow.
            self.move_horizontal(-1)
        elif k == curses.KEY_RIGHT:   # Right arrow.
            self.move_horizontal(1)

        # ALT group:
        elif k == curses.ascii.ESC:
            if c == ord('q'):         # ALT-q -> Quit.
                exit()

    def loop(self):
        """Start the window's interaction loop."""
        while self.reading:
            self.window.refresh()

            k = self.window.getch()
            c = self.window.getch() if (k == curses.ascii.ESC) else None

            self.switch_command(k, c)


class TextWindow(Window):
    def switch_command(self, k, c):
        super().switch_command(k, c)
        # ALT group:
        if k == curses.ascii.ESC:
            if c == ord('s'):      # ALT-s -> Save file as...
                self.save_file()
            elif c == ord('e'):    # ALT-e -> Evaluate expression...
                self.evaluate()
            elif c == ord('x'):    # ALT-x -> Execute code...
                self.execute()


class MiniWindow(Window):
    def __init__(self, parent):
        super().__init__(parent, 1, curses.COLS, curses.LINES - 1, 0)
        self.timer = None

    def write_newline(self):
        self.reading = False

    def prompt(self, caller, question, answer, action):
        def clear():
            y, x = caller.window.getyx()
            self.window.deleteln()
            self.window.refresh()
            caller.window.move(y, x)
            caller.window.refresh()

        if self.timer:
            self.timer.cancel()
            clear()

        self.window.addstr(0, 0, question, curses.color_pair(1))
        self.borders = (0, len(question))
        self.reading = True
        self.loop()

        if self.content[0]:
            try:
                message = answer.format(action(self.content[0]))
            except Exception as err:
                message = str(err)

            self.window.deleteln()
            self.window.addstr(0, 0, message, curses.color_pair(1))
            self.window.refresh()

            self.timer = Timer(3.0, lambda: clear())
            self.timer.start()
            self.content = ['']
        else:
            clear()

    def switch_command(self, k, c):
        super().switch_command(k, c)
        # CTRL group:
        if k == curses.ascii.ctrl(ord('c')):  # CTRL-c -> Quit insertion.
            self.content = ['']
            self.reading = False


if __name__ == '__main__':
    curses.wrapper(main)
