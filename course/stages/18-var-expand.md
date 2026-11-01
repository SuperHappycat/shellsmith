---
slug: var-expand
title: Expand `$VARIABLES`
chapter: Variables
difficulty: medium
---

Every process carries **environment variables**: name/value pairs like `HOME=/home/you`. In a shell, `$NAME` is replaced by the variable's value before the command runs.

```
$ echo $HOME
/home/you
$ echo dir:$HOME:end
dir:/home/you:end
$ echo $NOT_SET lotus
lotus
```

A variable that isn't set expands to nothing. When an unquoted word becomes completely empty that way, it disappears instead of becoming an empty argument (that's why `lotus` above has no leading space).

A variable name starts with a letter or `_` and continues with letters, digits and `_`.

### Tips
Do the expansion inside your tokenizer, at the moment you meet a `$`, so quoting rules (next stages) fall out naturally.
