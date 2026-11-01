---
slug: var-braces
title: Braces: `${NAME}`
chapter: Variables
difficulty: easy
---

When a variable is followed directly by letters, the shell can't tell where the name ends. Braces mark it explicitly.

```
$ export TREE=teak
$ echo ${TREE}wood
teakwood
$ echo ${HOME}/notes
/home/you/notes
```
