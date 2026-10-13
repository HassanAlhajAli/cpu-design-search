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

## Results

Pending measurement. Predictions above must remain unchanged when adding
observations and interpretation below.
