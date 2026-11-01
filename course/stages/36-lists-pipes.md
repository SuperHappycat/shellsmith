---
slug: lists-pipes
title: Lists with pipelines
chapter: Command lists
difficulty: medium
---

`|` binds tighter than `&&`, `||` and `;`. So `a | b && c` means "run the pipeline `a | b`, then `c` if the pipeline succeeded".

```
$ echo lotus | tr a-z A-Z && echo done
LOTUS
done
$ cat words.txt | sort | uniq; echo end
$ cat missing 2> err.txt || echo teak | tr a-z A-Z
TEAK
```

### How it's tested
The tester compares your output with what your system's `sh` prints for the same line.
