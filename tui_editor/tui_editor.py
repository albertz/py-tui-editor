"""
Simple TUI editor
"""

# Original code:
# https://github.com/pfalcon/picotui/blob/master/seditor.py
#
# Very simple VT100 terminal text editor widget
# Copyright (c) 2015 Paul Sokolovsky, (c) 2022 Albert Zeyer
# Distributed under MIT License

# https://en.wikipedia.org/wiki/ANSI_escape_code
# https://invisible-island.net/xterm/ctlseqs/ctlseqs.html

from __future__ import annotations
from typing import Optional, Union
from .tty_helpers import *


class TuiEditor:
    """TUI editor"""

    def __init__(self, *,
                 control_key_abort: Optional[str] = "C",  # raises KeyboardInterrupt
                 control_key_quit: Optional[str] = "S",  # normal quit
                 ):
        self.top_line_idx = 0
        self.row = 0
        self.col = 0
        self.height = 10  # lines for editor only, excluding status bars
        self._orig_termios = None
        self._orig_sig_win_ch = None
        self.content_prefix_escape = b"\x1b[30;106m"
        self.status_prefix_escape = b"\x1b[30;102m"
        self._content = [""]
        self._status_content = [""]
        self._control_key_abort = _control_key(control_key_abort)
        self._control_key_quit = _control_key(control_key_quit)
        self.tty = TtyController(
            total_height=lambda: self.actual_height + len(self._status_content),
            update_screen=self.update_screen,
        )

    def edit(self):
        """enter raw tty, enter loop, and exit raw tty at the end"""
        self.tty.init_tty()
        try:
            self.update_screen()
            self.loop()
        finally:
            self.tty.deinit_tty()

    def set_text_lines(self, lines: list[str]):
        """set editor text"""
        self._content = lines or [""]

    def set_text(self, text: str):
        """set editor text"""
        self._content = text.split("\n")

    def get_text_lines(self):
        """get editor text"""
        return self._content

    def get_text(self) -> str:
        """get editor text"""
        return "\n".join(self._content)

    def set_status_lines(self, lines: list[str]):
        """set status bar"""
        assert self._status_content
        lines = lines or [""]
        prev_lines = self._status_content
        self._status_content = lines
        # assume we have already drawn the screen before
        if len(lines) != len(prev_lines):
            self.tty.cursor(False)
            self.tty.goto(self.actual_height, 0)
            self.tty.update_occupied_space()
        self.update_screen_status()

    def set_cursor(self):
        """set the cursor back to the editor pos"""
        self.tty.goto(self.row, self.col)

    def adjust_cursor_eol(self):
        """when the cur line changed, potentially fix cursor pos col"""
        cur_line_len = len(self._content[self.cur_line_idx])
        if self.col > cur_line_len:
            self.col = cur_line_len

    @property
    def total_lines(self):
        """total number of text lines (potentially not all are visible)"""
        return len(self._content)

    @property
    def cur_line_idx(self) -> int:
        """cursor line index"""
        return self.top_line_idx + self.row

    def loop(self):
        """main loop, reading user inputs"""
        while True:
            buf = os.read(self.tty.fd_in, 32)
            sz = len(buf)
            i = 0
            while i < sz:
                if buf[0] == 0x1b:
                    key = buf
                    i = len(buf)
                else:
                    key = buf[i:i + 1]
                    i += 1
                if key in KEYMAP:
                    key = KEYMAP[key]
                if self.on_key(key):
                    continue
                if key == self._control_key_abort:
                    raise KeyboardInterrupt
                if key == self._control_key_quit:
                    return
                if self.handle_cursor_keys(key):
                    self.on_cursor_pos_change()
                    continue
                self.handle_key(key)
                self.on_cursor_pos_change()

    def update_screen(self):
        """update the screen, i.e. editor and status bar(s)"""
        self.tty.cursor(False)
        self.tty.goto(0, 0)
        self.tty.write(self.content_prefix_escape)
        i = self.top_line_idx
        for c in range(self.height):
            self._show_line(self._content[i])
            self.tty.write(b"\r\n")
            i += 1
            if i == self.total_lines:
                break
        self.update_screen_status(goto=False)
        self.set_cursor()
        self.tty.cursor(True)

    @property
    def actual_height(self) -> int:
        """actual height of editor (excluding status bars)"""
        return min(self.height, self.total_lines)

    def update_screen_status(self, *, goto=True):
        """
        Update the screen status bar(s).

        :param goto: set the cursor ot the status bar, and then back to the editor
        """
        if goto:
            self.tty.cursor(False)
            self.tty.goto(self.actual_height, 0)
        self.tty.write(self.status_prefix_escape)
        assert self._status_content
        for c, line in enumerate(self._status_content):
            if c > 0:
                self.tty.write(b"\n")
            self._show_line(line)
            self.tty.write(b"\r")
        self.tty.write(b"\x1b[0m")
        if goto:
            self.set_cursor()
            self.tty.cursor(True)

    def update_line(self):
        """
        Update just the current line, assuming that the cursor is in the right line.
        """
        self.tty.cursor(False)
        self.tty.write(b"\r")
        self.tty.write(self.content_prefix_escape)
        self._show_line(self._content[self.cur_line_idx])
        self.set_cursor()
        self.tty.cursor(True)

    def _show_line(self, line: str):
        self.tty.write(line.encode("utf8"))
        self.tty.clear_to_eol()

    def _move_cursor_next_line(self):
        if self.row + 1 == self.height:
            self.top_line_idx += 1
            self.adjust_cursor_eol()
            return True
        else:
            self.row += 1
            self.adjust_cursor_eol()
            return False

    def _move_cursor_prev_line(self):
        if self.row == 0:
            if self.top_line_idx > 0:
                self.top_line_idx -= 1
                self.adjust_cursor_eol()
                return True
            return False
        else:
            self.row -= 1
            self.adjust_cursor_eol()
            return False

    def handle_cursor_keys(self, key):
        """
        Handle potential cursor-position-manipulating key,
        potentially updating the cursor position
        and potentially updating the screen.

        :return: True, if we consumed the event, and it should not be handled further
        """
        if key == KEY_DOWN:
            if self.cur_line_idx + 1 != self.total_lines:
                if self._move_cursor_next_line():
                    self.update_screen()
                else:
                    self.set_cursor()
        elif key == KEY_UP:
            if self.cur_line_idx > 0:
                if self._move_cursor_prev_line():
                    self.update_screen()
                else:
                    self.set_cursor()
        elif key == KEY_LEFT:
            if self.col > 0:
                self.col -= 1
                self.set_cursor()
        elif key == KEY_RIGHT:
            self.col += 1
            self.adjust_cursor_eol()
            self.set_cursor()
        elif key == KEY_HOME:
            self.col = 0
            self.set_cursor()
        elif key == KEY_END:
            self.col = len(self._content[self.cur_line_idx])
            self.set_cursor()
        elif key == KEY_PGUP:
            self.top_line_idx -= self.height
            if self.top_line_idx < 0:
                self.top_line_idx = 0
                self.row = 0
            elif self.cur_line_idx < 0:
                self.row = 0
            self.adjust_cursor_eol()
            self.update_screen()
        elif key == KEY_PGDN:
            self.top_line_idx += self.height
            if self.cur_line_idx >= self.total_lines:
                self.top_line_idx = self.total_lines - self.height
                if self.top_line_idx >= 0:
                    self.row = self.height - 1
                else:
                    self.top_line_idx = 0
                    self.row = self.cur_line_idx
            self.adjust_cursor_eol()
            self.update_screen()
        else:
            return False
        return True

    def handle_key(self, key: Union[bytes, int]):
        """
        Handle potential edit key and update screen.
        Assumes the cursor is at the right position.
        """
        cur_line = self._content[self.cur_line_idx]
        if key == KEY_ENTER:
            self._content[self.cur_line_idx] = cur_line[:self.col]
            self._content.insert(self.cur_line_idx + 1, cur_line[self.col:])
            self.col = 0
            self._move_cursor_next_line()
            self.tty.update_occupied_space()  # actual height will increase
            self.update_screen()
        elif key == KEY_BACKSPACE:
            if self.col > 0:
                self.col -= 1
                cur_line = cur_line[:self.col] + cur_line[self.col + 1:]
                self._content[self.cur_line_idx] = cur_line
                self.update_line()
            elif self.col == 0 and self.cur_line_idx > 0:
                self.col = len(self._content[self.cur_line_idx - 1])
                self._content[self.cur_line_idx - 1] += self._content[self.cur_line_idx]
                self._content.pop(self.cur_line_idx)
                if self.top_line_idx > 0 and self.top_line_idx + self.height > len(self._content):
                    self.top_line_idx -= 1
                elif self.row > 0:
                    self.row -= 1
                if len(self._content) < self.height:
                    self.tty.write(b"\x1b[0m\x1b[1M")  # delete one line
                self.update_screen()
        elif key == KEY_DELETE:
            cur_line = cur_line[:self.col] + cur_line[self.col + 1:]
            self._content[self.cur_line_idx] = cur_line
            self.update_line()
        elif isinstance(key, int):
            pass
        elif ord(key) <= 31:  # other control char
            pass
        else:
            cur_line = cur_line[:self.col] + str(key, "utf-8") + cur_line[self.col:]
            self._content[self.cur_line_idx] = cur_line
            self.col += 1
            self.update_line()
        self.on_edit()

    def on_key(self, key: Union[bytes, int]) -> Union[bool, None]:
        """
        Called on input key events.

        :param key:
        :return: True -> the function consumed the event, i.e. the event should not be passed on further
        """
        # Overwrite this function if you want.
        pass

    def on_cursor_pos_change(self):
        """
        Called on (potential) cursor position changes.
        """
        # Overwrite this function if you want.
        pass

    def on_edit(self):
        """
        Called on (potential) edits.
        """
        # Overwrite this function if you want.
        pass


def _control_key(key: Optional[str]) -> Optional[bytes]:
    if not key:
        return None
    key = key.upper()
    assert ord("A") <= ord(key) <= ord("Z"), f"invalid control key {key!r}, should be in range A-Z"
    return bytes([ord(key) - ord("A") + 1])
