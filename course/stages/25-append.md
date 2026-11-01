---
slug: append
title: Append instead of overwrite: `>>`
chapter: Redirection
difficulty: medium
---

`>>` and `1>>` append stdout to a file; `2>>` appends stderr. The file is created if it doesn't exist, and existing content is kept.

```
$ echo one > log.txt
$ echo two >> log.txt
$ echo three 1>> log.txt
$ cat log.txt
one
two
three
```
