#!/usr/bin/env python3

import curses
import curses.ascii
from threading import Timer


class Window:
    """Autonomous editing window."""
    def __init__(self, window, content=''):
        self.window = window
        self.content = content.split('\n')
        self.max_y, self.max_x = self.window.getmaxyx()
        self.timer = None
        self.scope = {n: eval('s.'+n, {'s': self}) for n in dir(self) if n[:2] != '__'}

    def clear_line(self, y):
        """Clear a line in the window only, preserving the cursor position."""
        save_y, save_x = self.window.getyx()
        self.window.move(y, 0)
        self.window.clrtoeol()
        self.window.move(save_y, save_x)

    def write(self, c):
        """Insert a character where the cursor is."""
        y, x = self.window.getyx()

        self.window.addch(y, x, c)
        if x < len(self.content[y]):
            self.window.insch(self.content[y][x])

        self.content[y] = self.content[y][:x] + chr(c) + self.content[y][x:]

    def write_newline(self):
        """Insert a newline where the cursor is."""
        y, x = self.window.getyx()

        self.window.addch(y, x, curses.ascii.NL)
        self.window.insertln()
        self.window.insstr(self.content[y][x:])

        self.content[y: y+1] = [self.content[y][:x], self.content[y][x:]]

    def move_horizontal(self, d):
        """Move the cursor left (d = -1) or right (d = 1), adjusting the vertical position if needed."""
        y, x = self.window.getyx()

        if (d == -1 and x > 0) or (d == 1 and x < len(self.content[y])):
            self.window.move(y, x + d)
        elif (d == -1 and y > 0) or (d == 1 and y+1 < len(self.content)):
            self.window.move(y + d, len(self.content[y + d]))

    def delete(self):
        """Delete the character immediately before the cursor."""
        y, x = self.window.getyx()

        self.move_horizontal(-1)
        if x > 0:
            self.content[y] = self.content[y][:x-1] + self.content[y][x:]
            self.window.delch()
        elif y > 0:
            self.content[y-1: y+1] = [self.content[y-1] + self.content[y]]

    def prompt(self, question, answer, action):
        """Get user input from the minibuffer with prompt question, and show
           the result of action as a formatted parameter inside answer"""
        if self.timer:
            self.timer.cancel()
        y, x = self.window.getyx()
        minibuffer = self.max_y - 1

        self.clear_line(minibuffer)
        self.window.addstr(minibuffer, 0, question, curses.A_BOLD | curses.color_pair(1))
        curses.echo()
        user_input = self.window.getstr().decode()
        curses.noecho()

        try:
            message = answer.format(action(user_input))
        except Exception as err:
            message = str(err)

        self.window.clrtoeol()
        self.window.addstr(minibuffer, 0, message, curses.A_BOLD | curses.color_pair(1))

        self.timer = Timer(3.0, lambda: self.clear_line(minibuffer))
        self.timer.start()

        self.window.move(y, x)

    def save_file(self):
        """Prompt for the name of the file where to save the buffer."""
        def save_file_callback(file_name):
            open(file_name, 'w').write('\n'.join(self.content))
            return file_name
        self.prompt('Save as:  ', "Saved as '{}'.", save_file_callback)

    def evaluate(self):
        """Prompt for a Python expression to evaluate."""
        self.prompt('Evaluate:  ', '{}', lambda x: eval(x, self.scope))

    def execute(self):
        """Prompt for Python code to execute."""
        self.prompt('Execute:  ', 'OK.', lambda x: exec(x, self.scope))

    def loop(self):
        """Start the window's interaction loop."""
        while True:
            c = self.window.getch()

            if curses.ascii.isprint(c):   # Printable character.
                self.write(c)
            elif c == curses.ascii.NL:    # Newline.
                self.write_newline()
            elif c == curses.ascii.DEL:   # Backspace.
                self.delete()

            elif c == curses.KEY_LEFT:    # Left arrow.
                self.move_horizontal(-1)
            elif c == curses.KEY_RIGHT:   # Right arrow.
                self.move_horizontal(1)

            # ALT group:
            elif c == curses.ascii.ESC:
                c = self.window.getch()
                if c == ord('q'):         # ALT-q -> Quit.
                    break
                elif c == ord('s'):       # ALT-s -> Save file as...
                    self.save_file()
                elif c == ord('e'):       # ALT-e -> Evaluate expression...
                    self.evaluate()
                elif c == ord('x'):       # ALT-x -> Execute code...
                    self.execute()

            self.window.refresh()


def main(stdscr):
    curses.raw()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    Window(stdscr).loop()

curses.wrapper(main)
