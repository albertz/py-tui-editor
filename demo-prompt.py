"""
demo prompt
"""

from tui_editor import TuiEditor


if __name__ == '__main__':
    print('Hello World!')
    e = TuiEditor()
    e.edit()
    print(repr(e.get_text()))
    print('Good bye!')
