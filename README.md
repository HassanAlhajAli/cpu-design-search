# CPU Design Search: a measured architecture study

An in-progress portfolio project by Hassan Alhaj Ali. The aim is to test whether reinforcement learning and learned performance models can help search a CPU configuration space under a limited detailed-simulation budget. We will implement RL as a substantive, inspectable method, compare it with simpler search methods, and validate selected designs in a simulator. The measured comparison will determine whether RL is useful for this task.

The simulator, design knobs, workloads and comparison protocol are **not yet frozen**. The first milestone is a correctness-checked reference run and a timing pilot. Results will be published here only after they are reproducible from recorded configurations and raw measurements.

## Principles

- Keep the simulator revision, workload binary, input and measurement region identifiable for every result.
- Show raw performance and traffic beside any combined score.
- Give simple baselines the same observation budget as learned methods.
- Explain the RL formulation, update rule and its limits; do not claim RL is superior unless measured results support it.
- Distinguish measured results from predictions and proposed explanations.
- Document changes of direction and negative results.

## Status

Project framing. No simulator runs or performance claims yet.

## Planned first milestone

Run one workload at a reference CPU configuration and one controlled variation, check outputs, inspect the relevant simulator counters, and measure experiment cost. The pilot will determine the final study scope.

The first tracked experiment is [the MSHR overlap pilot](docs/mshr-pilot.md)
([issue #1](https://github.com/HassanAlhajAli/cpu-design-search/issues/1)).
It compares one dependent pointer chain with eight independent chains at two
L1 data-cache MSHR settings. Its prediction and reproducible protocol are
recorded before the simulator result.
