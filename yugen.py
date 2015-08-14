#!/usr/bin/env python3
"""Subtly profound text editor."""


import curses
from curses import ascii
from curses.ascii import ctrl


class Screen:
    """Abstraction of the whole screen."""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.init_curses()
        self.init_border()

        self.cmdline = CommandWindow(self, 1, curses.COLS, curses.LINES-1, 0)
        self.main = TextWindow(self, curses.LINES-2, curses.COLS, 0, 0)

        self.main.loop()

    @staticmethod
    def init_curses():
        """Initialize curses modes and colors."""
        curses.raw()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

    def init_border(self):
        """Draw the command window border"""
        self.stdscr.hline(curses.LINES - 2, 0, curses.ACS_HLINE, curses.COLS)
        self.stdscr.refresh()


class Window:
    """Generic text editing window."""
    def __init__(self, screen, height, width, y, x, borders=(0, 0), content=''):
        self.screen = screen
        self.window = self.screen.stdscr.subwin(height, width, y, x)
        self.window.keypad(True)
        self.borders = borders

        self.content = content.split('\n')
        self.reload()

        self.reading = True
        self.scope = globals()
        self.scope.update({n: eval('s.'+n, {'s': self}) for n in dir(self)})

    def coords(self):
        """Return positions in the window y, x and positions in the buffer row, col."""
        y, x = self.window.getyx()
        row, col = (y - self.borders[0], x - self.borders[1])
        return y, x, row, col

    def reload(self):
        """Reload the buffer into the window."""
        self.window.clear()
        for y, line in enumerate(self.content):
            self.window.insstr(self.borders[0] + y, self.borders[1], line)
        self.window.move(*self.borders)

    def write(self, c):
        """Insert a character where the cursor is."""
        y, x, row, col = self.coords()

        # Put the character in the current cursor position:
        self.window.addch(y, x, c)
        # If there were other character ahead in the same line:
        if col < len(self.content[row]):
            # Reinsert the overwritten one and shift the others forward:
            self.window.insch(self.content[row][col])
        # Update the buffer by adding the character in the middle:
        self.content[row] = self.content[row][:col] + chr(c) + self.content[row][col:]

    def write_newline(self):
        """Insert a newline where the cursor is."""
        y, x, row, col = self.coords()

        self.window.addch(y, x, ascii.NL)  # Newline (overwrite next characters).
        self.window.insertln()             # Create a blank line below, push back everything.
        # Write all the characters that were left in the first line and we overwrote:
        self.window.insstr(y+1, self.borders[1], self.content[row][col:])
        # Update the buffer (basically split the line in two):
        self.content[row: row+1] = [self.content[row][:col], self.content[row][col:]]

    def move_horizontal(self, d):
        """Move the cursor left (d = -1) or right (d = 1), adjusting the vertical position if needed."""
        y, x, row, col = self.coords()

        # If there are still characters where to go horizontally:
        if (d == -1 and col > 0) or (d == 1 and col < len(self.content[row])):
            self.window.move(y, x + d)
        # Otherwise we have to move vertically, if possible:
        elif (d == -1 and row > 0) or (d == 1 and row+1 < len(self.content)):
            # Last character horizontally if moving left, first one if moving right:
            self.window.move(y + d, self.borders[1] + (0 if d == 1 else len(self.content[row + d])))

    def delete(self):
        """Delete the character immediately before the cursor."""
        y, x, row, col = self.coords()

        # If there are characters to delete horizontally:
        if col > 0:
            self.move_horizontal(-1)  # Move left.
            self.window.delch()       # Delete the char.
            self.content[row] = self.content[row][:col-1] + self.content[row][col:]
        # Else remove vertically, if possibile:
        elif row > 0:
            self.window.deleteln()    # Delete the current line.
            self.move_horizontal(-1)  # Move up, end of previous line.
            # Write the line we deleted at the end of the previous one:
            self.window.insstr(y-1, len(self.content[row-1]), self.content[row])
            self.content[row-1: row+1] = [self.content[row-1] + self.content[row]]

    def switch_command(self, k, c):
        """Choose the action to perform based on the pressed key.
           Override to extend key-bindings."""
        if ascii.isprint(k):          # Printable character.
            self.write(k)
        elif k == ascii.NL:           # Newline.
            self.write_newline()
        elif k == ascii.DEL:          # Backspace.
            self.delete()

        elif k == curses.KEY_LEFT:    # One character back.
            self.move_horizontal(-1)
        elif k == curses.KEY_RIGHT:   # One character forward.
            self.move_horizontal(1)

        # ALT group:
        elif k == ascii.ESC:
            if c == ord('q'):             # ALT-q -> Quit.
                quit()
            elif c == ord('j'):           # ALT-j -> One character back.
                self.move_horizontal(-1)
            elif c == ord('l'):           # ALT-l -> One character forward.
                self.move_horizontal(1)

    def loop(self):
        """Start the window's interaction loop."""
        while self.reading:
            self.window.refresh()

            k = self.window.getch()
            c = self.window.getch() if (k == ascii.ESC) else None

            self.switch_command(k, c)


class TextWindow(Window):
    """Text editing window, for savable buffers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmdline = self.screen.cmdline

    def save_file(self):
        """Prompt in minibuffer for the name of the file where to save."""
        def save_file_callback(file_name):
            open(file_name, 'w').write('\n'.join(self.content))
            return file_name
        self.cmdline.prompt('Save as: ', "Saved as '{}'.", save_file_callback)

    def evaluate(self):
        """Prompt in minibuffer for a Python expression to evaluate."""
        self.cmdline.prompt('Eval: ', '{}', lambda x: eval(x, self.scope))

    def execute(self):
        """Prompt in minibuffer for Python code to execute."""
        self.cmdline.prompt('Exec: ', 'OK.', lambda x: exec(x, self.scope))

    def switch_command(self, k, c):
        super().switch_command(k, c)

        # CTRL group:
        if k == ctrl(ord('c')):    # CTRL-c -> Clear command line.
            self.cmdline.clear()
        elif k == ctrl(ord('s')):  # CTRL-s -> Save file as...
            self.save_file()

        # ALT group:
        elif k == ascii.ESC:
            if c == ord('e'):      # ALT-e -> Evaluate expression...
                self.evaluate()
            elif c == ord('x'):    # ALT-x -> Execute code...
                self.execute()


class CommandWindow(Window):
    """Small text window to insert commands."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timer = None

    def write_newline(self):
        """Newlines in CommandWindow launch the command."""
        self.reading = False

    def clear(self):
        """Clear the command line."""
        self.window.deleteln()
        self.window.refresh()

    def prompt(self, question, answer, action):
        """Get user input by showing a question, then perform
           an action for the caller and show the result as a
           formatted input inside answer."""
        # Show the question, arrange the borders and read the input:
        self.window.addstr(0, 0, question, curses.A_BOLD)
        self.borders = (0, len(question))

        self.reading = True
        self.loop()

        # If any input was read:
        if self.content[0]:
            self.window.deleteln()
            # Show the resulting message:
            try:
                self.window.addstr(0, 0, answer.format(action(self.content[0])), curses.color_pair(2))
            except Exception as err:
                self.window.addstr(0, 0, str(err), curses.color_pair(1))

            self.window.refresh()
            self.content = ['']
        else:
            self.clear()

    def switch_command(self, k, c):
        super().switch_command(k, c)

        # CTRL group:
        if k == ctrl(ord('c')):   # CTRL-c -> Quit insertion.
            self.content = ['']
            self.reading = False


if __name__ == '__main__':
    curses.wrapper(Screen)
