---
slug: pipe-builtin
title: Pipelines with builtins
chapter: Pipelines
difficulty: hard
---

Builtins can sit on either side of a pipe.

```
$ echo lotus river | wc -w
2
$ echo ignored | type exit
exit is a shell builtin
$ type echo | tr a-z A-Z
ECHO IS A SHELL BUILTIN
```

A builtin on the left writes into the pipe instead of the screen. A builtin on the right simply ignores its stdin.
