#!/bin/sh
# The tester runs this file to start your shell (build.sh has already compiled it).
exec "$(dirname "$0")/.smith/build/shell" "$@"
