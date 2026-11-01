#!/bin/sh
# The tester runs this file to start your shell.
exec node "$(dirname "$0")/app/main.js" "$@"
