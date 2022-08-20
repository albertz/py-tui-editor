Simple Python terminal (TUI) multi-line editor
##############################################

This is just a simple multi-line editor for the terminal
(VT100).
It is a bit like
``input`` (`doc <https://docs.python.org/3/library/functions.html#input>`__)
but supporting multiple lines
and behaving more like a simple editor.
It is different to other editors
and other TUI frameworks in that it will not go full-screen
but only use the last N lines of the terminal.
It is intended to be simple and flexible and hackable,
i.e. the behavior can be changed, typing events can be handled,
etc.
It takes extra care to handle terminal resizing.
It also supports to show a status bar (potential multi-line).

Homepage: https://github.com/albertz/py-tui-editor


Installation
************

The project is on PyPI:
https://pypi.org/project/tui-editor/

Thus you can just do:

.. code-block:: bash

    pip install tui-editor


Usage
*****

.. code-block:: python

    >>> from tui_editor import TuiEditor
    >>> editor = TuiEditor()
    >>> editor.edit()
    >>> editor.get_text()
    'Hello World!'


Screenshot
**********

.. image:: https://raw.githubusercontent.com/albertz/py-tui-editor/main/screenshots/2022-08-21.png?sanitize=true


Motivation
**********

Python TUI?

What I want:

- simple multi-line editor
- not whole screen but only next N lines
- show interactive feedback. e.g. mark edits, show number of edits, show diff in separate plane or so


Licence
*******

MIT License


History
*******

2015 Paul Sokolovsky:
`picotui project <https://pypi.org/project/picotui/>`__
`seditor.py example <https://github.com/pfalcon/picotui/blob/master/seditor.py>`__.
2022 Albert Zeyer: extend and redesign and package just the text editor as this library.


Related projects
****************

https://docs.python.org/3/library/curses.html
- too complex but at the same time too limited?

https://github.com/bczsalba/pytermgui (1.2k stars)
- limited, no real text editor

https://urwid.org/examples/index.html (2.5k stars)
- edit example: https://github.com/urwid/urwid/blob/master/examples/edit.py

https://github.com/prompt-toolkit/python-prompt-toolkit (7.9k stars)
- too complex...? similar as curses...

https://github.com/pfalcon/picotui (0.7k stars)
- good enough? editor: https://github.com/pfalcon/picotui/blob/master/picotui/editor.py
- another editor: https://github.com/pfalcon/picotui/blob/master/seditor.py

https://github.com/Textualize/textual (13k stars)
- async framework, I don't want that...

(Or coding some line edit by hand, should not be too difficult...?)

https://github.com/pfalcon/picotui/blob/master/seditor.py


References
**********

https://en.wikipedia.org/wiki/ANSI_escape_code#Terminal_input_sequences
https://invisible-island.net/xterm/ctlseqs/ctlseqs.html#h2-The-Alternate-Screen-Buffer
