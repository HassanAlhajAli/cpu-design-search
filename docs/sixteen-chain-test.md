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
