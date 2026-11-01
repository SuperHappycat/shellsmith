import os
import readline
import subprocess
import sys

BUILTINS = ["echo", "exit", "type", "pwd", "cd", "history", "export"]
HISTORY = []
STATE = {"status": 0, "appended": 0}
OPS = ("|", "&&", "||", ";")
NAME_START = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"


def expand(line, i):
    """line[i] == '$'. Returns (value, new_i)."""
    j = i + 1
    if j < len(line) and line[j] == "?":
        return str(STATE["status"]), j + 1
    if j < len(line) and line[j] == "{":
        k = line.index("}", j)
        return os.environ.get(line[j + 1:k], ""), k + 1
    k = j
    if k < len(line) and line[k] in NAME_START:
        while k < len(line) and (line[k].isalnum() or line[k] == "_"):
            k += 1
        return os.environ.get(line[j:k], ""), k
    return "$", j


def tokenize(line):
    out, cur, i, have = [], "", 0, False

    def flush():
        nonlocal cur, have
        if have:
            out.append(cur)
        cur, have = "", False

    while i < len(line):
        c = line[i]
        if c == "'":
            j = line.index("'", i + 1)
            cur += line[i + 1:j]; i = j + 1; have = True; continue
        if c == '"':
            i += 1
            while line[i] != '"':
                if line[i] == "\\" and line[i + 1] in '"\\$`\n':
                    cur += line[i + 1]; i += 2
                elif line[i] == "$":
                    v, i = expand(line, i); cur += v
                else:
                    cur += line[i]; i += 1
            i += 1; have = True; continue
        if c == "\\":
            cur += line[i + 1]; i += 2; have = True; continue
        if c == "$":
            v, i = expand(line, i)
            if v:
                cur += v; have = True
            continue
        if c in " \t":
            flush(); i += 1; continue
        two = line[i:i + 2]
        if two in ("&&", "||"):
            flush(); out.append((two,)); i += 2; continue
        if c in "|;":
            flush(); out.append((c,)); i += 1; continue
        cur += c; have = True; i += 1
    flush()
    return out


def find_exe(name):
    for d in os.environ.get("PATH", "").split(":"):
        p = os.path.join(d, name)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def parse_redirs(args):
    red, rest, i = {}, [], 0
    while i < len(args):
        a = args[i]
        if a in (">", "1>", ">>", "1>>", "2>", "2>>"):
            fd = 2 if a.startswith("2") else 1
            red[fd] = (args[i + 1], "a" if a.endswith(">>") else "w")
            i += 2
        else:
            rest.append(a); i += 1
    return rest, red


def save_history(path, items):
    with open(path, "a") as f:
        for h in items:
            f.write(h + "\n")


def builtin(args, out, err):
    cmd = args[0]
    status = 0
    if cmd == "echo":
        out.write(" ".join(args[1:]) + "\n")
    elif cmd == "type":
        for n in args[1:]:
            if n in BUILTINS:
                out.write(f"{n} is a shell builtin\n")
            elif (p := find_exe(n)):
                out.write(f"{n} is {p}\n")
            else:
                out.write(f"{n}: not found\n"); status = 1
    elif cmd == "pwd":
        out.write(os.getcwd() + "\n")
    elif cmd == "cd":
        raw = args[1] if len(args) > 1 else "~"
        try:
            os.chdir(os.path.expanduser(raw))
        except OSError:
            err.write(f"cd: {raw}: No such file or directory\n"); status = 1
    elif cmd == "export":
        for a in args[1:]:
            if "=" in a:
                k, v = a.split("=", 1)
                os.environ[k] = v
    elif cmd == "history":
        if len(args) > 2 and args[1] in ("-r", "-w", "-a"):
            flag, path = args[1], args[2]
            if flag == "-r":
                with open(path) as f:
                    for l in f.read().splitlines():
                        if l.strip():
                            HISTORY.append(l); readline.add_history(l)
            elif flag == "-w":
                open(path, "w").close(); save_history(path, HISTORY)
                STATE["appended"] = len(HISTORY)
            else:
                save_history(path, HISTORY[STATE["appended"]:])
                STATE["appended"] = len(HISTORY)
        else:
            items = list(enumerate(HISTORY, 1))
            if len(args) > 1:
                items = items[-int(args[1]):]
            for n, h in items:
                out.write(f"{n:5d}  {h}\n")
    elif cmd == "exit":
        hf = os.environ.get("HISTFILE")
        if hf:
            open(hf, "w").close(); save_history(hf, HISTORY)
        sys.exit(int(args[1]) if len(args) > 1 else STATE["status"])
    out.flush(); err.flush()
    return status


