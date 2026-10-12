# MSHR overlap pilot

Tracked task: [GitHub issue #1](https://github.com/HassanAlhajAli/cpu-design-search/issues/1).

## Question

An MSHR is a cache entry that remembers an unfinished miss while a lower level
fetches its data. If a core knows several addresses at once, more MSHRs may let
it overlap the waits. If the next address comes from the previous load, extra
entries alone cannot reveal that address sooner.

**Prediction, recorded before measurement:** raising L1 data-cache MSHRs from
2 to 8 will reduce cycles more for eight independent pointer chains than for
one dependent chain. This is a prediction, not a measured result.

## Controlled comparison

The program creates 32,768 nodes, each exactly 64 bytes: a 2 MiB working set.
A fixed-seed shuffle places the nodes in random order. Dependent mode links
them into one ring; independent mode divides the same shuffled nodes into
eight disjoint rings. One traversal visits every node once in either mode.
After one warm-up traversal, two more traversals perform 65,536 measured
pointer reads. Native and simulated executions must return the same result.

| Simulated setting | Fixed value |
| --- | --- |
| Simulator | gem5 v25.1.0.1, commit `c8222cc67a399bfc01e8658dd14b30d5bfd634f9` |
| ISA and core | one RISC-V out-of-order core, 2 GHz, 192 ROB entries |
| L1 instruction/data cache | 32 KiB, 8-way, 64-byte lines; tag/data/response latency 2 cycles each |
| L2 cache | 512 KiB, 8-way; tag/data/response latency 12 cycles each; 32 MSHRs |
| Main memory | gem5 SimpleMemory, 100 ns, 12.8 GiB/s, no latency variation |
| Prefetching | disabled at all cache levels |
| Varied hardware setting | L1 data-cache MSHRs: 2 or 8 |

We compare **2 versus 8 MSHRs within each mode**. The modes use different loop
instructions, so their absolute cycle counts are not a controlled comparison
of equal instruction streams. A benefit is evidence about this generic model,
not a claim about Kirin hardware. Zero benefit is also informative: another
resource might limit overlap, or the modeled cache might not be the bottleneck.

The workload calls gem5's statistics reset immediately after warm-up and dumps
statistics after the two measured traversals. The runner checks that a region
dump exists, that cycles and misses are present, that the result matches native
execution, and that only the intended MSHR field differs between configurations
for a given mode. Raw statistics and resolved configurations are retained.

## Reproduce in Ubuntu or WSL2 Ubuntu 24.04

Install the development packages:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  scons g++-riscv64-linux-gnu python3-dev pkg-config \
  libprotobuf-dev protobuf-compiler libgoogle-perftools-dev \
  libhdf5-dev libboost-dev zlib1g-dev m4
```

Build the pinned simulator outside this repository, then build the workload:

```bash
git clone --depth 1 --branch v25.1.0.1 \
  https://github.com/gem5/gem5.git "$HOME/cpu-design-search-deps/gem5"
export GEM5_ROOT="$HOME/cpu-design-search-deps/gem5"
git -C "$GEM5_ROOT" rev-parse HEAD  # must match the commit above
scons -C "$GEM5_ROOT" build/RISCV/gem5.opt -j4
bash scripts/build_workload.sh
python3 scripts/run_pilot.py --outdir runs/mshr-pilot
```

Run the last two commands from this repository's root. Use a new output
directory for each rerun. The runner records wall time and maximum memory use
for each simulation. Its `summary.json` is written only after all four cases
pass; failed and partial raw runs remain available for diagnosis.

## Measured result

All four runs completed with the native checksum, the intended 65,536
measured pointer reads, a measured-region statistics block, and a resolved
configuration check. The resolved L1I, L1D and L2 prefetchers were all absent.
The simulator was built from the pinned commit above; the project code used
for these runs was commit `4a8aefdd3f855e98daf9f128fb068d1725bdc9c0`.

| Workload | L1D MSHRs | Measured CPU cycles | L1D misses | L2 misses | L1D cycles blocked for no MSHRs | Simulator wall time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Dependent | 2 | 15,987,588 | 65,543 | 65,543 | 4,398 | 19.92 s |
| Dependent | 8 | 15,987,392 | 65,546 | 65,543 | 0 | 16.28 s |
| Independent | 2 | 7,865,143 | 65,574 | 65,542 | 7,733,955 | 15.37 s |
| Independent | 8 | 1,999,674 | 65,557 | 65,543 | 1,605,816 | 9.64 s |

Raising MSHRs from 2 to 8 made the independent workload **3.93 times faster
in simulated cycles**, a 74.6% cycle reduction. The dependent workload changed
by only 196 cycles (about 0.001%). The independent workload's L1D blocked
cycles fell by 79.2%, while its cache-miss count barely changed. This is
consistent with *overlapping more waits*, rather than avoiding the misses.
The fact that the 8-MSHR case still has blocked cycles does not establish
that 8 is optimal.

The four simulation processes took **61.21 seconds combined**, with a peak
reported process memory use of about **108 MiB**. The first gem5 build was a
separate, much larger one-time setup cost. These run costs describe only this
short synthetic workload; they cannot establish the cost of every later
workload or a full design sweep. They make a small exhaustive comparison worth
testing before assuming a learned search method saves enough simulation work.

The final machine-readable summary and each run's raw statistics, resolved
configuration, command, output, and timing are in
[`data/mshr-pilot/`](../data/mshr-pilot/). The complete first statistics block
in each `stats.txt` is the measured region; the second block is the automatic
end-of-process dump and includes later activity. The workload and simulator
scripts are in this repository, while the gem5 executable and workload
binaries are rebuilt using the commands above.

This result supports the prediction **for one synthetic input and this gem5
model**. It does not measure hardware area, power, a Kirin CPU, production
programs, or the benefit of RL. It also does not tell us yet whether L2 MSHRs
are a useful knob for the broader search. We will choose later design knobs
after checking which resources actually constrain representative workloads.
