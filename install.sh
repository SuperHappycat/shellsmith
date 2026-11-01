#!/bin/sh
# Install (or update) the `shellsmith` command.
#   git clone https://github.com/SuperHappycat/shellsmith && cd shellsmith && ./install.sh
set -e

SRC=$(cd "$(dirname "$0")" && pwd)
DEST="${SHELLSMITH_HOME:-$HOME/.shellsmith}"
BIN="${SHELLSMITH_BIN:-$HOME/.local/bin}"

say() { printf '%s\n' "$*"; }
fail() { printf 'shellsmith: %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || fail "git is required (https://git-scm.com/downloads)"
command -v python3 >/dev/null 2>&1 || fail "python3 (3.9 or newer) is required"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' \
  || fail "python3 is too old; Shellsmith needs 3.9 or newer"
python3 -c 'import pty' 2>/dev/null \
  || fail "this Python has no pty module. On Windows, install inside WSL (wsl --install)"

mkdir -p "$DEST" "$BIN"
rm -rf "$DEST/engine.new"
mkdir "$DEST/engine.new"
cp -R "$SRC/shellsmith.py" "$SRC/hook.py" "$SRC/tester" "$SRC/course" "$SRC/starters" "$DEST/engine.new/"
rm -rf "$DEST/engine"
mv "$DEST/engine.new" "$DEST/engine"
find "$DEST/engine" -name '__pycache__' -type d -prune -exec rm -rf {} +

cat > "$BIN/shellsmith" <<EOF
#!/bin/sh
exec python3 "$DEST/engine/shellsmith.py" "\$@"
EOF
chmod +x "$BIN/shellsmith"

say "✔ Installed shellsmith to $BIN/shellsmith"
case ":$PATH:" in
  *":$BIN:"*) ;;
  *)
    say ""
    say "! $BIN is not on your PATH yet. Add this line to ~/.bashrc or ~/.zshrc, then open a new terminal:"
    say "    export PATH=\"$BIN:\$PATH\""
    ;;
esac
say ""
say "Next:  shellsmith start python      (or: shellsmith languages)"
