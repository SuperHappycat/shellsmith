---
slug: history-append
title: Append new history: `history -a`
chapter: History
difficulty: medium
---

`history -a FILE` appends only the commands entered **since the last `history -a`** (or since the shell started) to `FILE`, keeping what's already in it.

```
$ echo one
$ history -a log.txt        # adds: echo one, history -a log.txt
$ echo two
$ history -a log.txt        # adds: echo two, history -a log.txt
```

Running it twice in a row must not write the same lines twice.
