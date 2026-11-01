---
slug: var-quotes
title: Variables and quotes
chapter: Variables
difficulty: medium
---

Quoting decides whether `$` is special:

- **Double quotes:** variables expand, but spaces in the result are kept as they are.
- **Single quotes:** nothing expands.
- **Backslash** before `$` (outside quotes or inside double quotes) makes it a plain dollar sign.
- A `$` that isn't followed by a name is just a `$`.

```
$ export T=lotus
$ echo "$T   pond"
lotus   pond
$ echo '$T'
$T
$ echo \$T
$T
$ echo "\$T is $T"
$T is lotus
$ echo $ alone
$ alone
```
