---
slug: run-program
title: Run real programs
chapter: Basics
difficulty: medium
---

Time to make the shell useful. When the first word isn't a builtin, look it up in `PATH` (same search as `type`) and **run it** with the remaining words as arguments. Wait for it to finish before showing the prompt again.

```
$ my_program alpha beta
(whatever my_program prints)
$ ▌
```

The program must receive the name you typed as its argument zero (`argv[0]`), not the full path.

### How it's tested
The tester puts a small script on your `PATH`. The script prints a secret number and each argument it receives, so the output proves you really ran it.

### Tips
- Python: `subprocess.run([name, *args], executable=full_path)`.
- C: `fork()`, then `execv(full_path, argv)` in the child and `waitpid()` in the parent.
