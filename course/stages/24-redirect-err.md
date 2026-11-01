---
slug: redirect-err
title: Send errors to a file: `2>`
chapter: Redirection
difficulty: medium
---

Programs have two output streams: **stdout** (file descriptor 1) for results, **stderr** (2) for errors. `2> file` redirects only stderr.

```
$ cat missing.txt 2> /tmp/err.txt
$ cat /tmp/err.txt
cat: missing.txt: No such file or directory
$ echo still here 2> /tmp/err2.txt
still here
```

In the second example `echo` writes nothing to stderr, so the file is created but empty, while normal output still reaches the screen.
