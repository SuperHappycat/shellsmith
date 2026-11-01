"""PTY harness: runs the learner's shell inside a pseudo-terminal, like a real user would."""
import errno
import fcntl
import os
import pty
import re
import select
import signal
import struct
import termios
import time

PROMPT = "$ "
CSI = re.compile(r"\x1b\[([0-9;?]*)([ -/]*)([@-~])")
OTHER_ESC = re.compile(r"\x1b\][^\x07]*\x07|\x1b[()][0-9A-Za-z]|\x1b[=>78]")
# An escape sequence that may still be arriving at the end of a chunk.
PARTIAL_ESC = re.compile(r"\x1b(\[[0-9;?]*[ -/]*|\][^\x07]*|[()])?$")


class StageFailed(Exception):
    pass


class Screen:
    """A one-dimensional terminal: CR, LF, backspace, cursor left/right, erase and
    insert/delete characters (what line editors use to redraw). Finished lines never
    change, so only the current line is mutable; feeding is O(new bytes)."""

    def __init__(self):
        self.done = ""          # finished lines, each ending in "\n"
        self.line = []          # current line as a list of chars
        self.col = 0
        self.pending = ""       # incomplete escape sequence from the previous chunk
        self.bells = 0

    @property
    def text(self):
        return self.done + "".join(self.line)

    def feed(self, data):
        data = self.pending + data
        self.pending = ""
        m = PARTIAL_ESC.search(data)
        if m:
            self.pending, data = data[m.start():], data[:m.start()]
        i, n, line = 0, len(data), self.line
        while i < n:
            c = data[i]
            if c == "\x1b":
                m = CSI.match(data, i)
                if m:
                    self._csi(m.group(1), m.group(3))
                    line = self.line
                    i = m.end()
                    continue
                m = OTHER_ESC.match(data, i)
                i = m.end() if m else i + 1
                continue
            if c == "\r":
                self.col = 0
            elif c == "\n":
                self.done += "".join(line) + "\n"
                self.line = line = []
                self.col = 0
            elif c == "\b":
                self.col = max(0, self.col - 1)
            elif c == "\x07":
                self.bells += 1
            elif c >= " ":
                col = self.col
                if len(line) < col:
                    line.extend(" " * (col - len(line)))
                if col < len(line):
                    line[col] = c
                else:
                    line.append(c)
                self.col = col + 1
            i += 1

    def _csi(self, param, final):
        num = int(param) if param.isdigit() else 1
        line = self.line
        if final == "D":
            self.col = max(0, self.col - num)
        elif final == "C":
            self.col += num
        elif final == "G":
            self.col = max(0, num - 1)
        elif final == "K":
            if param in ("", "0"):
                del line[self.col:]
            elif param == "1":
                for k in range(min(self.col + 1, len(line))):
                    line[k] = " "
            elif param == "2":
                line.clear()
        elif final == "P":
            del line[self.col:self.col + num]
        elif final == "@":
            line[self.col:self.col] = [" "] * num


class Log:
    """Collects log lines for one stage. Printing happens in the parent (see print_log)."""

    def __init__(self, tag):
        self.tag = tag
        self.lines = []

    def _emit(self, kind, prefix, msg):
        for line in str(msg).split("\n"):
            self.lines.append({"kind": kind, "text": f"{prefix} {line}"})

    def info(self, msg):
        self._emit("info", f"[{self.tag}]", msg)

    def ok(self, msg):
        self._emit("ok", f"[{self.tag}] ✔", msg)

    def fail(self, msg):
        self._emit("fail", f"[{self.tag}] ✘", msg)

    def shell(self, msg):
        self._emit("shell", "  [your shell]", msg)

    def dim(self, msg):
        self._emit("dim", f"[{self.tag}]", msg)


COLORS = {"info": "36", "ok": "32", "fail": "31", "shell": "33", "dim": "90"}


def print_log(lines, color):
    for l in lines:
        text = l["text"]
        if color:
            head, sep, rest = text.partition("] ")
            if sep:
                text = f"\033[{COLORS[l['kind']]}m{head}]\033[0m {rest}"
        print(text)
    print(flush=True)


