"""
TTY helpers
"""

# https://en.wikipedia.org/wiki/ANSI_escape_code
# https://invisible-island.net/xterm/ctlseqs/ctlseqs.html

from __future__ import annotations
from typing import Callable
import os
import re
import tty
import termios
import signal


class TtyController:
    """TTY controller"""

    def __init__(self, *,
                 fd_in: int = 0,
                 fd_out: int = 1,
                 total_height: Callable[[], int],  # for reserving space
                 update_screen: Callable[[], None],  # called on resize
                 ):
        self.fd_in = fd_in
        self.fd_out = fd_out
        self.row = 0
        self.col = 0
        self.screen_top = 0
        self.width = os.get_terminal_size(self.fd_out).columns
        self.prev_total_height = 1  # assume we are already in a new line
        self.total_height = total_height
        self.update_screen = update_screen
        self._orig_termios = None
        self._orig_sig_win_ch = None
        self.initialized = False

    def init_tty(self):
        """init raw TTY mode, reserve space (via total_height)"""
        self._orig_termios = termios.tcgetattr(self.fd_in)
        tty.setraw(self.fd_in)
        self.initialized = True
        self.write(b"\x1b[?7l")  # No Auto-Wrap Mode (DECAWM)

        # make enough space
        # assuming nothing has been printed yet
        self.update_occupied_space()

        def _on_resize(_signum, _frame):
            self._update_editor_row_offset()
            self.width = os.get_terminal_size(self.fd_out).columns
            # If the colum size changed, and this wraps around existing text,
            # this is not handled correctly yet...
            # Updating the screen might be a good idea anyway.
            self.update_screen()

        self._orig_sig_win_ch = signal.getsignal(signal.SIGWINCH)
        signal.signal(signal.SIGWINCH, _on_resize)

    def deinit_tty(self, clear_editor=True):
        """resets the tty to normal (non-raw) mode, recovering the original state before init_tty"""
        self.write(b"\x1b[0m")
        self.write(b"\x1b[?7h")  # Auto-Wrap Mode (DECAWM)
        num_lines = self.total_height()
        if clear_editor:
            self.goto(0, 0)
            self.write(b"\x1b[%iM" % num_lines)
        else:
            # Don't leave cursor in the middle of screen
            self.goto(num_lines - 1, 0)
            self.write(b"\r\n")
        termios.tcsetattr(self.fd_in, termios.TCSANOW, self._orig_termios)
        signal.signal(signal.SIGWINCH, self._orig_sig_win_ch)
        self.initialized = False

    def write(self, s: bytes):
        """raw write"""
        assert isinstance(s, bytes)
        os.write(self.fd_out, s)

    def cls(self):
        """clear screen"""
        self.write(b"\x1b[2J")

    def goto(self, row: int, col: int):
        """change cursor position (relative to screen top)"""
        self.write(b"\x1b[%d;%dH" % (row + 1 + self.screen_top, col + 1))
        self.row = row
        self.col = col

    def get_cursor_pos_abs(self) -> (int, int):
        """get absolute cursor position"""
        self.write(b"\x1b[6n")
        s = b""
        while True:
            s += os.read(self.fd_in, 1)
            if s[-1:] == b"R":
                break
            if s[-1:] == b"\x03":
                raise KeyboardInterrupt
        res = re.match(rb".*\[(?P<y>\d*);(?P<x>\d*)R", s)
        row, col = res.groups()
        return int(row) - 1, int(col) - 1

    def clear_to_eol(self):
        """clear to end of line"""
        self.write(b"\x1b[0K")

    def cursor(self, enabled: bool):
        """show or hide cursor"""
        if enabled:
            self.write(b"\x1b[?25h")
        else:
            self.write(b"\x1b[?25l")

    def _update_editor_row_offset(self):
        row, col = self.get_cursor_pos_abs()
        expected_row = self.screen_top + self.row
        self.screen_top += row - expected_row

    def update_occupied_space(self):
        """
        Update occupied space.
        When new lines are added, they are always added at the end.
        When lines are deleted, they are deleted at the current cursor.
        The cursor row stays the same.
        """
        total_height = self.total_height()
        assert total_height > 0 and self.prev_total_height > 0
        if total_height == self.prev_total_height:
            return

        self.cursor(False)
        self.write(b"\r\x1b[0m")
        prev_row = self.row
        if total_height > self.prev_total_height:
            if self.row != self.prev_total_height - 1:
                self.goto(self.prev_total_height - 1, 0)
            num_lines = total_height - self.prev_total_height
            self.write(b"\n" * num_lines)
            self.row = total_height - 1
            self._update_editor_row_offset()
            self.goto(prev_row, 0)
        elif total_height < self.prev_total_height:
            num_lines = self.prev_total_height - total_height
            self.write(b"\x1b[%iM" % num_lines)  # delete lines
        self.prev_total_height = total_height


KEY_UP = 1
KEY_DOWN = 2
KEY_LEFT = 3
KEY_RIGHT = 4
KEY_HOME = 5
KEY_END = 6
KEY_PGUP = 7
KEY_PGDN = 8
KEY_ENTER = 10
KEY_BACKSPACE = 11
KEY_DELETE = 12

KEYMAP = {
    b"\x1b[A": KEY_UP,
    b"\x1b[B": KEY_DOWN,
    b"\x1b[D": KEY_LEFT,
    b"\x1b[C": KEY_RIGHT,
    b"\x1bOH": KEY_HOME,
    b"\x1bOF": KEY_END,
    b"\x1bb": KEY_HOME,
    b"\x1bf": KEY_END,
    b"\x1b[1~": KEY_HOME,
    b"\x1b[4~": KEY_END,
    b"\x1b[5~": KEY_PGUP,
    b"\x1b[6~": KEY_PGDN,
    b"\r": KEY_ENTER,
    b"\x7f": KEY_BACKSPACE,
    b"\x1b[3~": KEY_DELETE,
}
