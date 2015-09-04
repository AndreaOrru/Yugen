#!/usr/bin/env python3
"""Yugen, the subtly profound text editor."""

import curses
from editor import Editor
from ui_curses import Curses


if __name__ == '__main__':
    def main(stdscr):
        editor = Editor(Curses(stdscr))
        editor._run()
    curses.wrapper(main)
