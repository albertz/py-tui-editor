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
        self.top_line = 0
        self.row = 0
        self.col = 0
        self.height = 10  # 25
        self._orig_termios = None
        self._orig_sig_win_ch = None
        self.content_prefix_escape = b"\x1b[30;106m"
        self._content = [""]
        self._status_content = [""]
        self._control_key_abort = _control_key(control_key_abort)
        self._control_key_quit = _control_key(control_key_quit)
        self.tty = TtyController(
            total_height=lambda: self.max_visible_height + len(self._status_content),
            update_screen=self.update_screen,
        )

    def edit(self):
        self.tty.init_tty()
        try:
            self.update_screen()
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
        finally:
            self.tty.deinit_tty()

    def set_text_lines(self, lines: list[str]):
        self._content = lines or [""]

    def set_text(self, text: str):
        self._content = text.split("\n")

    def get_text_lines(self):
        return self._content

    def get_text(self) -> str:
        return "\n".join(self._content)

    def set_status_lines(self, lines: list[str]):
        assert self._status_content
        lines = lines or [""]
        # assume we have already drawn the screen before
        if len(lines) < len(self._status_content):
            self.tty.goto(self.max_visible_height, 0)
            self.tty.write(b"\x1b[0m\x1b[%iM" % (len(self._status_content) - len(lines)))
        elif len(lines) > len(self._status_content):
            self.tty.goto(self.max_visible_height, 0)
            self.tty.write(b"\n" * (len(lines) - 1))
            self.tty.update_editor_row_offset(self.max_visible_height + len(lines) - 1)
        self._status_content = lines
        self.update_screen_status()

    def set_cursor(self):
        self.tty.goto(self.row, self.col)

    def adjust_cursor_eol(self):
        l = len(self._content[self.cur_line])
        if self.col > l:
            self.col = l

    @property
    def total_lines(self):
        return len(self._content)

    @property
    def cur_line(self):
        return self.top_line + self.row

    def update_screen(self):
        self.tty.cursor(False)
        self.tty.goto(0, 0)
        self.tty.write(self.content_prefix_escape)
        if self.tty.screen_top == 0:
            self.tty.cls()
        i = self.top_line
        for c in range(self.height):
            self.show_line(self._content[i])
            if self.tty.screen_top > 0:
                self.tty.clear_to_eol()
            self.tty.write(b"\r\n")
            i += 1
            if i == self.total_lines:
                break
        self.update_screen_status(goto=False)
        self.set_cursor()
        self.tty.cursor(True)

    @property
    def max_visible_height(self):
        return min(self.height, self.total_lines)

    def update_screen_status(self, *, goto=True):
        if goto:
            self.tty.cursor(False)
            self.tty.goto(self.max_visible_height, 0)
        self.tty.write(b"\x1b[30;102m")
        assert self._status_content
        for c, line in enumerate(self._status_content):
            if c > 0:
                self.tty.write(b"\n")
            self.show_line(line)
            if self.tty.screen_top > 0:
                self.tty.clear_to_eol()
            self.tty.write(b"\r")
        self.tty.write(b"\x1b[0m")
        if goto:
            self.set_cursor()
            self.tty.cursor(True)

    def update_line(self):
        self.tty.cursor(False)
        self.tty.write(b"\r")
        self.tty.write(self.content_prefix_escape)
        self.show_line(self._content[self.cur_line])
        self.tty.clear_to_eol()
        self.set_cursor()
        self.tty.cursor(True)

    def show_line(self, line: str):
        self.tty.write(line.encode("utf8"))

    def next_line(self):
        if self.row + 1 == self.height:
            self.top_line += 1
            self.adjust_cursor_eol()
            return True
        else:
            self.row += 1
            self.adjust_cursor_eol()
            return False

    def prev_line(self):
        if self.row == 0:
            if self.top_line > 0:
                self.top_line -= 1
                self.adjust_cursor_eol()
                return True
            return False
        else:
            self.row -= 1
            self.adjust_cursor_eol()
            return False

    def handle_cursor_keys(self, key):
        if key == KEY_DOWN:
            if self.cur_line + 1 != self.total_lines:
                if self.next_line():
                    self.update_screen()
                else:
                    self.set_cursor()
        elif key == KEY_UP:
            if self.cur_line > 0:
                if self.prev_line():
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
            self.col = len(self._content[self.cur_line])
            self.set_cursor()
        elif key == KEY_PGUP:
            self.top_line -= self.height
            if self.top_line < 0:
                self.top_line = 0
                self.row = 0
            elif self.cur_line < 0:
                self.row = 0
            self.adjust_cursor_eol()
            self.update_screen()
        elif key == KEY_PGDN:
            self.top_line += self.height
            if self.cur_line >= self.total_lines:
                self.top_line = self.total_lines - self.height
                if self.top_line >= 0:
                    self.row = self.height - 1
                else:
                    self.top_line = 0
                    self.row = self.cur_line
            self.adjust_cursor_eol()
            self.update_screen()
        else:
            return False
        return True

    def handle_key(self, key: Union[bytes, int]):
        l = self._content[self.cur_line]
        if key == KEY_ENTER:
            if len(self._content) < self.height:
                self.tty.cursor(False)
                self.tty.goto(self.max_visible_height + len(self._status_content) - 1, 0)
                self.tty.write(b"\r\n")  # make space for new line at end
                self.tty.update_editor_row_offset(self.max_visible_height + len(self._status_content))
            self._content[self.cur_line] = l[:self.col]
            self._content.insert(self.cur_line + 1, l[self.col:])
            self.col = 0
            self.next_line()
            self.update_screen()
        elif key == KEY_BACKSPACE:
            if self.col > 0:
                self.col -= 1
                l = l[:self.col] + l[self.col + 1:]
                self._content[self.cur_line] = l
                self.update_line()
            elif self.col == 0 and self.cur_line > 0:
                self.col = len(self._content[self.cur_line - 1])
                self._content[self.cur_line - 1] += self._content[self.cur_line]
                self._content.pop(self.cur_line)
                if self.top_line > 0 and self.top_line + self.height > len(self._content):
                    self.top_line -= 1
                elif self.row > 0:
                    self.row -= 1
                if len(self._content) < self.height:
                    self.tty.write(b"\x1b[0m\x1b[1M")  # delete one line
                self.update_screen()
        elif key == KEY_DELETE:
            l = l[:self.col] + l[self.col + 1:]
            self._content[self.cur_line] = l
            self.update_line()
        elif isinstance(key, int):
            pass
        elif ord(key) <= 31:  # other control char
            pass
        else:
            l = l[:self.col] + str(key, "utf-8") + l[self.col:]
            self._content[self.cur_line] = l
            self.col += 1
            self.update_line()
        self.on_edit()

    def on_key(self, key: Union[bytes, int]) -> Union[bool, None]:
        # Overwrite this function if you want. Return True -> we consumed the event.
        pass

    def on_cursor_pos_change(self):
        # Overwrite this function if you want.
        pass

    def on_edit(self):
        # Overwrite this function if you want.
        pass


def _control_key(key: Optional[str]) -> Optional[bytes]:
    if not key:
        return None
    key = key.upper()
    assert ord("A") <= ord(key) <= ord("Z"), f"invalid control key {key!r}, should be in range A-Z"
    return bytes([ord(key) - ord("A") + 1])
