---
slug: backslash-bare
title: Backslashes outside quotes
chapter: Quoting
difficulty: medium
---

Outside any quotes, a backslash makes the **next character literal**, whatever it is, and the backslash itself disappears.

```
$ echo lotus\ \ \ river
lotus   river
$ echo \'hi\' \"there\"
'hi' "there"
$ echo a\nb
anb
$ echo \\x
\x
```
