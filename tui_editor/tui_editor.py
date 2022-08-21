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
        self.show_line_numbers = False
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
        self._content = lines.copy() or [""]
        if self.tty.initialized:
            self.update_screen()

    def set_text(self, text: str):
        """set editor text"""
        self.set_text_lines(text.split("\n"))

    def get_text_lines(self):
        """get editor text"""
        return self._content.copy()

    def get_text(self) -> str:
        """get editor text"""
        return "\n".join(self._content)

    def set_status_lines(self, lines: list[str]):
        """set status bar"""
        self._status_content = lines.copy() or [""]
        if self.tty.initialized:
            self.update_screen_status()

    def set_cursor_pos(self, line: int, col: int = 0):
        """
        Set the cursor position (row/col), by line/col
        """
        if self.top_line_idx > line or self.top_line_idx + self.actual_height <= line:
            self.top_line_idx = max(line - self.actual_height // 2, 0)
        self.row = line - self.top_line_idx
        self.col = col
        if self.tty.initialized:
            self.update_screen()

    def set_cursor(self):
        """set the cursor back to the editor pos"""
        width = self.tty.width
        col = self.col
        if self.show_line_numbers:
            col += len(str(self.total_lines)) + 2
        while col >= width - 1:
            col -= width // 3  # see _show_content_line
        self.tty.goto(self.row, col)

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
        assert self.tty.initialized
        while True:
            buf = os.read(self.tty.fd_in, 32)
            if buf and buf[:1] not in b"\x1b\x7f" and buf[0] > 31:
                try:
                    buf = buf.decode("utf8")
                except UnicodeDecodeError:
                    pass
            sz = len(buf)
            i = 0
            while i < sz:
                if isinstance(buf, bytes) and buf[0] == 0x1b:
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
        assert self.tty.initialized
        self.tty.cursor(False)
        self.tty.goto(0, 0)
        self.tty.write(self.content_prefix_escape)
        i = self.top_line_idx
        for c in range(self.height):
            self._show_content_line(i)
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
        assert self.tty.initialized
        if goto:
            self.tty.cursor(False)
            self.tty.goto(self.actual_height, 0)
            self.tty.update_occupied_space()
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

    def update_line(self, *, margin_logic_cur_line=True):
        """
        Update just the current line, assuming that the cursor is in the right line.
        """
        self.tty.cursor(False)
        self.tty.write(b"\r")
        self.tty.write(self.content_prefix_escape)
        self._show_content_line(self.cur_line_idx, margin_logic_cur_line=margin_logic_cur_line)
        self.set_cursor()
        self.tty.cursor(True)

    def _maybe_update_line_after_cursor_change(self, *, is_old_line=False):
        self.set_cursor()
        line = self._content[self.cur_line_idx]
        width = self.tty.width
        if self.show_line_numbers:
            width -= len(str(self.total_lines)) + 2
        if len(line) >= width:
            self.update_line(margin_logic_cur_line=not is_old_line)
            return True
        return False

    def _show_content_line(self, line_idx: int, *, margin_logic_cur_line=True):
        self._show_line_number(line_idx)
        line = self._content[line_idx]
        if margin_logic_cur_line and line_idx == self.cur_line_idx:
            width = self.tty.width
            col = self.col
            if self.show_line_numbers:
                col += len(str(self.total_lines)) + 2
            while col >= width - 1:  # keep consistent to set_cursor
                col -= width // 3
                line = line[width // 3:]
        self._show_line(line)

    def _show_line_number(self, line_idx: int = None):
        if not self.show_line_numbers:
            return
        if line_idx is None:
            line_idx = self.cur_line_idx
        s = str(line_idx + 1)
        s = " " * (len(str(self.total_lines)) - len(s)) + s + "| "
        self.tty.write(s.encode("utf8"))

    def _show_line(self, line: str):
        self.tty.write(line.encode("utf8"))
        self.tty.clear_to_eol()

    def _move_cursor_next_line(self, *, update=True):
        self._maybe_update_line_after_cursor_change(is_old_line=True)
        if self.row + 1 == self.height:
            self.top_line_idx += 1
            self.adjust_cursor_eol()
            if update:
                self.update_screen()
            return True
        else:
            self.row += 1
            self.adjust_cursor_eol()
            if update:
                self._maybe_update_line_after_cursor_change()
            return False

    def _move_cursor_prev_line(self, *, update=True):
        self._maybe_update_line_after_cursor_change(is_old_line=True)
        if self.row == 0:
            if self.top_line_idx > 0:
                self.top_line_idx -= 1
                self.adjust_cursor_eol()
                if update:
                    self.update_screen()
                return True
            return False
        else:
            self.row -= 1
            self.adjust_cursor_eol()
            if update:
                self._maybe_update_line_after_cursor_change()
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
                self._move_cursor_next_line()
        elif key == KEY_UP:
            if self.cur_line_idx > 0:
                self._move_cursor_prev_line()
        elif key == KEY_LEFT:
            if self.col > 0:
                self.col -= 1
                self._maybe_update_line_after_cursor_change()
            elif self.cur_line_idx > 0:
                self.col = len(self._content[self.cur_line_idx - 1])
                self._move_cursor_prev_line()
        elif key == KEY_RIGHT:
            if self.col < len(self._content[self.cur_line_idx]):
                self.col += 1
                self._maybe_update_line_after_cursor_change()
            elif self.cur_line_idx < len(self._content) - 1:
                self.col = 0
                self._move_cursor_next_line()
        elif key == KEY_HOME:
            self.col = 0
            self._maybe_update_line_after_cursor_change()
        elif key == KEY_END:
            self.col = len(self._content[self.cur_line_idx])
            self._maybe_update_line_after_cursor_change()
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

    def handle_key(self, key: Union[bytes, str, int]):
        """
        Handle potential edit key and update screen.
        Assumes the cursor is at the right position.
        """
        cur_line = self._content[self.cur_line_idx]
        if key == KEY_ENTER:
            self._content[self.cur_line_idx] = cur_line[:self.col]
            self._content.insert(self.cur_line_idx + 1, cur_line[self.col:])
            self.col = 0
            self._move_cursor_next_line(update=False)
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
                self.tty.update_occupied_space()  # actual height might have decreased
                self.update_screen()
        elif key == KEY_DELETE:
            if self.col < len(cur_line):
                cur_line = cur_line[:self.col] + cur_line[self.col + 1:]
                self._content[self.cur_line_idx] = cur_line
                self.update_line()
            elif self.col == len(cur_line) and self.cur_line_idx < len(self._content) - 1:
                self._content[self.cur_line_idx] += self._content[self.cur_line_idx + 1]
                self._content.pop(self.cur_line_idx + 1)
                self.tty.update_occupied_space()  # actual height might have decreased
                self.update_screen()
        elif isinstance(key, int):
            return
        elif isinstance(key, bytes) and key[0] == 0x1b:
            return
        elif len(key) == 1 and ord(key) <= 31:  # other control char
            return
        elif isinstance(key, str):
            cur_line = cur_line[:self.col] + key + cur_line[self.col:]
            self._content[self.cur_line_idx] = cur_line
            self.col += 1
            self.update_line()
        self.on_edit()

    def on_key(self, key: Union[bytes, str, int]) -> Union[bool, None]:
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
