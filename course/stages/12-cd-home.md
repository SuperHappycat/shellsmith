---
slug: cd-home
title: `cd ~` goes home
chapter: Navigation
difficulty: easy
---

`~` stands for the user's home directory, taken from the `HOME` environment variable.

```
$ cd ~
$ pwd
/home/you
$ cd ~/notes
$ pwd
/home/you/notes
```

### How it's tested
The tester sets `HOME` to a temporary folder. Read the variable, don't hard-code a path.
