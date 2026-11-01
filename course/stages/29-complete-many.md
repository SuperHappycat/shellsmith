---
slug: complete-many
title: Several matches
chapter: Completion
difficulty: hard
---

When several names match and they share nothing beyond what's already typed:

1. The **first** TAB rings the bell.
2. A **second** TAB prints all matches on a new line, then redraws the prompt with what was typed so far.

```
$ zz1_<TAB>          (beep)
$ zz1_<TAB>
zz1_lotus  zz1_mango  zz1_teak
$ zz1_▌
```

### How it's tested
After the second TAB, every matching name must be on screen and the last line must be the prompt plus the typed text. The exact spacing between names isn't checked.
