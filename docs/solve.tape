# Demo GIF: auto-solving known words (self-driving, no typing).
# Record from the repo root with:  vhs docs/solve.tape   ->   writes docs/solve.gif
# Needs VHS (brew install vhs) and the package installed in ./.venv
# (python3 -m venv .venv && .venv/bin/pip install -e .).

Output docs/solve.gif

Set FontSize 22
Set Width 1120
Set Height 420
Set Padding 20
Set TypingSpeed 55ms

# Hidden setup: make the repo venv's `wordlesmith` available inside VHS's shell.
Hide
Type "export PATH=$PWD/.venv/bin:$PATH && clear"
Enter
Sleep 500ms
Show

# MAVEN is a real NYT answer that isn't in the original 2,315-word list; the
# default full-valid pool solves it anyway.
Type "wordlesmith solve maven"
Enter
Sleep 2.5s

# The classic 2,315-answer pool, via --curated.
Type "wordlesmith solve crane --curated"
Enter
Sleep 3.5s
