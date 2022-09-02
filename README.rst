Simple Python terminal (TUI) multi-line editor
##############################################

Features:

- simple multi-line editor
- not whole screen but only next N lines
- show interactive feedback. e.g. mark edits, show number of edits, show diff in separate plane or so

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

Simple empty editor:

.. code-block:: python

    >>> from tui_editor import TuiEditor
    >>> editor = TuiEditor()
    >>> editor.edit()
    >>> editor.get_text()
    'Hello World!'

Predefined editable text:

.. code-block:: python

    >>> from tui_editor import TuiEditor
    >>> editor = TuiEditor()
    >>> editor.set_text('Hello World!')
    >>> editor.edit()
    >>> editor.get_text()
    'Hello World!'


See `demo-prompt.py <https://github.com/albertz/py-tui-editor/blob/main/demo-prompt.py>`__
and `demo-editor.py <https://github.com/albertz/py-tui-editor/blob/main/demo-editor.py>`__.


Screenshot
**********

.. image:: https://raw.githubusercontent.com/albertz/py-tui-editor/master/screenshots/2022-09-02.png?sanitize=true


Screencast
**********

.. image:: https://img.youtube.com/vi/zIFMyBkYwqg/maxresdefault.jpg
   :target: https://youtu.be/zIFMyBkYwqg

This shows the ``demo-prompt.py`` and ``demo-editor.py``.

.. image:: https://img.youtube.com/vi/4ERr0o9k72Y/maxresdefault.jpg
   :target: https://youtu.be/4ERr0o9k72Y

This uses a `very custom small app <https://github.com/albertz/playground/blob/master/pdf-extract-comments.py>`__,
which I use to take over annotated PDF edits into my Latex file,
where I get the editor, and it shows me the live-diff in the status bar of the editor.


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

Python terminal user interface (TUI) and related.

The features stated in the beginning were the main motivation.
The related work here did not really satisfy me in getting those features,
or did not really make it simpler to accomplish them.
(At least from a first glance to those other projects
- maybe I'm missing sth! Please share a short demo,
similar to the demos here, if you know how to easily implement it.)

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

https://en.wikipedia.org/wiki/ANSI_escape_code
https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
