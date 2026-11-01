---
slug: complete-missing
title: Ring the bell when nothing matches
chapter: Completion
difficulty: easy
---

When nothing matches, leave the line as it is and ring the terminal bell (the character `\a`, byte 7).

```
$ nothinglikethis<TAB>     (beep)
```

GNU readline does this by itself when your completer returns no matches.
