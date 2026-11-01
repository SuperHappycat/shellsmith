#!/bin/sh
# Run once by the tester before the stages start. Must exit non-zero on failure.
set -e
cd "$(dirname "$0")"
mkdir -p .smith/build
# GNU readline gives you line editing, TAB completion and history (stages 26+).
cc -O2 -Wall -Wextra -o .smith/build/shell app/*.c -lreadline
