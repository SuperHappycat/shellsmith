---
slug: histfile
title: Remember across sessions: `HISTFILE`
chapter: History
difficulty: medium
---

Make history survive restarts, using the `HISTFILE` environment variable:

1. On startup, if `HISTFILE` is set and the file exists, load it into history (like `history -r`).
2. On `exit`, write the whole history to `HISTFILE` (like `history -w`). The `exit` command itself is included.

```
$ history          # HISTFILE already had two lines
    1  echo lotus
    2  echo river
    3  history
$ echo teak
teak
$ exit 0
```
Afterwards the file holds all five lines, ending with `exit 0`.

🎉 This is the last stage. When it passes, you've built a shell with variables, lists, pipelines, completion and persistent history.
