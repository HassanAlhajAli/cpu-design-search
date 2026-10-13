#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${GEM5_ROOT:-}" ]]; then
    echo "Set GEM5_ROOT to the pinned gem5 checkout" >&2
    exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gem5_root="$(cd "$GEM5_ROOT" && pwd)"
mkdir -p "$repo_root/build"

scons -C "$gem5_root/util/m5" \
    riscv.CROSS_COMPILE=riscv64-linux-gnu- build/riscv/out/m5

g++ -O2 -std=c++17 -Wall -Wextra -Werror \
    "$repo_root/workloads/mshr_chains.cpp" \
    -o "$repo_root/build/mshr_chains_native"

riscv64-linux-gnu-g++ -O2 -std=c++17 -Wall -Wextra -Werror \
    -static -DUSE_GEM5_OPS -I"$gem5_root/include" \
    "$repo_root/workloads/mshr_chains.cpp" \
    -L"$gem5_root/util/m5/build/riscv/out" -lm5 \
    -o "$repo_root/build/mshr_chains_riscv"

file "$repo_root/build/mshr_chains_riscv"
"$repo_root/build/mshr_chains_native" dependent
"$repo_root/build/mshr_chains_native" independent
"$repo_root/build/mshr_chains_native" independent16
