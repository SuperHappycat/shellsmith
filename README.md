# Shellsmith — build your own shell

Build a working Unix shell from an empty file, one tested stage at a time.
43 stages in 9 chapters: a REPL, builtins, running programs, `cd`, quoting,
environment variables, redirection, TAB completion, pipelines, `;`/`&&`/`||`
lists, and history that survives restarts.

Your code lives in **your GitHub repo**. Each `./smith submit` pushes it,
GitHub Actions runs the tester, the result streams back to your terminal, and
your progress dashboard (GitHub Pages) updates.

```
 your terminal                     GitHub (your repo)
 ─────────────                     ──────────────────
 ./smith test   ──runs locally──▶  (nothing leaves your machine)
 ./smith submit ──git push──────▶  Actions: tester runs your shell
              ◀──live status + log─┘        │
                                            ▼
                                   Pages: https://<you>.github.io/<repo>/
```

## 1. One-time setup (≈3 minutes)

> **Easiest:** open your dashboard and click **Start here**. It walks you through three ways
> to work, with copy buttons: **Terminal** (macOS / Windows via WSL / Linux),
> **Desktop apps** (GitHub Desktop + VS Code, no terminal needed) and
> **Browser** (GitHub Codespaces, nothing to install).

Requirements: `git`, `python3` (3.9+), and the [GitHub CLI](https://cli.github.com).

```sh
gh auth login                 # once per computer
cd shellsmith
./smith setup                 # creates a public repo, enables the dashboard, pushes
```

`setup` prints your dashboard address, e.g. `https://yourname.github.io/shellsmith/`.
The first deploy takes a minute or two.

<details><summary>Prefer to do it by hand?</summary>

1. Create an empty **public** repo on github.com (Pages on private repos needs a paid plan).
2. `git init -b main && git add -A && git commit -m start`
3. `git remote add origin https://github.com/<you>/<repo>.git`
4. On GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
5. `git push -u origin main`
</details>

## 2. The work loop

```sh
./smith stage        # read the current stage's instructions in the terminal
# ...edit app/main.py...
./smith test         # run the tests here (a few seconds, stages run in parallel)
./smith test -w      # or: watch mode, re-runs whenever you save
./smith submit       # commit + push; watch GitHub test it and print the log here
```

Other commands: `./smith stages` (list + progress), `./smith stage 12` (read any stage),
`./smith test 12` (run one stage alone), `./smith test --seed 4711` (replay the exact
random words of a run; the seed is printed after every run), `./smith status`, `./smith open` (dashboard).

`submit` uses the GitHub CLI when it's logged in (fastest, full log). Without it,
it polls the public GitHub API and reads the results from your dashboard instead.

## 3. Pick your language

```sh
./smith language            # list: python (default), c, go, rust, javascript
./smith language rust       # switch; your old app/ is backed up in .smith/
```

Each language comes with a starter in `app/`. Compiled languages have a `build.sh`
that the tester runs once before the stages (also on GitHub), so a compile error
shows up as a clear message instead of 43 failures.

Any other language works too: the tester only ever runs `./your_shell.sh` (after
`./build.sh`, if present). Point them at your program, and if GitHub's Ubuntu
runner lacks your toolchain, add an install step before **Run the tester** in
`.github/workflows/smith.yml`.

## Notes

- **macOS + Python:** the Python that ships with macOS uses *libedit* instead of GNU
  readline. TAB-completion stages may behave differently locally; the official run on
  GitHub (Ubuntu) uses GNU readline. With libedit, bind TAB with
  `readline.parse_and_bind("bind ^I rl_complete")`.
- Tests stop at the first failing stage. Everything before it is "passed", that one
  is your current stage, the rest are locked (you can still read them).
- The tester types into your shell through a real pseudo-terminal, so prompts,
  echo and line editing all count. Random words are used each run, so hard-coding
  answers won't work.
- Slow machine? `SMITH_TIMEOUT=8 ./smith test` (seconds per wait; default 4).

## Layout

| Path | What it is |
|---|---|
| `app/` | **Your shell** (starter code; Python by default) |
| `starters/` | Starter code for every language (`./smith language`) |
| `build.sh` | Compile step for compiled languages (absent for Python/JS) |
| `your_shell.sh` | How the tester starts your shell |
| `smith` | The command-line companion |
| `tester/` | The tests (`stages.py`) and PTY harness |
| `course/stages/` | Stage instructions, one Markdown file each |
| `site/` + `scripts/build_site.py` | The dashboard website |
| `.github/workflows/smith.yml` | Runs tests on each push, deploys the dashboard |

## Licence

MIT. Course text, tests and tooling are original to this project.
