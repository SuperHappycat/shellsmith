#!/usr/bin/env python3
"""Shellsmith post-receive hook: runs the tests on every `git push`.

Installed into each challenge repository (the "server" that `shellsmith start` creates).
Everything this prints appears in the pusher's terminal as `remote: ...` lines, live.
"""
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile

ENGINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ENGINE, "tester"))
from run import load_course  # noqa: E402

ZERO = "0" * 40
C = {"bold": "\033[1m", "green": "\033[32m", "red": "\033[31m", "yellow": "\033[33m", "cyan": "\033[36m",
     "dim": "\033[90m", "off": "\033[0m"}


def paint(color, text):
    return f"{C[color]}{text}{C['off']}"


def say(text=""):
    print(text, flush=True)


def load_progress(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"best": 0, "current": None, "submissions": []}


def excerpt(md, limit=4):
    """First few prose lines of a stage, for the 'next stage' teaser."""
    out = []
    for line in md.splitlines():
        if line.startswith(("```", "#")) or (not line.strip() and out):
            break
        if line.strip():
            out.append(line.strip())
        if len(out) >= limit:
            break
    return " ".join(out).replace("**", "").replace("`", "")


def main():
    git_dir = os.path.abspath(os.environ.get("GIT_DIR", "."))
    updates = [l.split() for l in sys.stdin.read().splitlines() if l.strip()]
    target = next((u for u in updates if u[1] != ZERO and u[2] in ("refs/heads/main", "refs/heads/master")), None)
    if not target:
        return
    sha = target[1]
    course = load_course()
    prog_path = os.path.join(git_dir, "shellsmith", "progress.json")
    progress = load_progress(prog_path)

    work = tempfile.mkdtemp(prefix="shellsmith-submit-")
    try:
        # Check out exactly what was pushed (not the pusher's working tree).
        archive = subprocess.run(["git", "--git-dir", git_dir, "archive", sha], stdout=subprocess.PIPE, check=True)
        subprocess.run(["tar", "-x", "-C", work], input=archive.stdout, check=True)

        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["SMITH_COLOR"] = "1"
        env["SMITH_HOOK"] = "1"
        say(paint("dim", "─" * 60))
        say(paint("bold", f"Shellsmith: testing {sha[:7]}"))
        say(paint("dim", "─" * 60))
        results_file = os.path.join(work, ".shellsmith-results.json")
        subprocess.run([sys.executable, "-u", os.path.join(ENGINE, "tester", "run.py"),
                        "--solution", work, "--json", results_file], cwd=work, env=env)
        try:
            with open(results_file) as f:
                res = json.load(f)
        except (OSError, ValueError):
            say(paint("red", "The tester crashed before producing results. Please report this."))
            return
    finally:
        shutil.rmtree(work, ignore_errors=True)

    passed = res.get("passed") or 0
    before = progress.get("best", 0)
    progress["best"] = max(before, passed)
    progress["current"] = res.get("current")
    progress["last"] = {"passed": passed, "sha": sha, "build_error": bool(res.get("build_error"))}
    progress["submissions"] = (progress.get("submissions", []) + [{
        "sha": sha, "at": datetime.datetime.now().isoformat(timespec="seconds"), "passed": passed,
        "seconds": res.get("seconds")}])[-50:]
    os.makedirs(os.path.dirname(prog_path), exist_ok=True)
    with open(prog_path, "w") as f:
        json.dump(progress, f, indent=1)

    total = len(course)
    say()
    bar_len = 30
    fill = round(bar_len * passed / total)
    say(f"  {paint('green', '█' * fill)}{paint('dim', '░' * (bar_len - fill))}  {passed}/{total} stages")
    say()
    if res.get("build_error"):
        say(paint("red", "  ✘ Your code didn't compile. Fix the error above and push again."))
    elif passed == total:
        say(paint("green", "  🎉 Every stage passes. You built a shell. Congratulations!"))
    else:
        nxt = course[passed]
        if passed > before:
            newly = passed - before
            say(paint("green", f"  ✔ {newly} new stage{'s' if newly != 1 else ''} passed. Nice work!"))
            say()
            say(paint("bold", f"  Up next: stage {nxt['number']} · {nxt['title'].replace('`', '')}"))
            say(paint("dim", f"  {excerpt(nxt['body'])}"))
            say()
            say(f"  Read the full stage:  {paint('cyan', 'shellsmith stage')}")
        else:
            say(paint("red", f"  ✘ Stage {nxt['number']} ({nxt['title'].replace('`', '')}) isn't passing yet."))
            if passed < before:
                say(paint("yellow", f"  Heads up: stage {passed + 1} passed before but fails now (you reached {before})."))
            say(f"  Test without pushing:  {paint('cyan', 'shellsmith test')}")
    say(paint("dim", "─" * 60))


if __name__ == "__main__":
    main()
