# Demo GIF: playing along with a real puzzle.
# Record from the repo root with:  vhs docs/demo.tape   ->   writes docs/demo.gif
# Needs VHS (brew install vhs) and the package installed in ./.venv
# (python3 -m venv .venv && .venv/bin/pip install -e .).

Output docs/demo.gif

Set FontSize 22
Set Width 1120
Set Height 480
Set Padding 20
Set TypingSpeed 55ms

# Hidden setup: make the repo venv's `wordlesmith` available inside VHS's shell.
Hide
Type "export PATH=$PWD/.venv/bin:$PATH && clear"
Enter
Sleep 500ms
Show

# It suggests a word; you play it in the real game and type back the colors
# (g = green, y = yellow, x = gray). Target here is MAVEN.
Type "wordlesmith play"
Enter
Sleep 2s
Type "xgxgx"
Enter
Sleep 2s
Type "xgxgg"
Enter
Sleep 2s
Type "ggggg"
Enter
Sleep 3.5s
