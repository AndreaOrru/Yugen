#!/usr/bin/env python3
"""Yugen, the subtly profound text editor."""

import curses
from editor import Editor


if __name__ == '__main__':
    def main(stdscr):
        editor = Editor(Curses(stdscr))
        editor.run()
    curses.wrapper(main)
