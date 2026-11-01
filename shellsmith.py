#!/usr/bin/env python3
"""shellsmith: build your own shell, stage by stage, from your terminal.

  shellsmith start [LANG]    create a new challenge repository to clone
  shellsmith stage [N]       instructions for your current stage (or stage N)
  shellsmith test [N] [-w]   run the tests on your working copy (no commit)
  shellsmith submit [MSG]    commit everything and push; tests run and report back
  shellsmith status          stages passed, current stage, recent submissions
  shellsmith list            all your challenge repositories
  shellsmith languages       languages you can start with

Inside a challenge repo, plain `git push` works too: every push is tested.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ENGINE = os.path.dirname(os.path.abspath(__file__))
HOME = os.environ.get("SHELLSMITH_HOME") or os.path.join(os.path.expanduser("~"), ".shellsmith")
REPOS = os.path.join(HOME, "repos")
sys.path.insert(0, os.path.join(ENGINE, "tester"))
from run import load_course  # noqa: E402

LANGS = {"python": "Python 3", "c": "C (with GNU readline)", "go": "Go", "rust": "Rust",
         "javascript": "JavaScript (Node.js)"}
TOOLS = {"python": "python3", "c": "cc", "go": "go", "rust": "cargo", "javascript": "node"}

COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def c(code, t):
    return f"\033[{code}m{t}\033[0m" if COLOR else t


bold, dim, green, red, cyan, yellow = (lambda t: c("1", t)), (lambda t: c("90", t)), (lambda t: c("32", t)), \
    (lambda t: c("31", t)), (lambda t: c("36", t)), (lambda t: c("33", t))


def die(msg, hint=None):
    print(red("✘ ") + msg)
    if hint:
        print("  " + hint)
    sys.exit(1)


def git(*args, cwd=None, check=True, capture=True, env=None):
    r = subprocess.run(["git", *args], cwd=cwd, text=True, env=env,
                       stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE if capture else None)
    if check and r.returncode != 0:
        die(f"git {' '.join(args)} failed", (r.stderr or "").strip())
    return (r.stdout or "").strip()


# ------------------------------------------------------------------ locating things
def find_workspace(start=None):
    d = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.exists(os.path.join(d, "shellsmith.json")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def need_workspace():
    ws = find_workspace()
    if not ws:
        die("This isn't a Shellsmith challenge folder.",
            f"Create one with {cyan('shellsmith start python')}, or cd into the folder you cloned.")
    return ws


def server_of(ws):
    url = git("remote", "get-url", "origin", cwd=ws, check=False)
    if url.startswith("file://"):
        url = url[7:]
    url = os.path.expanduser(url)
    if url and os.path.isdir(url) and os.path.exists(os.path.join(url, "hooks", "post-receive")):
        return url
    return None


def progress_of(server):
    try:
        with open(os.path.join(server, "shellsmith", "progress.json")) as f:
            return json.load(f)
    except (OSError, ValueError, TypeError):
        return {}


def current_index(course, ws):
    p = progress_of(server_of(ws)) if ws else {}
    cur = p.get("current")
    if cur is None and p.get("last") and p["last"].get("passed") == len(course):
        return len(course)
    for i, s in enumerate(course):
        if s["slug"] == cur:
            return i
    return 0


def render_md(text):
    out, in_code = [], False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            out.append("    " + cyan(line))
        elif line.startswith("#"):
            out.append("\n" + bold(yellow(line.lstrip("# "))))
        else:
            line = re.sub(r"\*\*(.+?)\*\*", lambda m: bold(m.group(1)), line)
            line = re.sub(r"`([^`]+)`", lambda m: cyan(m.group(1)), line)
            out.append(line)
    return "\n".join(out)


def plain(title):
    return title.replace("`", "")


# ------------------------------------------------------------------ start
README = """# My shell ({lang_name})

Built with **Shellsmith**: {total} stages, from printing a prompt to pipelines,
TAB completion and history.

## How this works

```sh
shellsmith stage      # read your current stage
# ...write code in app/ ...
shellsmith test       # run the tests here, without committing
shellsmith submit     # commit + push; the tests run and report back in your terminal
```

`git push` works too: every push to this repository is tested, and the results
appear in the push output.

