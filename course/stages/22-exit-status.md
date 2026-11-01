---
slug: exit-status
title: Exit status: `$?`
chapter: Variables
difficulty: medium
---

Every command finishes with a number: `0` means success, anything else means failure. `$?` expands to the status of the **last** command.

```
$ false
$ echo $?
1
$ nosuchthing
nosuchthing: command not found
$ echo $?
127
$ cd /nowhere
cd: /nowhere: No such file or directory
$ echo $?
1
```

Rules:
- External program: its own exit code.
- Command not found: `127`.
- Builtins: `0` on success, `1` on failure (like a failed `cd`).
- A pipeline: the status of its **last** command.

Now that you track it, a plain `exit` (no number) can exit with the last status, as real shells do.
