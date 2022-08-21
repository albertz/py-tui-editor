"""
demo prompt
"""

import argparse
from tui_editor import TuiEditor


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--height", type=int, default=10)
    arg_parser.add_argument("--show-line-numbers", action="store_true")
    args = arg_parser.parse_args()

    print('Hello World! Ctrl+S to save.')
    e = TuiEditor()
    if args.show_line_numbers:
        e.show_line_numbers = True
    keys = []
    e.on_key = lambda key: (keys.append(key), e.set_status_lines(["key: %r" % key]), None)[-1]
    e.edit()
    print("Result:", repr(e.get_text()))
    print("Keys:", repr(keys))
    print('Good bye!')
