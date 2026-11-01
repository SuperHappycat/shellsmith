---
slug: redirect-out
title: Send output to a file: `>`
chapter: Redirection
difficulty: medium
---

`command > file` (or `1> file`) sends the command's standard output into `file` instead of the screen. The file is created if needed and **emptied first** if it exists.

```
$ echo lotus > /tmp/out.txt
$ cat /tmp/out.txt
lotus
$ ls /some/dir 1> /tmp/list.txt
```

This must work for builtins (like `echo`) *and* external programs (like `ls`).

### Tips
- For an external program, open the file and pass it as the child's stdout.
- For a builtin, write to the opened file instead of `sys.stdout`.
