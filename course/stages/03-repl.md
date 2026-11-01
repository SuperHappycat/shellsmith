---
slug: repl
title: Keep the loop going
chapter: Basics
difficulty: easy
---

A shell that answers once and quits isn't much of a shell. Turn your program into a **read–eval–print loop**: after handling a line, print the prompt again and wait for the next one.

```
$ abc
abc: command not found
$ def
def: command not found
$ ▌
```

### How it's tested
Three unknown commands in a row; after each one the prompt must come back.