def run_pipeline(stages):
    procs, prev_r, status = [], None, 0
    for idx, args in enumerate(stages):
        last = idx == len(stages) - 1
        args, red = parse_redirs(args)
        r, wfd = (None, None) if last else os.pipe()
        if args[0] in BUILTINS:
            out = open(red[1][0], red[1][1]) if 1 in red else (os.fdopen(wfd, "w") if wfd else sys.stdout)
            err = open(red[2][0], red[2][1]) if 2 in red else sys.stderr
            status = builtin(args, out, err)
            if out is not sys.stdout: out.close()
            if err is not sys.stderr: err.close()
            if prev_r is not None: os.close(prev_r)
        else:
            path = find_exe(args[0])
            if not path:
                print(f"{args[0]}: command not found", flush=True)
                status = 127
                if wfd: os.close(wfd)
                if prev_r is not None: os.close(prev_r)
            else:
                kw = {}
                if 1 in red: kw["stdout"] = open(red[1][0], red[1][1])
                elif wfd: kw["stdout"] = wfd
                if 2 in red: kw["stderr"] = open(red[2][0], red[2][1])
                if prev_r is not None: kw["stdin"] = prev_r
                procs.append((last, subprocess.Popen([args[0]] + args[1:], executable=path, **kw)))
                for v in kw.values():
                    if isinstance(v, int): os.close(v)
                    else: v.close()
        prev_r = r
    for is_last, p in procs:
        rc = p.wait()
        if is_last:
            status = rc
    return status


def split_lists(line):
    """Split at top-level ; && || (outside quotes) -> [(connector, text)]."""
    parts, cur, conn, i, q = [], "", None, 0, None
    while i < len(line):
        c = line[i]
        if q:
            if c == "\\" and q == '"' and i + 1 < len(line):
                cur += line[i:i + 2]; i += 2; continue
            if c == q:
                q = None
            cur += c; i += 1; continue
        if c in "'\"":
            q = c; cur += c; i += 1; continue
        if c == "\\":
            cur += line[i:i + 2]; i += 2; continue
        two = line[i:i + 2]
        if two in ("&&", "||") or c == ";":
            parts.append((conn, cur)); conn = two if two in ("&&", "||") else ";"
            cur = ""; i += 2 if conn != ";" else 1; continue
        cur += c; i += 1
    parts.append((conn, cur))
    return [(c, t) for c, t in parts if t.strip()]


def run_line(line):
    for conn, text in split_lists(line):
        if conn == "&&" and STATE["status"] != 0:
            continue
        if conn == "||" and STATE["status"] == 0:
            continue
        stages, cur = [], []
        for t in tokenize(text):      # expand variables now, not when the line was read
            if t == ("|",):
                stages.append(cur); cur = []
            else:
                cur.append(t)
        stages.append(cur)
        STATE["status"] = run_pipeline(stages)


def completer(text, state):
    names = set(b for b in BUILTINS if b.startswith(text))
    for d in os.environ.get("PATH", "").split(":"):
        try:
            for f in os.listdir(d):
                if f.startswith(text) and os.access(os.path.join(d, f), os.X_OK):
                    names.add(f)
        except OSError:
            pass
    m = sorted(names)
    if len(m) == 1:
        m = [m[0] + " "]
    return m[state] if state < len(m) else None


def main():
    readline.set_completer(completer)
    readline.set_completer_delims(" \t\n")
    readline.parse_and_bind("tab: complete")
    hf = os.environ.get("HISTFILE")
    if hf and os.path.exists(hf):
        with open(hf) as f:
            for l in f.read().splitlines():
                if l.strip():
                    HISTORY.append(l); readline.add_history(l)
        STATE["appended"] = len(HISTORY)
    while True:
        try:
            line = input("$ ")
        except EOFError:
            break
        if not line.strip():
            continue
        HISTORY.append(line)
        run_line(line)


main()
