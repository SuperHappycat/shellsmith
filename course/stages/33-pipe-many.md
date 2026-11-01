---
slug: pipe-many
title: Long pipelines
chapter: Pipelines
difficulty: hard
---

Generalise to any number of stages:

```
$ cat data.txt | head -n 7 | wc -l
7
$ cat data.txt | sort | head -n 3 | tr a-z A-Z
```

Each process reads from the previous pipe and writes to the next one.
