---
slug: history
title: The `history` builtin
chapter: History
difficulty: medium
---

Remember every line the user enters and add a `history` builtin that lists them, numbered from 1. The number is right-aligned in 5 characters, followed by two spaces.

```
$ echo lotus
lotus
$ echo river
river
$ history
    1  echo lotus
    2  echo river
    3  history
```

The `history` command itself is part of the list.
