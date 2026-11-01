---
slug: complete-builtin
title: TAB-complete builtins
chapter: Completion
difficulty: medium
---

Now the shell starts to feel like a real one. When the user presses **TAB**, finish the word they're typing.

Start with builtins. Typing `ech` then TAB should turn the line into `echo ` (with a trailing space, ready for arguments).

```
$ ech<TAB>
$ echo ▌
```

### How it's tested
The tester sends real keystrokes through a terminal and looks at what's on screen.

### Tips
- Python: `import readline`, then `readline.set_completer(fn)` and `readline.parse_and_bind("tab: complete")`. Your completer is called with the text and an index `state`; return the `state`-th match or `None`.
- Python's readline does not add a space for you; add it yourself when there is exactly one match.
- C: GNU readline offers `rl_attempted_completion_function`.
- Importing readline also gives you line editing for free.