- Your code goes in `app/`. The tester starts it through `your_shell.sh`.
{build_note}- Run one stage on its own: `shellsmith test 5`. Re-run on every save: `shellsmith test -w`.
- Progress: `shellsmith status`.
"""


def cmd_start(args):
    lang = (args[0] if args and not args[0].startswith("-") else "python").lower()
    if lang not in LANGS:
        die(f"Unknown language {lang!r}.", f"Choose one of: {', '.join(LANGS)}")
    if not shutil.which("git"):
        die("git is not installed.")
    if not shutil.which(TOOLS[lang]):
        print(yellow(f"! {TOOLS[lang]} isn't on your PATH. You'll need it to run a {LANGS[lang]} shell."))
    base = f"shell-{lang}"
    name, n = base, 2
    while os.path.exists(os.path.join(REPOS, name + ".git")):
        name, n = f"{base}-{n}", n + 1
    server = os.path.join(REPOS, name + ".git")
    os.makedirs(REPOS, exist_ok=True)

    course = load_course()
    starter = os.path.join(ENGINE, "starters", lang)
    tmp = tempfile.mkdtemp(prefix="shellsmith-init-")
    try:
        work = os.path.join(tmp, "repo")
        shutil.copytree(starter, work)
        build_note = "- `build.sh` compiles your code; the tester runs it before every test run.\n" \
            if os.path.exists(os.path.join(work, "build.sh")) else ""
        with open(os.path.join(work, "README.md"), "w") as f:
            f.write(README.format(lang_name=LANGS[lang], total=len(course), build_note=build_note))
        with open(os.path.join(work, "shellsmith.json"), "w") as f:
            json.dump({"challenge": "shell", "language": lang}, f, indent=2)
            f.write("\n")
        with open(os.path.join(work, ".gitignore"), "w") as f:
            f.write(".smith/\napp/target/\n__pycache__/\n*.pyc\n.DS_Store\n")
        ident = ["-c", "user.name=Shellsmith", "-c", "user.email=shellsmith@localhost"]
        git("init", "-q", "-b", "main", cwd=work)
        git("add", "-A", cwd=work)
        git(*ident, "commit", "-q", "-m", "Starter code", cwd=work)
        git("init", "-q", "--bare", "-b", "main", server)
        git("push", "-q", server, "main", cwd=work)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # Installed after the first push so the starter code isn't graded.
    hook = os.path.join(server, "hooks", "post-receive")
    with open(hook, "w") as f:
        f.write(f'#!/bin/sh\nexec "{sys.executable}" "{os.path.join(ENGINE, "hook.py")}"\n')
    os.chmod(hook, 0o755)
    os.makedirs(os.path.join(server, "shellsmith"), exist_ok=True)

    folder = f"shellsmith-{name}"
    home = os.path.expanduser("~")
    shown = "~" + server[len(home):] if server.startswith(home + os.sep) else server
    print(green("✔") + f" Created your {LANGS[lang]} shell challenge.\n")
    print("Clone it and start building:\n")
    print("  " + cyan(f"git clone {shown} {folder}"))
    print("  " + cyan(f"cd {folder}"))
    print("  " + cyan("shellsmith stage"))
    print(dim(f"\nEvery `git push` (or `shellsmith submit`) from that folder runs the tests."))


# ------------------------------------------------------------------ stage / status / list
def cmd_stage(args):
    course = load_course()
    ws = find_workspace()
    if args:
        hit = [s for s in course if args[0] in (s["slug"], str(s["number"]))]
        if not hit:
            die(f"No stage {args[0]!r}.", f"See all of them with {cyan('shellsmith status')}.")
        s = hit[0]
    else:
        i = current_index(course, ws)
        if i >= len(course):
            print(green("🎉 You've passed every stage."))
            return
        s = course[i]
    print(bold(f"Stage {s['number']}/{len(course)} · {plain(s['title'])}") + dim(f"   {s['chapter']} · {s['difficulty']}"))
    print(dim("─" * 60))
    print(render_md(s["body"]))
    print(dim("─" * 60))
    print(dim("Test it: ") + cyan("shellsmith test") + dim("   Submit: ") + cyan("shellsmith submit"))


def cmd_status(_):
    ws = need_workspace()
    course = load_course()
    server = server_of(ws)
    p = progress_of(server)
    cur = current_index(course, ws)
    best = p.get("best", 0)
    chapter = None
    for i, s in enumerate(course):
        if s["chapter"] != chapter:
            chapter = s["chapter"]
            print("\n" + bold(chapter))
        if i < cur:
            mark, title = green("✔"), plain(s["title"])
        elif i == cur:
            mark, title = yellow("➜"), bold(plain(s["title"]))
        else:
            mark, title = dim("·"), dim(plain(s["title"]))
        print(f"  {mark} {s['number']:>2}. {title}")
    print()
    print(f"{bold(str(min(cur, len(course))))}/{len(course)} stages passed" +
          (dim(f" (best ever: {best})") if best > cur else ""))
    subs = p.get("submissions", [])
    if subs:
        print(dim("\nRecent submissions:"))
        for sub in subs[-5:][::-1]:
            print(dim(f"  {sub['at'].replace('T', ' ')}  {sub['sha'][:7]}  {sub['passed']} passed"))
    if not server:
        print(yellow("\n! This folder's origin isn't a Shellsmith server, so pushes aren't graded."))


def cmd_list(_):
    if not os.path.isdir(REPOS) or not os.listdir(REPOS):
        print("No challenges yet. Start one with " + cyan("shellsmith start python"))
        return
    total = len(load_course())
    for d in sorted(os.listdir(REPOS)):
        p = progress_of(os.path.join(REPOS, d))
        passed = (p.get("last") or {}).get("passed", 0)
        print(f"  {bold(d[:-4]):<24} {passed:>2}/{total}   " + dim(os.path.join(REPOS, d)))


def cmd_languages(_):
    for k, v in LANGS.items():
        ok = green("✔") if shutil.which(TOOLS[k]) else dim("·")
        print(f"  {ok} {k:<11} {v}" + ("" if shutil.which(TOOLS[k]) else dim(f"   (needs {TOOLS[k]})")))
    print(dim("\nStart one with: shellsmith start LANGUAGE"))


# ------------------------------------------------------------------ test / submit
IGNORE = {".git", ".smith", "target", "__pycache__", "node_modules"}


def snapshot(ws):
    snap = {}
    for dp, dirs, files in os.walk(ws):
        dirs[:] = [d for d in dirs if d not in IGNORE]
        for f in files:
            try:
                snap[os.path.join(dp, f)] = os.stat(os.path.join(dp, f)).st_mtime_ns
            except OSError:
                pass
    return snap


def run_tester(ws, stage, extra):
    cmd = [sys.executable, os.path.join(ENGINE, "tester", "run.py"), "--solution", ws] + extra
    if stage:
        cmd += ["--only", stage]
    return subprocess.call(cmd, cwd=ws)


def cmd_test(args):
    ws = need_workspace()
    watch = any(a in ("-w", "--watch") for a in args)
    args = [a for a in args if a not in ("-w", "--watch")]
    extra, stage, i = [], None, 0
    while i < len(args):
        if args[i] in ("--seed", "--jobs") and i + 1 < len(args):
            extra += args[i:i + 2]
            i += 2
        else:
            stage, i = args[i], i + 1
    if not watch:
        code = run_tester(ws, stage, extra)
        if code == 0 and not stage:
            print(dim("Looks good. Submit it with ") + cyan("shellsmith submit"))
        sys.exit(code)
    snap = None
    try:
        while True:
            now = snapshot(ws)
            if now != snap:
                snap = now
                if COLOR:
                    print("\033[2J\033[H", end="")
                print(dim(time.strftime("%H:%M:%S") + "  watching for changes, Ctrl-C to stop\n"))
                run_tester(ws, stage, extra)
            time.sleep(0.4)
    except KeyboardInterrupt:
        print()


def cmd_submit(args):
    ws = need_workspace()
    msg = " ".join(args) or "shellsmith submit"
    if not server_of(ws):
        print(yellow("! origin isn't a Shellsmith server; pushing anyway, but it won't be graded."))
    git("add", "-A", cwd=ws)
    ident = []
    if not git("config", "user.email", cwd=ws, check=False):
        ident = ["-c", "user.name=Shellsmith learner", "-c", "user.email=learner@shellsmith.local"]
    changed = bool(git("status", "--porcelain", cwd=ws))
    git(*ident, "commit", "-q", "-m", msg, *([] if changed else ["--allow-empty"]), cwd=ws)
    print(green("✔ ") + (f"Committed: {msg}" if changed else "No changes; re-submitting your last commit."))
    branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=ws)
    code = subprocess.call(["git", "push", "origin", f"{branch}:main"], cwd=ws)
    if code != 0:
        die("git push failed (see above).")


COMMANDS = {"start": cmd_start, "stage": cmd_stage, "test": cmd_test, "submit": cmd_submit,
            "status": cmd_status, "list": cmd_list, "languages": cmd_languages}


def main():
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `shellsmith stage | less` quits cleanly
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__.strip())
        return
    fn = COMMANDS.get(sys.argv[1])
    if not fn:
        die(f"Unknown command {sys.argv[1]!r}.", f"Run {cyan('shellsmith help')} for the list.")
    try:
        fn(sys.argv[2:])
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
