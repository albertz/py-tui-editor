# py-tui-editor

Simple Python terminal (TUI) multi-line editor

Simple TUI editor

Python TUI?

What I want:
- simple multi-line editor
- not whole screen but only partial
- show interactive feedback. e.g. mark edits, show number of edits, show diff in separate plane or so

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

Very simple VT100 terminal text editor widget
Copyright (c) 2015 Paul Sokolovsky, (c) 2022 Albert Zeyer
Distributed under MIT License

https://en.wikipedia.org/wiki/ANSI_escape_code#Terminal_input_sequences
https://invisible-island.net/xterm/ctlseqs/ctlseqs.html#h2-The-Alternate-Screen-Buffer
