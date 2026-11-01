---
slug: type-path
title: Search `PATH` in `type`
chapter: Basics
difficulty: medium
---

Programs live in the folders listed in the `PATH` environment variable, separated by `:`.

Extend `type` so that, when `NAME` is not a builtin, it searches each `PATH` folder **in order** and reports the first match:

```
$ type cat
cat is /usr/bin/cat
```

A match only counts if it's a regular file **and** you're allowed to execute it. A file without the execute permission must be skipped, and the search continues with the next folder.

### How it's tested
The tester builds a `PATH` where the first folder contains a non-executable decoy and a later folder contains the real program. Only the real one should be reported. It also checks well-known programs like `cat` and `ls`.

### Tips
- Python: `os.access(path, os.X_OK)` and `os.path.isfile(path)`.
- Builtins still win: `type echo` must still say builtin.
