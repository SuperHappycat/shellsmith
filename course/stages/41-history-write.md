---
slug: history-write
title: Save history: `history -w`
chapter: History
difficulty: easy
---

`history -w FILE` writes the **whole** history to `FILE`, one command per line, replacing what was there. The `history -w` command itself is included.

```
$ echo lotus
lotus
$ history -w saved.txt
$ cat saved.txt
echo lotus
history -w saved.txt
```