class Shell:
    def __init__(self, argv, cwd, env, log, timeout=None):
        self.log = log
        self.timeout = timeout or float(os.environ.get("SMITH_TIMEOUT", "4"))
        self.term = Screen()
        self.pos = 0          # how much of the screen text the tests have consumed
        self.exit_code = None
        self._shown = 0       # how much of the screen we've mirrored to the log
        pid, fd = pty.fork()
        if pid == 0:  # child
            try:
                os.chdir(cwd)
                os.execvpe(argv[0], argv, env)
            except Exception as e:  # noqa: BLE001
                os.write(2, f"smith: could not start {argv[0]}: {e}\n".encode())
            os._exit(127)
        self.pid, self.fd = pid, fd
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 200, 0, 0))

    @property
    def screen(self):
        return self.term.text

    @property
    def bells(self):
        return self.term.bells

    # ------------------------------------------------------------ low level
    def _read_some(self, wait):
        try:
            r, _, _ = select.select([self.fd], [], [], wait)
        except InterruptedError:
            return False
        if not r:
            return False
        try:
            data = os.read(self.fd, 65536)
        except OSError as e:
            if e.errno == errno.EIO:  # child closed the pty
                self._reap(block=True)
                return None
            raise
        if not data:
            self._reap(block=True)
            return None
        self.term.feed(data.decode("utf-8", "replace"))
        return True

    def _reap(self, block=False):
        if self.exit_code is not None:
            return self.exit_code
        try:
            pid, status = os.waitpid(self.pid, 0 if block else os.WNOHANG)
        except ChildProcessError:
            self.exit_code = -1
            return self.exit_code
        if pid == 0:
            return None
        self.exit_code = os.waitstatus_to_exitcode(status)
        return self.exit_code

    def _mirror(self):
        screen = self.screen
        if len(screen) < self._shown:
            self._shown = screen.rfind("\n") + 1
        new = screen[self._shown:]
        if new:
            self._shown = len(screen)
            for line in new.rstrip("\n").split("\n"):
                if line:
                    self.log.shell(line)

    def wait_for(self, predicate, what, timeout=None, quiet=0.06):
        """Read until predicate(unconsumed_text) is true and output has settled."""
        deadline = time.monotonic() + (timeout or self.timeout)
        while time.monotonic() < deadline:
            if predicate(self.screen[self.pos:]):
                while self._read_some(quiet):   # let the shell finish printing
                    pass
                if predicate(self.screen[self.pos:]):
                    return self.screen[self.pos:]
            got = self._read_some(0.05)
            if got is None:
                if predicate(self.screen[self.pos:]):
                    return self.screen[self.pos:]
                self._mirror()
                raise StageFailed(f"Your shell exited (code {self.exit_code}) while I was waiting for {what}.")
        self._mirror()
        seen = self.screen[self.pos:]
        raise StageFailed(f"Timed out waiting for {what}. Last output: {seen[-200:]!r}")

    def send(self, text):
        os.write(self.fd, text.encode())

    # ------------------------------------------------------------ high level
    def expect_prompt(self):
        self.wait_for(lambda s: s.endswith(PROMPT), 'the prompt "$ "')
        self.pos = len(self.screen)

    def run(self, command):
        """Type a command at the prompt, return the lines it printed (prompt must already be shown)."""
        self.log.info(f"Typing: {command}")
        self.send(command + "\n")
        text = self.wait_for(lambda s: "\n" in s and s.endswith(PROMPT),
                             f'output of "{command}" followed by a new prompt')
        self.pos = len(self.screen)
        self._mirror()
        lines = text[: -len(PROMPT)].split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        return lines[1:]  # first line is the command being echoed back by the terminal

    def type_keys(self, keys, label=None):
        self.log.info(f"Typing: {label or keys!r}")
        self.send(keys)

    def settle(self, quiet=0.2):
        while self._read_some(quiet):
            pass
        return self.screen[self.pos:]

    def expect_exit(self, timeout=None):
        deadline = time.monotonic() + (timeout or self.timeout)
        while time.monotonic() < deadline:
            if self._reap() is not None:
                break
            if self._read_some(0.05) is None:
                break
        else:
            self._mirror()
            raise StageFailed("Your shell is still running; expected it to exit.")
        self._mirror()
        return self.exit_code

    def close(self):
        if self._reap() is None:
            try:
                os.kill(self.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self._reap(block=True)
        try:
            os.close(self.fd)
        except OSError:
            pass
