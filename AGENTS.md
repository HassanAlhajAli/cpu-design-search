# Project guidance

This is a measured CPU architecture study. Keep changes small and leave a reproducible path from configuration to raw simulator output to reported result. Never present predicted performance as measured performance. Treat failed correctness checks, missing statistics, crashes and timeouts as failures. Protect held-out/reference labels from search methods until the protocol permits access.

The first measurement pilot is complete; the broader simulator setup, workloads, design space and method comparison remain provisional. Update the README when a decision or result changes the public project story. Private interview notes live outside this repository.

Hassan is learning CPU architecture while building this project. For each meaningful new component or experiment, explain in plain language what it does, why we need it, what CPU or RL concept it uses, and how we checked it. Define unfamiliar terms when first used. Keep him involved in methodological decisions and record predictions and corrections in the private project log. Routine edits do not need a ceremony, but do not let an unexplained implementation or file become part of the project.

Keep code reviewable as it grows: use clear names, give each function a coherent job, document non-obvious experimental assumptions, and fail visibly when required measurements or checks are missing. Before each meaningful commit, review the diff for clarity and run the smallest check that can catch a real regression. Refactor confusing code in focused commits, preserving measured behavior and raw provenance. Explain the changed code and its verification to Hassan so he can trace a result without relying on comments alone.
