---
slug: single-quotes
title: Single quotes
chapter: Quoting
difficulty: medium
---

So far you split input on whitespace. Real shells let you keep spaces inside an argument with quotes.

Inside **single quotes** every character is literal — spaces, backslashes, everything — until the closing `'`. Quoted pieces glue onto whatever touches them.

```
$ echo 'lotus     river'
lotus     river
$ echo 'lo''tus' teak
lotus teak
$ echo 'a\nb'
a\nb
$ cat 'my notes.txt'
(contents of the file called "my notes.txt")
```

### Tips
This is the moment to replace `split()` with a small character-by-character tokenizer. You'll extend it in the next few stages, so make it easy to grow.
