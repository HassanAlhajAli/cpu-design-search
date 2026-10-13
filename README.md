# CPU Design Search: a measured architecture study

An in-progress portfolio project by Hassan Alhaj Ali. The aim is to test whether reinforcement learning and learned performance models can help search a CPU configuration space under a limited detailed-simulation budget. We will implement RL as a substantive, inspectable method, compare it with simpler search methods, and validate selected designs in a simulator. The measured comparison will determine whether RL is useful for this task.

The broader simulator setup, design knobs, workloads and comparison protocol are **not yet frozen**. The first correctness-checked timing pilot is complete. Further results will be published here only after they are reproducible from recorded configurations and raw measurements.

## Principles

- Keep the simulator revision, workload binary, input and measurement region identifiable for every result.
- Show raw performance and traffic beside any combined score.
- Give simple baselines the same observation budget as learned methods.
- Explain the RL formulation, update rule and its limits; do not claim RL is superior unless measured results support it.
- Distinguish measured results from predictions and proposed explanations.
- Document changes of direction and negative results.

## Status

The first correctness-checked gem5 pilot is complete. For eight independent
pointer chains, raising L1 data-cache MSHRs from 2 to 8 reduced simulated
cycles by 74.6%; one dependent chain barely changed. The raw measurements,
configuration, commands and limitations are in the
[pilot report](docs/mshr-pilot.md). No RL/search result exists yet.

## First milestone

We ran two workload modes at two L1 data-cache MSHR settings, checked their
outputs against native execution, inspected counters, and measured run cost.
The next scope decision will use representative workload timings and bottleneck
measurements rather than assuming the original design space is final.

The first tracked experiment is [the MSHR overlap pilot](docs/mshr-pilot.md)
([issue #1](https://github.com/HassanAlhajAli/cpu-design-search/issues/1)).
It compares one dependent pointer chain with eight independent chains at two
L1 data-cache MSHR settings. The Git history and issue preserve the prediction
recorded before the measured result.

The [follow-up MSHR sweep](docs/mshr-sweep.md) records a prediction and
protocol for testing whether gains level off at larger MSHR counts. Its
results are pending.
