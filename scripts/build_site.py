#!/usr/bin/env python3
"""Build the dashboard website (site/ + course + results) into one folder for GitHub Pages.

  python3 scripts/build_site.py --results results.json --out _site
  python3 scripts/build_site.py --summary results.json      # markdown for the Actions summary
"""
import argparse
import html
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tester"))
from run import load_course  # noqa: E402


def inline(text):
    text = html.escape(text, quote=False)
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            out.append(f"<code>{p[1:-1]}</code>")
        else:
            p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
            p = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", p)
            p = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', p)
            out.append(p)
    return "".join(out)


def markdown(md):
    lines, out, i = md.split("\n"), [], 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            out.append(f"<pre><code>{html.escape(chr(10).join(code), quote=False)}</code></pre>")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            lvl = min(len(m.group(1)) + 1, 6)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if re.match(r"^\s*(-|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.", line))
            items = []
            while i < len(lines) and re.match(r"^\s*(-|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*(-|\d+\.)\s+", "", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if not line.strip():
            i += 1
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(```|#|\s*(-|\d+\.)\s)", lines[i]):
            para.append(lines[i])
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


def summary(results_path):
    course = load_course()
    try:
        with open(results_path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        print("## Shellsmith\n\nThe tester did not produce results. Check the *Run the tester* step log.")
        return
    passed = data.get("passed") or 0
    print(f"## Shellsmith — {passed}/{len(course)} stages\n")
    done = {r["slug"]: r for r in data["results"]}
    print("| # | Stage | Result |\n|---|---|---|")
    for s in course:
        r = done.get(s["slug"])
        mark = "✅ passed" if r and r["passed"] else ("❌ failed" if r else "🔒 locked")
        print(f"| {s['number']} | {s['title']} | {mark} |")
    failed = [r for r in data["results"] if not r["passed"]]
    if failed:
        print(f"\n**Stage {failed[0]['number']} failed:**\n\n```\n{failed[0]['error']}\n```")


def build(results_path, out):
    course = load_course()
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(os.path.join(ROOT, "site"), out)
    stages = [{k: s[k] for k in ("slug", "number", "title", "chapter", "difficulty")} | {"html": markdown(s["body"])}
              for s in course]
    with open(os.path.join(out, "stages.json"), "w") as f:
        json.dump(stages, f)
    data = None
    if results_path and os.path.exists(results_path):
        with open(results_path) as f:
            data = json.load(f)
    if data is None:
        data = {"total": len(course), "passed": 0, "current": course[0]["slug"], "results": [],
                "repository": os.environ.get("GITHUB_REPOSITORY"), "commit": None, "generated_at": None}
    with open(os.path.join(out, "results.json"), "w") as f:
        json.dump(data, f)
    open(os.path.join(out, ".nojekyll"), "w").close()
    print(f"Built dashboard in {out}/ ({len(stages)} stages)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results")
    p.add_argument("--out", default="_site")
    p.add_argument("--summary")
    a = p.parse_args()
    if a.summary:
        summary(a.summary)
    else:
        build(a.results, a.out)


if __name__ == "__main__":
    main()
