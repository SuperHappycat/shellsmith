---
slug: backslash-double
title: Backslashes inside double quotes
chapter: Quoting
difficulty: hard
---

Inside double quotes, a backslash is only special before a few characters: `\`, `"`, `$`, `` ` `` and newline. Before those it escapes them; before anything else it stays as a normal backslash.

Inside single quotes it is never special.

```
$ echo "say \"hi\""
say "hi"
$ echo "back\\slash"
back\slash
$ echo "keep\nthis"
keep\nthis
$ echo 'a\"b'
a\"b
```
