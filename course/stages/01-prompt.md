---
slug: prompt
title: Show a prompt
chapter: Basics
difficulty: warm-up
---

Every interactive shell starts the same way: it tells you it is ready, then waits.

Make your program print `$ ` (a dollar sign and one space, **no newline**) and then wait for a line of input.

```
$ ▌
```

### How it's tested
The tester starts your shell inside a pseudo-terminal and waits for `$ ` to appear. Nothing is typed yet.

### Tips
- Output is often buffered. Flush stdout after printing the prompt, or the tester will never see it.
- In Python, `input("$ ")` prints the prompt and reads a line in one call.
