# Shellsmith: build your own shell

Build a working Unix shell from an empty file, one tested stage at a time, entirely
from your terminal. 43 stages in 9 chapters: a prompt and REPL, builtins, running
programs, `cd`, quoting, environment variables, redirection, TAB completion,
pipelines, `;` / `&&` / `||`, and history that survives restarts.

You get a repository, clone it, write code, and `git push`. Every push runs the
tests and the results come back right in the push output:

```
$ git push
remote: ────────────────────────────────────────────────────────────
remote: Shellsmith: testing 4f2c9e1
remote: [stage 1] Show a prompt
remote: [stage 1] ✔ Saw the prompt "$ "
remote: [stage 1] ✔ Stage passed
remote: [stage 2] Complain about unknown commands
remote: [stage 2] Typing: lotus_499
remote:   [your shell] $ lotus_499
remote: [stage 2] ✘ Your shell exited (code 0) while I was waiting for "lotus_499: command not found".
remote:
remote:   █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  1/43 stages
remote:   ✔ 1 new stage passed. Nice work!
remote:   Up next: stage 2 · Complain about unknown commands
remote:   Read the full stage:  shellsmith stage
```

Nothing runs on GitHub or any website. The "server" you push to is a git repository
on your own computer, with a hook that runs the tester.

## Install

You need `git` and `python3` (3.9 or newer) on macOS or Linux. On Windows, use WSL:
run `wsl --install` in PowerShell as administrator, restart, open **Ubuntu**, and do
everything below in that window.

```sh
git clone https://github.com/SuperHappycat/shellsmith
cd shellsmith
./install.sh
```

This puts the `shellsmith` command in `~/.local/bin`. If the installer says that folder
isn't on your `PATH`, add the line it prints to `~/.bashrc` or `~/.zshrc` and open a
new terminal. To update later: `git pull && ./install.sh`.

## Start a challenge

```sh
shellsmith start python          # or: c, go, rust, javascript  (shellsmith languages)
```

It creates your challenge repository and tells you how to clone it:

```sh
git clone ~/.shellsmith/repos/shell-python.git shellsmith-shell-python
cd shellsmith-shell-python
shellsmith stage
```

## The loop

```sh
shellsmith stage        # read your current stage
# ...write code in app/...
shellsmith test         # run the tests on your working copy, nothing committed
shellsmith test -w      # same, re-running every time you save
shellsmith submit       # commit everything and push; tests run, results stream back
```

`shellsmith submit` is just `git add -A && git commit && git push`. Committing and
pushing yourself works exactly the same.

| Command | What it does |
|---|---|
| `shellsmith start [lang]` | create a new challenge repository |
| `shellsmith stage [N]` | instructions for your current stage, or stage N |
| `shellsmith test [N] [-w]` | test locally: everything, only stage N, or watch mode |
| `shellsmith test --seed S` | replay a run with exactly the same random words |
| `shellsmith submit [message]` | commit + push + see the results |
| `shellsmith status` | stages passed, current stage, recent submissions |
| `shellsmith list` | all your challenges |
| `shellsmith languages` | available languages and whether their tools are installed |

## How grading works

- The tester starts your shell inside a real pseudo-terminal and types into it like a
  person, so prompts, echo, TAB and arrow keys all count.
- Every run uses random words, so hard-coded answers don't pass.
- Stages run in order and stop at the first failure. That stage is your current one.
  Passing several stages in one push is fine.
- Pushes are graded on exactly what you committed, not on your working folder.
- If a stage that used to pass starts failing, the push output warns you.

## Languages

| Language | Needs | Starter |
|---|---|---|
| Python | `python3` | `app/main.py` |
| C | a C compiler and GNU readline (`sudo apt install build-essential libreadline-dev`) | `app/main.c` |
| Go | `go` | `app/main.go` |
| Rust | `cargo` | `app/src/main.rs` |
| JavaScript | `node` | `app/main.js` |

Compiled languages have a `build.sh` that runs once before each test run, so a compile
error shows up as one clear message. Any other language works if you point
`your_shell.sh` (and `build.sh`) at it.

**macOS note:** the Python and readline that ship with macOS use *libedit*, which
handles TAB differently from GNU readline. If the completion stages (26–30) misbehave,
bind TAB with `readline.parse_and_bind("bind ^I rl_complete")` on libedit, or use a
Python built with GNU readline.

## Where things live

| Path | What it is |
|---|---|
| `~/.shellsmith/engine/` | the installed tester, course and starters |
| `~/.shellsmith/repos/*.git` | your challenge "servers" (bare git repos with the test hook) |
| `~/.shellsmith/repos/*.git/shellsmith/progress.json` | your progress and submission history |
| your clone | your code; push it anywhere else too (e.g. GitHub) as a backup |

Uninstall: `rm -rf ~/.shellsmith ~/.local/bin/shellsmith` (this deletes your challenge
servers; your clones stay).

## This repository

| Path | What it is |
|---|---|
| `install.sh` | installs the `shellsmith` command |
| `shellsmith.py` | the command-line tool |
| `hook.py` | the git hook that grades each push |
| `tester/` | PTY harness (`harness.py`), stage tests (`stages.py`), runner (`run.py`) |
| `course/stages/` | stage instructions, one Markdown file each |
| `starters/` | starter code for each language |

## Licence

MIT. Course text, tests and tooling are original to this project.
