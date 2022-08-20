#!/usr/bin/env python3

"""
Demo editor
"""

import argparse
from tui_editor import Editor


def main():
    """main"""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("file", help="File content to edit (nothing will be written)", default=__file__, nargs="?")
    arg_parser.add_argument("--height", type=int, default=20)
    args = arg_parser.parse_args()

    with open(args.file) as f:
        content = f.read().splitlines()

    print("Hello editor!")

    e = Editor()
    e.set_lines(content)
    e.height = args.height

    e.on_cursor_pos_change = (
        lambda: e.set_status_content([
            "line: %d/%d" % (e.cur_line + 1, e.total_lines),
            "col: %d" % e.col,
            ]))

    e.loop()

    print("Good bye!")


if __name__ == "__main__":
    main()
