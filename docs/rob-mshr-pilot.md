# Pilot: reorder buffer size and L1D MSHRs

[Issue #4](https://github.com/HassanAlhajAli/cpu-design-search/issues/4) records the protocol before implementation.

## Question and hypothesis (before measurement)

The reorder buffer (ROB) holds instructions that have entered an out-of-order
CPU but have not yet retired in program order. A larger ROB may give the core
more room to find independent pointer reads while earlier reads wait for
memory. We ask whether changing ROB capacity affects the benefits of L1
data-cache MSHR capacity across one, eight, and 16 pointer chains.

The supervisor's **uncertain** hypothesis is that a larger ROB will help the
16-chain workload more when 16 MSHRs can accept more concurrent misses. A
dependent chain may benefit less because its next address remains unknown
until the previous read returns. Hassan has not made a prediction for this
pilot; we will review the evidence together afterward.

## Protocol

- Use the existing statically linked RISC-V workload without changing its
  source or input. Run `dependent`, `independent` (eight chains), and
  `independent16` (16 chains).
- Cross ROB entries **64 and 192** with L1D MSHRs **8 and 16** for each mode:
  12 cases. Keep all other CPU, cache, memory, clock, and prefetch settings
  fixed in the pinned gem5 model.
- Keep 32,768 nodes, fixed seed, one warm-up traversal and two measured
  traversals, for 65,536 pointer reads per case.
- Require native/simulated output equality, valid measured-region statistics,
  intended resolved ROB and MSHR values, and otherwise identical resolved
  hardware within a mode. Preserve commands, raw simulator output,
  configuration, statistics, source/binary identity, and wall time.
- Compare CPU cycles within each mode while showing misses and no-MSHR
  blocked cycles. Report interaction between settings as an observation;
  do not infer area, power, general workload performance, or RL usefulness.

## Measured result

All 12 cases passed native/simulated output, 65,536-read, exit, statistics,
and resolved-configuration checks. Within each workload mode, the resolved
configurations differed only in ROB entries and L1D MSHRs. L1I, L1D, and L2
prefetchers were absent. The workload binary hash matches the earlier
[16-chain test](sixteen-chain-test.md), and the ROB-192 eight- and 16-chain
results reproduce its four CPU-cycle results exactly.

| Mode | ROB entries | L1D MSHRs | CPU cycles | L1D misses | L2 misses | ROB-full events | L1D cycles blocked for no MSHRs | Simulator wall time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 chain | 64 | 8 | 15,992,126 | 65,622 | 65,560 | 213,000 | 0 | 17.43 s |
| 1 chain | 64 | 16 | 15,992,126 | 65,622 | 65,560 | 213,000 | 0 | 14.94 s |
| 1 chain | 192 | 8 | 15,991,622 | 65,601 | 65,560 | 1,001 | 0 | 17.35 s |
| 1 chain | 192 | 16 | 15,991,622 | 65,601 | 65,560 | 1,001 | 0 | 17.53 s |
| 8 chains | 64 | 8 | 2,000,701 | 65,670 | 65,559 | 67,603 | 1,605,728 | 9.69 s |
| 8 chains | 64 | 16 | 2,000,701 | 65,670 | 65,559 | 67,603 | 0 | 7.43 s |
| 8 chains | 192 | 8 | 2,000,946 | 65,640 | 65,559 | 14 | 1,605,847 | 10.10 s |
| 8 chains | 192 | 16 | 2,000,203 | 65,643 | 65,559 | 14 | 0 | 9.84 s |
| 16 chains | 64 | 8 | 1,967,863 | 65,626 | 65,559 | 65,567 | 1,835,122 | 7.89 s |
| 16 chains | 64 | 16 | 1,091,347 | 65,626 | 65,559 | 65,567 | 442,632 | 8.84 s |
| 16 chains | 192 | 8 | 1,967,838 | 65,643 | 65,560 | 4 | 1,835,122 | 10.42 s |
| 16 chains | 192 | 16 | 1,007,288 | 65,656 | 65,560 | 24 | 606,530 | 9.19 s |

For 16 chains at **16 MSHRs**, increasing the ROB from 64 to 192 entries
saved **84,059 CPU cycles (7.7023%)**. At **8 MSHRs**, the same ROB change
saved only **25 cycles (0.0013%)**. This supports an interaction: extra ROB
room mattered when the cache could accept more concurrent misses. At 16
chains, raising MSHRs from 8 to 16 saved 44.54% of cycles with ROB 64 and
48.81% with ROB 192. The one- and eight-chain modes changed little with ROB
capacity.

The 16-chain, 16-MSHR ROB-full count fell from 65,567 at ROB 64 to 24 at
ROB 192. This is consistent with the larger ROB reducing a constraint, but
it is not a count of CPU cycles saved. For example, the dependent workload's
ROB-full count fell sharply with a larger ROB while its CPU cycles changed
by only 0.0032%. Cache no-MSHR blocked cycles can also increase as the core
exposes more requests, even when total CPU cycles fall. Miss counts remained
close across configurations. These observations do not isolate every
pipeline or memory-system limit.

The 12 simulator processes took **140.65 seconds combined** after setup.
This is one synthetic pointer workload family on a generic modeled CPU.
Neither hardware area/power nor general application performance was measured;
the fastest case here is not a claim of the best general CPU design. No RL
or search-method comparison has been run.

## Reproduce and inspect

From a clean repository checkout in the prepared Ubuntu environment, with
gem5 built at the pinned revision:

```bash
export GEM5_ROOT="$HOME/cpu-design-search-deps/gem5"
bash scripts/build_workload.sh
python3 scripts/run_pilot.py --modes dependent independent independent16 \
  --mshrs 8 16 --rob-entries 64 192 --outdir runs/rob-mshr-pilot-retry
```

The measured project revision was `c4eab24c8f2a2a6a28348525f669185dc0991839`;
gem5 was `c8222cc67a399bfc01e8658dd14b30d5bfd634f9`. The
[summary](../data/rob-mshr-pilot-retry/summary.json) records the workload,
simulator, and config-script hashes. The [raw case files](../data/rob-mshr-pilot-retry/)
preserve commands, resolved configurations, first measured-region and final
statistics blocks, output, and wall time. Values above come from the first
statistics block; gem5 writes a second block at process exit.

The first attempted run was stopped before a successful summary: the runner
required a rename-stage issue-queue statistic that was absent for the
dependent case. Commit `c4eab24` changed the check to gem5's available
issue-stage counter. We retained that incomplete attempt locally and ran
the full grid in a fresh `-retry` directory. No measurements from the
incomplete attempt appear in the table.
