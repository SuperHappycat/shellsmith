---
slug: semicolon
title: Run one after another: `;`
chapter: Command lists
difficulty: easy
---

`;` separates commands on one line. They run in order, whatever happens to each.

```
$ echo first; echo second
first
second
$ cd notes ; pwd
/home/you/notes
$ oops;echo still going
oops: command not found
still going
```

`;` doesn't need spaces around it.
