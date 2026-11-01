#!/bin/sh
set -e
cd "$(dirname "$0")"
mkdir -p .smith/build
cargo build --quiet --release --manifest-path app/Cargo.toml
cp app/target/release/shell .smith/build/shell
