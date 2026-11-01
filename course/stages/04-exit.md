---
slug: exit
title: Leave with `exit`
chapter: Basics
difficulty: easy
---

Add your first **builtin** — a command the shell handles itself instead of running a program.

`exit N` stops the shell with exit status `N`.

```
$ exit 3
```
(the process ends; `echo $?` in your real terminal would show `3`)

### How it's tested
Two runs: `exit 0` must end with status 0, then `exit` with a random small number must end with that number.
