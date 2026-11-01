---
slug: var-export
title: Set variables with `export`
chapter: Variables
difficulty: medium
---

Add the builtin `export NAME=value`. It sets the variable in the shell **and** in the environment of every program the shell starts from then on.

```
$ export FRUIT=mango
$ echo $FRUIT
mango
$ printenv FRUIT
mango
$ type export
export is a shell builtin
```

### How it's tested
The tester puts a small program on your `PATH` that prints a variable's value, so it can see what your child processes inherit.

### Tips
- Python: changing `os.environ` changes what `subprocess` passes to children.
- C: `setenv()`.
