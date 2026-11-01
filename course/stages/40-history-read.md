---
slug: history-read
title: Load history from a file: `history -r`
chapter: History
difficulty: medium
---

`history -r FILE` reads `FILE` and appends each non-empty line to the history list.

```
$ history -r old_commands.txt
$ history
    1  history -r old_commands.txt
    2  echo lotus
    3  echo river
    4  history
```

The loaded lines should also be reachable with the UP arrow.
