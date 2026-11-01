---
slug: double-quotes
title: Double quotes
chapter: Quoting
difficulty: medium
---

**Double quotes** also keep spaces together, and a single quote inside them is just a character.

```
$ echo "lotus   river"  "teak"
lotus   river teak
$ echo "mango's tree"
mango's tree
$ echo "a"'b'c
abc
```

(Real shells also expand `$VARS` inside double quotes. That is not tested here.)
