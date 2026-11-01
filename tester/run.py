#!/usr/bin/env python3
"""Shellsmith tester. Runs stages in order and stops at the first one that fails.

  python3 tester/run.py                    # run until the first failing stage
  python3 tester/run.py --only cd-home     # run a single stage (slug or number)
  python3 tester/run.py --json out.json    # also write machine-readable results
  python3 tester/run.py --jobs 1           # no parallelism (slow machines / debugging)

Stages are independent (fresh temp dirs and shell processes), so they run in
parallel worker processes; results are still reported strictly in order.
"""
import argparse
import concurrent.futures as cf
import datetime
import json
import multiprocessing as mp
import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from harness import Log, StageFailed, print_log  # noqa: E402
from stages import TESTS, Ctx  # noqa: E402


def load_course():
    """Read stage metadata from course/stages/NN-slug.md front matter."""
    d = os.path.join(ROOT, "course", "stages")
    stages = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".md"):
            continue
        with open(os.path.join(d, fn), encoding="utf-8") as f:
            text = f.read()
        meta, body = {}, text
        if text.startswith("---"):
            head, body = text[3:].split("\n---", 1)
            for line in head.strip().splitlines():
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        meta["number"] = len(stages) + 1
        meta["body"] = body.strip()
        stages.append(meta)
    return stages


def run_build():
    """Compile the learner's shell once (if the chosen language has a build.sh)."""
    script = os.path.join(ROOT, "build.sh")
    if not os.path.exists(script):
        return None
    print("Building your shell (build.sh)…", flush=True)
    t0 = time.monotonic()
    r = subprocess.run(["sh", script], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        return (r.stdout or "").strip()[-4000:] or f"build.sh exited with status {r.returncode}"
    print(f"Built in {time.monotonic() - t0:.1f}s\n", flush=True)
    return None


def run_stage(stage, program, seed):
    random.seed(f"{seed}:{stage['slug']}")
    log = Log(f"stage {stage['number']}")
    log.info(stage["title"].replace("`", ""))
    ctx = Ctx(program, log)
    started = time.monotonic()
    try:
        TESTS[stage["slug"]](ctx)
        passed, error = True, None
        log.ok("Stage passed")
    except StageFailed as e:
        passed, error = False, str(e)
        log.fail(error)
    except Exception as e:  # tester bug or unexpected crash
        passed, error = False, f"Tester error: {type(e).__name__}: {e}"
        log.fail(error)
    finally:
        ctx.cleanup()
    return {"slug": stage["slug"], "number": stage["number"], "title": stage["title"],
            "chapter": stage.get("chapter"), "passed": passed, "error": error,
            "seconds": round(time.monotonic() - started, 2), "log": log.lines}


def run_all(todo, program, seed, jobs, color, quiet):
    """Run stages, print each one's log in order, stop reporting at the first failure."""
    results = []

    def report(r):
        results.append(r)
        if not quiet:
            print_log(r["log"], color)
        return r["passed"]

    if jobs <= 1 or len(todo) == 1:
        for st in todo:
            if not report(run_stage(st, program, seed)):
                break
        return results

    ctx = mp.get_context("fork" if sys.platform.startswith("linux") else "spawn")
    with cf.ProcessPoolExecutor(max_workers=jobs, mp_context=ctx) as pool:
        futures = [pool.submit(run_stage, st, program, seed) for st in todo]
        try:
            for fut in futures:
                if not report(fut.result()):
                    break
        finally:
            for f in futures:
                f.cancel()
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--program", default=os.path.join(ROOT, "your_shell.sh"))
    p.add_argument("--only", help="run just this stage (slug or number)")
    p.add_argument("--json", help="write results to this file")
    p.add_argument("--seed", default=None, help="fix the random words (reproduce a run)")
    p.add_argument("--jobs", type=int, default=int(os.environ.get("SMITH_JOBS", min(8, os.cpu_count() or 2))))
    a = p.parse_args()

    seed = a.seed or str(random.randrange(10**6))
    color = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    quiet = os.environ.get("SMITH_QUIET") == "1"

    course = load_course()
    missing = [s["slug"] for s in course if s["slug"] not in TESTS]
    if missing:
        sys.exit(f"Tester has no test for: {missing}")
    if not os.access(a.program, os.X_OK):
        sys.exit(f"{a.program} is not executable. Run: chmod +x {a.program}")

    todo = course
    if a.only:
        todo = [s for s in course if a.only in (s["slug"], str(s["number"]))]
        if not todo:
            sys.exit(f"No stage called {a.only!r}")

    build_error = run_build()
    if build_error:
        print(build_error)
        print("\nYour shell did not compile, so no stages were run.")
        if a.json:
            with open(a.json, "w") as f:
                json.dump({"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                           "repository": os.environ.get("GITHUB_REPOSITORY"), "commit": os.environ.get("GITHUB_SHA"),
                           "run_id": os.environ.get("GITHUB_RUN_ID"), "total": len(course), "passed": 0,
                           "current": course[0]["slug"], "build_error": build_error, "results": []}, f, indent=1)
        sys.exit(1)

    t0 = time.monotonic()
    results = run_all(todo, a.program, seed, a.jobs, color, quiet)
    elapsed = time.monotonic() - t0

    passed = [r for r in results if r["passed"]]
    current = None
    if not a.only:
        done = len(passed)
        current = course[done]["slug"] if done < len(course) else None

    if a.json:
        with open(a.json, "w") as f:
            json.dump({
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                "repository": os.environ.get("GITHUB_REPOSITORY"),
                "commit": os.environ.get("GITHUB_SHA"),
                "run_id": os.environ.get("GITHUB_RUN_ID"),
                "seed": seed,
                "seconds": round(elapsed, 1),
                "total": len(course),
                "passed": len(passed) if not a.only else None,
                "current": current,
                "results": results,
            }, f, indent=1)

    tail = f"  [{elapsed:.1f}s, seed {seed}]"
    if a.only:
        print(("Passed." if results[0]["passed"] else "Failed.") + tail)
        sys.exit(0 if results[0]["passed"] else 1)
    if current is None:
        print(f"\U0001F389  All {len(course)} stages pass. You built a shell!" + tail)
        sys.exit(0)
    cur = course[len(passed)]
    print(f"Stopped at stage {cur['number']}: {cur['title'].replace('`', '')}  "
          f"({len(passed)}/{len(course)} done)" + tail)
    print("Read the instructions with:  ./smith stage")
    sys.exit(1)


if __name__ == "__main__":
    main()
