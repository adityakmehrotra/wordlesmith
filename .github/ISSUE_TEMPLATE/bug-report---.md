---
name: Bug report
about: A wrong guess, a bad score, a crash, or an off benchmark number
title: ""
labels: bug
assignees: ""
---

**What happened**
A clear description. If the solver made a bad guess or gave a wrong feedback
score, include the target word and the guess.

**To reproduce**
The exact command or code, e.g.:

```
wordlesmith solve maven --strategy entropy
```

or, for a scoring bug:

```
python -c "from wordlesmith import feedback, pattern_to_string; print(pattern_to_string(feedback('speed', 'abide')))"
```

**Expected vs actual**
What you expected (turns, guesses, or the g/y/x pattern) and what you got.

**Environment**
- wordlesmith version (`wordlesmith --version`):
- Python version:
- OS:
