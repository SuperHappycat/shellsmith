---
slug: pipe
title: Two-program pipelines
chapter: Pipelines
difficulty: hard
---

`a | b` runs both programs **at the same time**, connecting `a`'s stdout to `b`'s stdin through a pipe.

```
$ cat fruit.txt | wc -l
4
$ echo hi there | tr a-z A-Z
HI THERE
```

### How it's tested
The tester runs the same pipeline with your system's `sh` and expects identical output.

### Tips
- Create the pipe with `os.pipe()` (or `pipe()` in C).
- Close the ends you don't use, in the parent too. If a write end stays open, the reader never sees end-of-file and the pipeline hangs.
- Wait for **all** processes before printing the next prompt.
