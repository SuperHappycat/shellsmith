---
slug: quoted-exe
title: Quoted program names
chapter: Quoting
difficulty: medium
---

The first word of a command is just another argument, so it can be quoted too. That's how you run a program whose file name has a space or a quote in it.

```
$ 'my tool' x
$ "it's here" "two  words"
```

If your tokenizer already handles quotes, this is mostly about making sure the *program lookup* uses the unquoted name.
