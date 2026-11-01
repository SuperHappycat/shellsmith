---
slug: history-arrows
title: Arrow keys recall commands
chapter: History
difficulty: medium
---

Pressing **UP** replaces the current line with the previous command; pressing it again goes further back. ENTER runs whatever is on the line.

```
$ echo lotus
lotus
$ echo river
river
$ <UP><UP>
$ echo lotus
lotus
```

### Tips
With Python's `readline`, lines read by `input()` are added to its history automatically, so this may already work. Make sure your own `history` list and readline's stay in step.
