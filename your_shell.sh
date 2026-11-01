#!/bin/sh
# The tester runs this file to start your shell.
exec python3 -u "$(dirname "$0")/app/main.py" "$@"
