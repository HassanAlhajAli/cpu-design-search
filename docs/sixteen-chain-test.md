# Can 16 pointer chains use 16 L1D MSHRs?

[Issue #3](https://github.com/HassanAlhajAli/cpu-design-search/issues/3) records this question before implementation.

## Question and prediction (before measurement)

The [MSHR sweep](mshr-sweep.md) found that increasing L1 data-cache MSHRs
from 8 to 16 barely reduced CPU cycles for eight independent pointer chains,
although the cache's no-MSHR blocked-cycle counter fell to zero. Perhaps eight
chains expose too few useful concurrent reads to benefit from more slots.

Hassan's prediction is **unsure**. With 16 independent chains, extra MSHRs
may let more reads overlap. Alternatively, a different core or memory limit
may keep the 8-to-16 performance gain small. We will report both CPU cycles
and diagnostic counters rather than treating the counter as saved CPU time.

## Protocol

- Keep the pinned gem5 RISC-V O3 CPU, fixed seed, 32,768 one-line nodes,
  cache and memory settings, and disabled prefetching.
- Use the existing `independent` eight-chain mode and add an `independent16`
  mode with 16 disjoint randomly arranged rings. Both perform one warm-up
  traversal and two measured traversals, totaling 65,536 pointer reads.
- Rebuild one native and one RISC-V workload binary. Run both modes at 8 and
  16 L1D MSHRs: four simulator cases. Within each mode, only the MSHR
  setting may change in the resolved configuration.
- Require closed, disjoint rings, matching native and simulated results,
  expected work count, valid measured-region statistics, and the intended
  MSHR setting. Inspect the built code for separate pointer-load sequences.
- Preserve commands, exact revisions and binary hashes, resolved settings,
  raw statistics and output, wall time, cycles, L1D/L2 misses, and no-MSHR
  blocked cycles. Compare the percentage cycle gain from 8 to 16 MSHRs for
  both chain counts.

A larger gain with 16 chains would support the overlap explanation; it would
not prove that chain count is the only limit. This synthetic experiment does
not measure area, power, Kirin hardware, or whether RL is useful.

## Measured result

All four cases passed the native-result, 65,536-read, exit, statistics, and
resolved-configuration checks. Each mode's 8- and 16-MSHR configurations
differed only in the L1D MSHR setting. L1I, L1D, and L2 prefetchers were
absent. Disassembly of `traverse_sixteen` in the RISC-V binary showed 16
separate pointer loads in the loop, one for each cursor.

| Pointer chains | L1D MSHRs | CPU cycles | L1D misses | L2 misses | L1D cycles blocked for no MSHRs | Simulator wall time |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 8 | 2,000,946 | 65,640 | 65,559 | 1,605,847 | 9.65 s |
| 8 | 16 | 2,000,203 | 65,643 | 65,559 | 0 | 9.16 s |
| 16 | 8 | 1,967,838 | 65,643 | 65,560 | 1,835,122 | 9.67 s |
| 16 | 16 | 1,007,288 | 65,656 | 65,560 | 606,530 | 7.59 s |

With eight chains, 8 to 16 MSHRs saved **743 CPU cycles (0.0371%)**. With
16 chains, it saved **960,550 CPU cycles (48.8125%)**. Miss counts changed
little within each mode. The result supports the explanation that eight
chains exposed too few useful concurrent reads to benefit much from 16
MSHRs. It does not isolate all remaining limits: even with 16 MSHRs, the
16-chain run still recorded 606,530 cache cycles blocked for lack of an
MSHR. That diagnostic counter must not be read as CPU cycles that could all
be saved.

The eight-chain cycle counts differ slightly from the previous sweep because
this comparison uses a rebuilt workload with a wider cursor array and a new
mode dispatcher. We re-ran both eight-chain settings with that **same**
binary. We compare 8 versus 16 MSHRs *within* a mode; absolute cycle counts
across modes also include different loop instructions and ring partitions.

The four simulator processes took **36.07 seconds combined**, excluding
build, preparation, review, and publication. This experiment is one synthetic
workload on one generic modeled CPU. It does not measure hardware area or
power, real applications, Kirin hardware, or RL search quality.

## Reproduce and inspect

From the clean repository root in Ubuntu, with the pinned gem5 checkout
built as described in the [pilot setup](mshr-pilot.md):

```bash
export GEM5_ROOT="$HOME/cpu-design-search-deps/gem5"
bash scripts/build_workload.sh
python3 scripts/run_pilot.py --modes independent independent16 \
  --mshrs 8 16 --outdir runs/sixteen-chain-test
```

The measured project revision was `e3955139a3f9c65eb9490de5a1e67e32e216189c`;
gem5 was `c8222cc67a399bfc01e8658dd14b30d5bfd634f9`. The
[machine-readable summary](../data/sixteen-chain-test/summary.json) records
binary hashes and results. [Raw case files](../data/sixteen-chain-test/)
include the exact command, resolved `config.json`, `stats.txt`, simulator
output, and wall time. Read the **first** statistics block in each
`stats.txt`: it covers the measured traversal. The second is gem5's
automatic end-of-process dump.
