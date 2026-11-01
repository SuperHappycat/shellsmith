#!/bin/sh
set -e
cd "$(dirname "$0")"
mkdir -p .smith/build
cd app && go build -o ../.smith/build/shell .
