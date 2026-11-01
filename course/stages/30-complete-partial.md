---
slug: complete-partial
title: Longest common prefix
chapter: Completion
difficulty: hard
---

If all matches share a longer prefix than what's typed, TAB extends the line to that prefix (without a trailing space, because the word isn't finished).

Given programs `kv1_x`, `kv1_x_y` and `kv1_x_y_z`:

```
$ kv1<TAB>
$ kv1_x▌
$ kv1_x_<TAB>
$ kv1_x_y▌
$ kv1_x_y_<TAB>
$ kv1_x_y_z ▌
```

The last one is unique, so it gets the trailing space.
