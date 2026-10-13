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

From the repository root in the prepared Ubuntu environment, after the
implementation has been committed and the pinned workload built:

```bash
python3 scripts/run_pilot.py --modes dependent independent independent16 \
  --mshrs 8 16 --rob-entries 64 192 --outdir runs/rob-mshr-pilot
```
