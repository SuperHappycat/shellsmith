---
slug: and-or
title: Conditional lists: `&&` and `||`
chapter: Command lists
difficulty: medium
---

- `a && b` runs `b` only if `a` **succeeded** (status 0).
- `a || b` runs `b` only if `a` **failed**.

They chain left to right, each deciding based on the status of whatever ran last:

```
$ true && echo yes
yes
$ false && echo never
$ false || echo fallback
fallback
$ cd /nowhere && echo moved
cd: /nowhere: No such file or directory
$ false && echo a || echo b
b
$ false; echo $? && echo ok
1
ok
```

A skipped command doesn't change `$?`.

### Watch out
Expand variables when each command **runs**, not when the whole line is read. Otherwise `false; echo $?` prints the status from *before* `false`. A simple approach: first split the line at top-level `;`, `&&` and `||` (ignoring ones inside quotes), then tokenize and expand each piece just before running it.
