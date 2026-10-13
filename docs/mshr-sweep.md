# Follow-up: where do extra L1D MSHRs stop helping?

## Question and prediction (written before this sweep)

The [first pilot](mshr-pilot.md) showed that raising L1 data-cache MSHRs
from 2 to 8 reduced simulated cycles for eight independent pointer chains.
It did almost nothing for one dependent chain. At 8 MSHRs, however, the
independent run still recorded 1,605,816 L1D cycles blocked for lack of an
MSHR. Does capacity beyond 8 still help?

Hassan predicts that the **8-to-16 cycle improvement will be smaller than the
2-to-8 improvement**, but notes that 16 may substantially reduce the blocked
counter. This is uncertain: the earlier 74.6% cycle reduction alone cannot
tell us where gains level off. Eight independent chains suggest a possible
limit to useful overlap, while other memory requests and resource constraints
may complicate that intuition. Blocked cycles are diagnostic; they are not
CPU cycles that can simply be subtracted from total run time.

## Protocol

- Use the same statically linked RISC-V workload, fixed random seed, gem5
  v25.1.0.1 revision, O3 core, cache sizes, L2, memory, and disabled
  prefetchers as in the first pilot.
- Run both existing workload modes at L1D MSHR counts **2, 4, 8, and 16**.
  Within a mode, only this hardware parameter may differ.
- Keep one warm-up traversal and two measured traversals, for 65,536 pointer
  reads per case. Require the simulated result to match native execution.
- Save commands, resolved configurations, raw statistics, simulator output,
  run time, and the exact source and gem5 revisions. A missing result,
  statistic, or configuration match is a failed run.
- Compare simulated CPU cycles, L1D and L2 misses, and L1D
  `blockedCycles::no_mshrs` across adjacent capacities. Decide whether a
  larger MSHR count appears useful for this workload, while noting that this
  synthetic one-knob study does not measure hardware area, power, or Kirin.

After committing this prediction and protocol, run from the repository root
in the prepared Ubuntu environment:

```bash
python3 scripts/run_pilot.py --mshrs 2 4 8 16 --outdir runs/mshr-sweep
```

The `GEM5_ROOT` environment variable must point to the pinned simulator
checkout; build the workload with `scripts/build_workload.sh` if needed.
The default runner command still reproduces the original 2-versus-8 pilot.

## Measured results

All eight runs passed the native-result, work-count, exit, statistics, and
resolved-configuration checks. The 2- and 8-MSHR cases reproduced the first
pilot's simulated cycles and misses exactly. The resolved L1 instruction,
L1 data, and L2 prefetchers were absent in all eight configurations.
The simulator used the pinned gem5 commit in the first pilot; the project
source used for these runs was commit
`80044d01f80c43bb5f754e816c32a53464c1641b`.

| Workload | L1D MSHRs | CPU cycles | L1D misses | L2 misses | L1D cycles blocked for no MSHRs | Simulator wall time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Dependent | 2 | 15,987,588 | 65,543 | 65,543 | 4,398 | 21.00 s |
| Dependent | 4 | 15,987,392 | 65,546 | 65,543 | 0 | 18.70 s |
| Dependent | 8 | 15,987,392 | 65,546 | 65,543 | 0 | 19.87 s |
| Dependent | 16 | 15,987,392 | 65,546 | 65,543 | 0 | 17.28 s |
| Independent | 2 | 7,865,143 | 65,574 | 65,542 | 7,733,955 | 17.13 s |
| Independent | 4 | 3,933,201 | 65,578 | 65,543 | 3,801,120 | 10.37 s |
| Independent | 8 | 1,999,674 | 65,557 | 65,543 | 1,605,816 | 10.60 s |
| Independent | 16 | 1,999,287 | 65,575 | 65,543 | 0 | 8.86 s |

For the independent workload, 2-to-4 MSHRs reduced simulated cycles by
49.99%, and 4-to-8 reduced them by 49.16%. The 8-to-16 change reduced them
by only **387 cycles (0.019%)**. The dependent workload was almost unchanged
at every setting. L1D and L2 miss counts stayed close across capacities.

Hassan's two-part prediction was borne out: 8-to-16 helped cycles far less
than 2-to-8, while the no-MSHR blocked-cycle counter fell from 1,605,816
to zero. These are different measurements. The blocked counter records when
the cache was unable to accept requests for lack of an MSHR; it is not a
count of CPU cycles that can all be recovered ([gem5's blocked-cycle
accounting](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/mem/cache/base.hh#L1224-L1235)). The near-identical CPU cycles
show that clearing this cache-level blockage did not appreciably shorten
the program's measured execution. One plausible explanation is that eight
pointer chains expose about eight immediately available pointer reads, so
other limits dominate once that overlap is supported. The sweep does not
isolate the exact remaining limit; a workload with more chains could test
that explanation.

The eight simulator processes took **123.81 seconds combined**. This excludes
the one-time gem5 build, workload build, setup, analysis, and publication.
Wall time varies with host conditions and is not the simulated CPU performance
metric. The result applies to this generic modeled core, memory system, and
synthetic workload. It does not establish an optimal hardware design: area,
power, other workloads, and other design parameters were not measured. It
also does not establish whether RL helps a broader search problem. For this
single knob and short workload, exhaustive evaluation was inexpensive once
the simulator was built.

The machine-readable [summary](../data/mshr-sweep/summary.json) and each
case's `stats.txt`, resolved `config.json`, command, simulator output, and
timing are in [`data/mshr-sweep/`](../data/mshr-sweep/). Use the **first**
statistics block in each `stats.txt`: it covers the measured traversal. The
second block is gem5's automatic end-of-process dump and includes activity
after measurement. The results above were taken from the first block.
