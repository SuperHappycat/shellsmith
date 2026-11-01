---
slug: cd-absolute
title: `cd` to absolute paths
chapter: Navigation
difficulty: medium
---

Add the builtin `cd`. Start with absolute paths (those beginning with `/`).

```
$ cd /usr/local
$ pwd
/usr/local
$ cd /no/such/place
cd: /no/such/place: No such file or directory
```

`cd` must be a builtin: if it ran as a separate program, it would change *that* program's directory and then exit, leaving your shell where it was.

A failed `cd` must not move the shell.
