"""
demo prompt
"""

from tui_editor import TuiEditor


if __name__ == '__main__':
    print('Hello World! Ctrl+S to save.')
    e = TuiEditor()
    keys = []
    e.on_key = lambda key: (keys.append(key), e.set_status_lines(["key: %r" % key]), None)[-1]
    e.edit()
    print("Result:", repr(e.get_text()))
    print("Keys:", repr(keys))
    print('Good bye!')
