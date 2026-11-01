---
slug: cd-relative
title: `cd` to relative paths
chapter: Navigation
difficulty: medium
---

Support paths relative to the current directory, including `.` (here) and `..` (one level up).

```
$ pwd
/home/you
$ cd ./notes/2026
$ pwd
/home/you/notes/2026
$ cd ../..
$ pwd
/home/you
```

Most languages' "change directory" call already understands relative paths, so this may work with little extra code.
