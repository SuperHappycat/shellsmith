"""Stage tests. Each test gets a Ctx and raises StageFailed on the first mismatch."""
import os
import random
import shutil
import stat
import subprocess
import tempfile

from harness import Shell, StageFailed

WORDS = ["mango", "papaya", "lychee", "durian", "tamarind", "pomelo", "rambutan", "longan",
         "guava", "banana", "coconut", "jackfruit", "starfruit", "lime", "ginger", "pepper",
         "orchid", "lotus", "teak", "bamboo", "river", "valley", "summit", "lantern", "monsoon"]


def w(n=1):
    return random.sample(WORDS, n) if n > 1 else random.choice(WORDS)


def tok():
    return f"{random.randint(100, 999)}"


class Ctx:
    def __init__(self, program, log):
        self.program = os.path.abspath(program)
        self.log = log
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="smith-"))
        self.home = os.path.join(self.root, "home")
        self.bin = os.path.join(self.root, "bin")
        self.work = os.path.join(self.root, "work")
        for d in (self.home, self.bin, self.work):
            os.makedirs(d)
        base_path = os.environ.get("PATH", "/usr/bin:/bin")
        self.env = {
            "PATH": f"{self.bin}:{base_path}",
            "HOME": self.home,
            "TERM": "xterm",
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "INPUTRC": "/dev/null",
        }
        self.shells = []

    # ---- helpers
    def shell(self, cwd=None, env=None):
        e = dict(self.env)
        e.update(env or {})
        self.log.dim("Starting your shell")
        s = Shell([self.program], cwd or self.work, e, self.log)
        self.shells.append(s)
        s.expect_prompt()
        return s

    def exe(self, name, body, directory=None):
        path = os.path.join(directory or self.bin, name)
        with open(path, "w") as f:
            f.write("#!/bin/sh\n" + body + "\n")
        os.chmod(path, 0o755)
        return path

    def arg_printer(self, name, directory=None):
        """An executable that prints a secret token and every argument it gets."""
        secret = tok()
        body = (f'echo "secret: {secret}"\n'
                'echo "arg0: $(basename "$0")"\n'
                'i=1; for a in "$@"; do echo "arg$i: $a"; i=$((i+1)); done')
        self.exe(name, body, directory)
        return secret

    def file(self, rel, content):
        path = os.path.join(self.work, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return path

    def real_sh(self, cmd, cwd=None):
        """What a real POSIX shell prints (stdout+stderr) for cmd, used as the reference answer."""
        out = subprocess.run(["sh", "-c", cmd], cwd=cwd or self.work, env=self.env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return [l.rstrip() for l in out.stdout.rstrip("\n").split("\n")] if out.stdout else []

    def cleanup(self):
        for s in self.shells:
            s.close()
        shutil.rmtree(self.root, ignore_errors=True)


def check(log, cmd, got, want):
    got = [l.rstrip() for l in got]
    want = [l.rstrip() for l in want]
    if got != want:
        fmt = lambda ls: "\n".join(f"    {l!r}" for l in ls) or "    (nothing)"
        raise StageFailed(f'Wrong output for "{cmd}".\n  Expected:\n{fmt(want)}\n  Got:\n{fmt(got)}')
    log.ok(f"Output matched ({len(want)} line{'s' if len(want) != 1 else ''})")


def run_check(ctx, sh, cmd, want):
    check(ctx.log, cmd, sh.run(cmd), want)


def check_file(log, path, want, label):
    if not os.path.exists(path):
        raise StageFailed(f"Expected {label} to exist at {path}, but it does not.")
    with open(path) as f:
        got = f.read()
    if got != want:
        raise StageFailed(f"{label} has the wrong contents.\n  Expected: {want!r}\n  Got:      {got!r}")
    log.ok(f"{label} contains the right text")


# =================================================================== Basics
def t_prompt(ctx):
    ctx.shell()
    ctx.log.ok('Saw the prompt "$ "')


def t_not_found(ctx):
    sh = ctx.shell()
    cmd = f"{w()}_{tok()}"
    sh.send(cmd + "\n")
    ctx.log.info(f"Typing: {cmd}")
    text = sh.wait_for(lambda s: f"{cmd}: command not found" in s, f'"{cmd}: command not found"')
    sh._mirror()
    ctx.log.ok("Got the right error message")


def t_repl(ctx):
    sh = ctx.shell()
    for _ in range(3):
        cmd = f"{w()}_{tok()}"
        run_check(ctx, sh, cmd, [f"{cmd}: command not found"])
    ctx.log.ok("The prompt came back after every command")


def t_exit(ctx):
    for code in (0, random.randint(1, 9)):
        sh = ctx.shell()
        sh.type_keys(f"exit {code}\n", f"exit {code}")
        got = sh.expect_exit()
        if got != code:
            raise StageFailed(f"Expected exit status {code}, got {got}")
        ctx.log.ok(f"Shell exited with status {code}")


def t_echo(ctx):
    sh = ctx.shell()
    a, b, c = w(3)
    run_check(ctx, sh, f"echo {a}", [a])
    run_check(ctx, sh, f"echo {a} {b} {c}", [f"{a} {b} {c}"])
    run_check(ctx, sh, f"echo   {a}     {b}", [f"{a} {b}"])
    run_check(ctx, sh, "echo", [""])


def t_type_builtin(ctx):
    sh = ctx.shell()
    for b in ("echo", "exit", "type"):
        run_check(ctx, sh, f"type {b}", [f"{b} is a shell builtin"])
    bogus = f"{w()}_{tok()}"
    run_check(ctx, sh, f"type {bogus}", [f"{bogus}: not found"])


def t_type_path(ctx):
    d1 = os.path.join(ctx.root, "decoy")
    d2 = os.path.join(ctx.root, "real")
    os.makedirs(d1); os.makedirs(d2)
    name = f"{w()}_tool"
    with open(os.path.join(d1, name), "w") as f:   # present but NOT executable: must be skipped
        f.write("#!/bin/sh\n")
    ctx.exe(name, "echo hi", d2)
    sh = ctx.shell(env={"PATH": f"{d1}:{d2}:{ctx.env['PATH']}"})
    run_check(ctx, sh, f"type {name}", [f"{name} is {os.path.join(d2, name)}"])
    for prog in ("cat", "ls"):
        found = shutil.which(prog, path=f"{d1}:{d2}:{ctx.env['PATH']}")
        run_check(ctx, sh, f"type {prog}", [f"{prog} is {found}"])
    run_check(ctx, sh, "type echo", ["echo is a shell builtin"])


def t_run_program(ctx):
    name = f"{w()}_{tok()}"
    secret = ctx.arg_printer(name)
    sh = ctx.shell()
    a, b = w(2)
    run_check(ctx, sh, f"{name} {a} {b}",
              [f"secret: {secret}", f"arg0: {name}", f"arg1: {a}", f"arg2: {b}"])
    run_check(ctx, sh, name, [f"secret: {secret}", f"arg0: {name}"])


# =================================================================== Navigation
def t_pwd(ctx):
    sh = ctx.shell()
    run_check(ctx, sh, "pwd", [ctx.work])
    run_check(ctx, sh, "type pwd", ["pwd is a shell builtin"])


def t_cd_absolute(ctx):
    target = os.path.join(ctx.root, w(), w())
    os.makedirs(target)
    sh = ctx.shell()
    check(ctx.log, "cd", sh.run(f"cd {target}"), [])
    run_check(ctx, sh, "pwd", [target])
    missing = f"/{w()}-{tok()}/nowhere"
    run_check(ctx, sh, f"cd {missing}", [f"cd: {missing}: No such file or directory"])
    run_check(ctx, sh, "pwd", [target])


def t_cd_relative(ctx):
    a, b, c = w(3)
    os.makedirs(os.path.join(ctx.work, a, b, c))
    sh = ctx.shell()
    sh.run(f"cd ./{a}/{b}")
    run_check(ctx, sh, "pwd", [os.path.join(ctx.work, a, b)])
    sh.run(f"cd {c}")
    run_check(ctx, sh, "pwd", [os.path.join(ctx.work, a, b, c)])
    sh.run("cd ../..")
    run_check(ctx, sh, "pwd", [os.path.join(ctx.work, a)])


def t_cd_home(ctx):
    sh = ctx.shell()
    sh.run("cd ~")
    run_check(ctx, sh, "pwd", [ctx.home])
    sub = w()
    os.makedirs(os.path.join(ctx.home, sub))
    sh.run(f"cd {ctx.work}")
    sh.run(f"cd ~/{sub}")
    run_check(ctx, sh, "pwd", [os.path.join(ctx.home, sub)])


# =================================================================== Quoting
def t_single_quotes(ctx):
    sh = ctx.shell()
    a, b = w(2)
    run_check(ctx, sh, f"echo '{a}     {b}'", [f"{a}     {b}"])
    run_check(ctx, sh, f"echo '{a}''{b}' {a}", [f"{a}{b} {a}"])
    run_check(ctx, sh, f"echo '{a}\\n{b}'", [f"{a}\\n{b}"])
    fname = f"{a} {b}.txt"
    ctx.file(fname, f"{b}\n")
    run_check(ctx, sh, f"cat '{fname}'", [b])


def t_double_quotes(ctx):
    sh = ctx.shell()
    a, b, c = w(3)
    run_check(ctx, sh, f'echo "{a}   {b}"  "{c}"', [f"{a}   {b} {c}"])
    run_check(ctx, sh, f'echo "{a}\'s {b}"', [f"{a}'s {b}"])
    run_check(ctx, sh, f'echo "{a}"\'{b}\'{c}', [f"{a}{b}{c}"])
    fname = f"it's {c}.txt"
    ctx.file(fname, f"{a}\n")
    run_check(ctx, sh, f'cat "{fname}"', [a])


def t_backslash_bare(ctx):
    sh = ctx.shell()
    a, b = w(2)
    run_check(ctx, sh, f"echo {a}\\ \\ \\ {b}", [f"{a}   {b}"])
    run_check(ctx, sh, f"echo \\'{a}\\' \\\"{b}\\\"", [f"'{a}' \"{b}\""])
    run_check(ctx, sh, f"echo {a}\\n{b}", [f"{a}n{b}"])
    run_check(ctx, sh, f"echo \\\\{a}", [f"\\{a}"])


def t_backslash_double(ctx):
    sh = ctx.shell()
    a, b = w(2)
    run_check(ctx, sh, f'echo "{a}\\"{b}\\""', [f'{a}"{b}"'])
    run_check(ctx, sh, f'echo "{a}\\\\{b}"', [f"{a}\\{b}"])
    run_check(ctx, sh, f'echo "{a}\\n{b}"', [f"{a}\\n{b}"])
    run_check(ctx, sh, f"echo '{a}\\\"{b}'", [f'{a}\\"{b}'])


def t_quoted_exe(ctx):
    a, b = w(2)
    name1 = f"{a} with space"
    name2 = f"{b}'s tool"
    s1 = ctx.arg_printer(name1)
    s2 = ctx.arg_printer(name2)
    sh = ctx.shell()
    run_check(ctx, sh, f"'{name1}' x", [f"secret: {s1}", f"arg0: {name1}", "arg1: x"])
    run_check(ctx, sh, f'"{name2}" "y  z"', [f"secret: {s2}", f"arg0: {name2}", "arg1: y  z"])


# =================================================================== Redirection
def t_redirect_out(ctx):
    sh = ctx.shell()
    a, b = w(2)
    out1 = os.path.join(ctx.root, f"{a}.out")
    check(ctx.log, "echo >", sh.run(f"echo {a} {b} > {out1}"), [])
    check_file(ctx.log, out1, f"{a} {b}\n", out1)
    d = os.path.join(ctx.work, "box")
    for n in sorted(w(3)):
        ctx.file(f"box/{n}", "")
    out2 = os.path.join(ctx.root, f"{b}.out")
    check(ctx.log, "ls 1>", sh.run(f"ls {d} 1> {out2}"), [])
    want = "\n".join(sorted(os.listdir(d))) + "\n"
    check_file(ctx.log, out2, want, out2)
    run_check(ctx, sh, f"cat {out2}", want.rstrip("\n").split("\n"))
    check(ctx.log, "echo > (overwrite)", sh.run(f"echo {b} > {out1}"), [])
    check_file(ctx.log, out1, f"{b}\n", f"{out1} (overwritten)")


def t_redirect_err(ctx):
    sh = ctx.shell()
    a = w()
    missing = f"{a}-{tok()}.txt"
    err = os.path.join(ctx.root, "err.txt")
    check(ctx.log, "cat 2>", sh.run(f"cat {missing} 2> {err}"), [])
    want = "\n".join(ctx.real_sh(f"cat {missing}")) + "\n"
    check_file(ctx.log, err, want, err)
    err2 = os.path.join(ctx.root, "err2.txt")
    run_check(ctx, sh, f"echo {a} 2> {err2}", [a])
    check_file(ctx.log, err2, "", f"{err2} (should be empty)")


def t_append(ctx):
    sh = ctx.shell()
    a, b, c = w(3)
    f1 = os.path.join(ctx.root, "log.txt")
    sh.run(f"echo {a} > {f1}")
    sh.run(f"echo {b} >> {f1}")
    sh.run(f"echo {c} 1>> {f1}")
    check_file(ctx.log, f1, f"{a}\n{b}\n{c}\n", f1)
    f2 = os.path.join(ctx.root, "errors.txt")
    m1, m2 = f"{a}-{tok()}", f"{b}-{tok()}"
    sh.run(f"cat {m1} 2>> {f2}")
    sh.run(f"cat {m2} 2>> {f2}")
    want = "\n".join(ctx.real_sh(f"cat {m1}") + ctx.real_sh(f"cat {m2}")) + "\n"
    check_file(ctx.log, f2, want, f2)
    f3 = os.path.join(ctx.root, f"fresh-{tok()}.txt")
    sh.run(f"echo {c} >> {f3}")
    check_file(ctx.log, f3, f"{c}\n", f"{f3} (created by >>)")


# =================================================================== Completion
def _typed(sh):
    return sh.settle()


def _finish_line(ctx, sh, want_last):
    sh.send("\n")
    text = sh.wait_for(lambda s: "\n" in s and s.endswith("$ "), "the command to finish")
    sh.pos = len(sh.screen)
    sh._mirror()
    lines = text[:-2].rstrip("\n").split("\n")
    if lines[-1].rstrip() != want_last:
        raise StageFailed(f"Expected the command to print {want_last!r} last, got {lines[-1]!r}")
    ctx.log.ok("Completed command ran correctly")


def path_executables(path):
    names = set()
    for d in path.split(":"):
        try:
            for f in os.listdir(d):
                if os.access(os.path.join(d, f), os.X_OK):
                    names.add(f)
        except OSError:
            pass
    return names


def unique_prefix(word, others):
    """Shortest prefix (2+ chars, shorter than word) that only `word` starts with."""
    for n in range(2, len(word)):
        if not any(o != word and o.startswith(word[:n]) for o in others):
            return word[:n]
    return None


def t_complete_builtin(ctx):
    # Real machines have thousands of programs on PATH (CI runners especially), so only
    # test builtins whose prefix is unambiguous on *this* machine.
    others = path_executables(ctx.env["PATH"]) | {"echo", "exit", "type"}
    picks = [(b, unique_prefix(b, others)) for b in ("echo", "exit", "type")]
    picks = [(b, p) for b, p in picks if p]
    if not picks:
        raise StageFailed("Tester problem: every builtin prefix is ambiguous on this machine's PATH")
    sh = ctx.shell()
    for builtin_name, prefix in picks:
        sh.type_keys(prefix + "\t", f"{prefix}<TAB>")
        line = _typed(sh)
        if not line.endswith(builtin_name + " "):
            raise StageFailed(f'Expected the line to become "{builtin_name} " after TAB, screen shows {line!r}')
        ctx.log.ok(f'Line completed to "{builtin_name} "')
        if builtin_name == "exit":
            sh.type_keys("0\n", "0<ENTER>")
            if sh.expect_exit() != 0:
                raise StageFailed("Expected the completed exit command to exit with status 0")
            ctx.log.ok("Completed exit command ran")
            sh = ctx.shell()
        elif builtin_name == "type":
            sh.type_keys("type")
            _finish_line(ctx, sh, "type is a shell builtin")
        else:
            word = w()
            sh.type_keys(word)
            _finish_line(ctx, sh, word)


def t_complete_exe(ctx):
    name = f"zq{tok()}_{w()}"
    secret = ctx.arg_printer(name)
    sh = ctx.shell()
    sh.type_keys(name[:5] + "\t", f"{name[:5]}<TAB>")
    line = _typed(sh)
    if not line.endswith(name + " "):
        raise StageFailed(f'Expected the line to become "{name} " after TAB, screen shows {line!r}')
    ctx.log.ok(f'Line completed to "{name} "')
    _finish_line(ctx, sh, f"arg0: {name}")


def t_complete_missing(ctx):
    sh = ctx.shell()
    junk = f"qx{tok()}nope"
    bells = sh.bells
    sh.type_keys(junk + "\t", f"{junk}<TAB>")
    raw = sh.settle()
    if sh.bells == bells:
        raise StageFailed("Expected a bell character (\\x07) when nothing matches")
    if not raw.endswith(junk):
        raise StageFailed(f"The line should stay unchanged, screen shows {raw!r}")
    ctx.log.ok("Rang the bell and left the line alone")
    _finish_line(ctx, sh, f"{junk}: command not found")


def t_complete_many(ctx):
    stem = f"zz{tok()}_"
    names = sorted(stem + n for n in w(3))
    for n in names:
        ctx.arg_printer(n)
    sh = ctx.shell()
    bells = sh.bells
    sh.type_keys(stem + "\t", f"{stem}<TAB>")
    sh.settle()
    if sh.bells == bells:
        raise StageFailed("Expected a bell on the first TAB when several programs match")
    ctx.log.ok("First TAB rang the bell")
    sh.type_keys("\t", "<TAB>")
    second = sh.settle()
    missing = [n for n in names if n not in second]
    if missing:
        raise StageFailed(f"Second TAB should list all matches; missing {missing}. Screen: {second!r}")
    if not second.rstrip("\n").endswith("$ " + stem):
        raise StageFailed(f'After the list, expected the prompt to come back as "$ {stem}". Screen: {second!r}')
    ctx.log.ok("Second TAB listed every match and restored the prompt")
    rest = names[0][len(stem):]
    sh.type_keys(rest)
    _finish_line(ctx, sh, f"arg0: {names[0]}")


def t_complete_partial(ctx):
    base = f"kv{tok()}"
    names = [f"{base}_x", f"{base}_x_y", f"{base}_x_y_z"]
    for n in names:
        ctx.arg_printer(n)
    sh = ctx.shell()
    sh.type_keys(base[:4] + "\t", f"{base[:4]}<TAB>")
    line = _typed(sh)
    if not line.endswith(names[0]):
        raise StageFailed(f'Expected "{names[0]}" (longest shared prefix), screen shows {line!r}')
    ctx.log.ok(f"Extended to {names[0]}")
    sh.type_keys("_\t", "_<TAB>")
    line = _typed(sh)
    if not line.endswith(names[1]):
        raise StageFailed(f'Expected "{names[1]}", screen shows {line!r}')
    ctx.log.ok(f"Extended to {names[1]}")
    sh.type_keys("_\t", "_<TAB>")
    line = _typed(sh)
    if not line.endswith(names[2] + " "):
        raise StageFailed(f'Expected "{names[2]} " (unique, with a space), screen shows {line!r}')
    ctx.log.ok(f"Completed to {names[2]}")
    _finish_line(ctx, sh, f"arg0: {names[2]}")


# =================================================================== Pipelines
def t_pipe(ctx):
    a, b, c = w(3)
    ctx.file("fruit.txt", f"{a}\n{b}\n{c}\n{a}\n")
    sh = ctx.shell()
    for cmd in ("cat fruit.txt | wc -l", f"echo {a} {b} | tr a-z A-Z", "cat fruit.txt | sort"):
        run_check(ctx, sh, cmd, ctx.real_sh(cmd))


def t_pipe_builtin(ctx):
    sh = ctx.shell()
    a, b = w(2)
    run_check(ctx, sh, f"echo {a} {b} | wc -w", ctx.real_sh(f"echo {a} {b} | wc -w"))
    run_check(ctx, sh, f"echo {a} | type exit", ["exit is a shell builtin"])
    run_check(ctx, sh, "type echo | tr a-z A-Z", ["ECHO IS A SHELL BUILTIN"])


def t_pipe_many(ctx):
    lines = "\n".join(f"{w()} {i}" for i in range(20)) + "\n"
    ctx.file("data.txt", lines)
    sh = ctx.shell()
    for cmd in ("cat data.txt | head -n 7 | wc -l", "cat data.txt | sort | head -n 3 | tr a-z A-Z"):
        run_check(ctx, sh, cmd, ctx.real_sh(cmd))


# =================================================================== History
def t_history(ctx):
    sh = ctx.shell()
    a, b = w(2)
    sh.run(f"echo {a}")
    sh.run(f"echo {b}")
    run_check(ctx, sh, "history", [f"    1  echo {a}", f"    2  echo {b}", "    3  history"])


def t_history_n(ctx):
    sh = ctx.shell()
    ws = w(4)
    for x in ws:
        sh.run(f"echo {x}")
    run_check(ctx, sh, "history 2", [f"    4  echo {ws[3]}", "    5  history 2"])


def t_history_arrows(ctx):
    sh = ctx.shell()
    a, b = w(2)
    sh.run(f"echo {a}")
    sh.run(f"echo {b}")
    sh.type_keys("\x1b[A", "<UP>")
    line = _typed(sh)
    if not line.endswith(f"echo {b}"):
        raise StageFailed(f'UP should recall "echo {b}", screen shows {line!r}')
    ctx.log.ok("UP recalled the last command")
    sh.type_keys("\x1b[A", "<UP>")
    line = _typed(sh)
    if not line.endswith(f"echo {a}"):
        raise StageFailed(f'Second UP should recall "echo {a}", screen shows {line!r}')
    ctx.log.ok("UP again recalled the one before")
    _finish_line(ctx, sh, a)


# =================================================================== Variables
def env_printer(ctx, name, var):
    ctx.exe(name, f'echo "{var}=${{{var}}}"')


def t_var_expand(ctx):
    sh = ctx.shell()
    a = w()
    run_check(ctx, sh, "echo $HOME", [ctx.home])
    run_check(ctx, sh, f"echo {a}:$HOME:{a}", [f"{a}:{ctx.home}:{a}"])
    unset = f"NOPE_{tok()}"
    run_check(ctx, sh, f"echo ${unset} {a}", [a])
    run_check(ctx, sh, f"echo x${unset}.y", ["x.y"])


def t_var_export(ctx):
    var = f"FRUIT_{tok()}"
    prog = f"show_{tok()}"
    env_printer(ctx, prog, var)
    sh = ctx.shell()
    run_check(ctx, sh, "type export", ["export is a shell builtin"])
    a, b = w(2)
    check(ctx.log, "export", sh.run(f"export {var}={a}"), [])
    run_check(ctx, sh, f"echo ${var}", [a])
    run_check(ctx, sh, prog, [f"{var}={a}"])
    sh.run(f"export {var}={b}")
    run_check(ctx, sh, prog, [f"{var}={b}"])


def t_var_braces(ctx):
    var = f"V{tok()}"
    sh = ctx.shell()
    a, b = w(2)
    sh.run(f"export {var}={a}")
    run_check(ctx, sh, f"echo ${{{var}}}{b}", [f"{a}{b}"])
    run_check(ctx, sh, f"echo ${{HOME}}/{b}", [f"{ctx.home}/{b}"])


def t_var_quotes(ctx):
    var = f"Q{tok()}"
    sh = ctx.shell()
    a, b = w(2)
    sh.run(f"export {var}={a}")
    run_check(ctx, sh, f'echo "${var}   {b}"', [f"{a}   {b}"])
    run_check(ctx, sh, f"echo '${var}'", [f"${var}"])
    run_check(ctx, sh, f"echo \\${var}", [f"${var}"])
    run_check(ctx, sh, f'echo "\\${var} is ${var}"', [f"${var} is {a}"])
    run_check(ctx, sh, "echo $ alone", ["$ alone"])


def t_exit_status(ctx):
    sh = ctx.shell()
    sh.run("true")
    run_check(ctx, sh, "echo $?", ["0"])
    sh.run("false")
    run_check(ctx, sh, "echo $?", ["1"])
    bogus = f"{w()}_{tok()}"
    sh.run(bogus)
    run_check(ctx, sh, "echo $?", ["127"])
    sh.run(f"cd /{w()}-{tok()}")
    run_check(ctx, sh, "echo status=$?", ["status=1"])
    code = random.randint(2, 9)
    prog = f"fails_{tok()}"
    ctx.exe(prog, f"exit {code}")
    sh.run(prog)
    run_check(ctx, sh, "echo $?", [str(code)])


# =================================================================== Command lists
def t_semicolon(ctx):
    a, b, c = w(3)
    os.makedirs(os.path.join(ctx.work, c))
    sh = ctx.shell()
    run_check(ctx, sh, f"echo {a}; echo {b}", [a, b])
    run_check(ctx, sh, f"cd {c} ; pwd", [os.path.join(ctx.work, c)])
    bogus = f"{w()}_{tok()}"
    run_check(ctx, sh, f"{bogus};echo {a}", [f"{bogus}: command not found", a])


def t_and_or(ctx):
    sh = ctx.shell()
    a, b = w(2)
    run_check(ctx, sh, f"true && echo {a}", [a])
    run_check(ctx, sh, f"false && echo {a}", [])
    run_check(ctx, sh, f"false || echo {b}", [b])
    run_check(ctx, sh, f"true || echo {b}", [])
    missing = f"/{w()}-{tok()}"
    run_check(ctx, sh, f"cd {missing} && echo {a}", [f"cd: {missing}: No such file or directory"])
    run_check(ctx, sh, f"false && echo {a} || echo {b}", [b])
    run_check(ctx, sh, f"false; echo $? && echo {a}", ["1", a])


def t_lists_pipes(ctx):
    a, b = w(2)
    ctx.file("words.txt", f"{a}\n{b}\n{a}\n")
    sh = ctx.shell()
    for cmd in (f"echo {a} | tr a-z A-Z && echo {b}",
                f"cat words.txt | sort | uniq; echo {b}",
                f"cat missing-{tok()} 2> err.txt || echo {a} | tr a-z A-Z"):
        run_check(ctx, sh, cmd, ctx.real_sh(cmd))


# =================================================================== Persistent history
def t_history_read(ctx):
    a, b, c = w(3)
    hist = ctx.file("old_history", f"echo {a}\necho {b}\n\necho {c}\n")
    sh = ctx.shell()
    check(ctx.log, "history -r", sh.run(f"history -r {hist}"), [])
    run_check(ctx, sh, "history", [f"    1  history -r {hist}", f"    2  echo {a}", f"    3  echo {b}",
                                   f"    4  echo {c}", "    5  history"])


def t_history_write(ctx):
    a, b = w(2)
    out = os.path.join(ctx.root, "hist_out")
    sh = ctx.shell()
    sh.run(f"echo {a}")
    sh.run(f"echo {b}")
    check(ctx.log, "history -w", sh.run(f"history -w {out}"), [])
    check_file(ctx.log, out, f"echo {a}\necho {b}\nhistory -w {out}\n", out)
    sh.run(f"history -w {out}")
    check_file(ctx.log, out, f"echo {a}\necho {b}\nhistory -w {out}\nhistory -w {out}\n", f"{out} (rewritten)")


def t_history_append(ctx):
    a, b = w(2)
    out = os.path.join(ctx.root, "hist_app")
    with open(out, "w") as f:
        f.write("echo earlier\n")
    sh = ctx.shell()
    sh.run(f"echo {a}")
    sh.run(f"history -a {out}")
    check_file(ctx.log, out, f"echo earlier\necho {a}\nhistory -a {out}\n", out)
    sh.run(f"echo {b}")
    sh.run(f"history -a {out}")
    check_file(ctx.log, out, f"echo earlier\necho {a}\nhistory -a {out}\necho {b}\nhistory -a {out}\n",
               f"{out} (only new lines appended)")


def t_histfile(ctx):
    a, b, c = w(3)
    hf = os.path.join(ctx.root, "my_history")
    with open(hf, "w") as f:
        f.write(f"echo {a}\necho {b}\n")
    sh = ctx.shell(env={"HISTFILE": hf})
    run_check(ctx, sh, "history", [f"    1  echo {a}", f"    2  echo {b}", "    3  history"])
    sh.run(f"echo {c}")
    sh.type_keys("exit 0\n", "exit 0")
    if sh.expect_exit() != 0:
        raise StageFailed("Expected exit status 0")
    check_file(ctx.log, hf, f"echo {a}\necho {b}\nhistory\necho {c}\nexit 0\n", f"HISTFILE {hf}")
    sh2 = ctx.shell(env={"HISTFILE": os.path.join(ctx.root, f"none-{tok()}")})
    run_check(ctx, sh2, "history", ["    1  history"])


TESTS = {name[2:].replace("_", "-"): fn for name, fn in globals().items() if name.startswith("t_")}
