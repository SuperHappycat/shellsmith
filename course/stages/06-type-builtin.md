---
slug: type-builtin
title: Identify builtins with `type`
chapter: Basics
difficulty: easy
---

`type NAME` tells you what kind of command `NAME` is. Start with builtins and unknowns:

```
$ type echo
echo is a shell builtin
$ type exit
exit is a shell builtin
$ type type
type is a shell builtin
$ type qwerty
qwerty: not found
```

Note the `type` command is itself a builtin.
