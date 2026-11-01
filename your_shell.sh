#!/bin/sh
# The tester runs this file to start your shell.
# Using another language? Change the last line to run your program instead,
# for example:  exec "$(dirname "$0")/build/myshell" "$@"
exec python3 -u "$(dirname "$0")/app/main.py" "$@"
