# sourcePrepAgent Memory

<!-- Harness² C3 memory (LongTermMEMORY.md). Every call. Durable domain facts shared across tasks, one line each with its evidence path. Never task-specific answers or grader output. -->

- Cut-out tests need rembg and the cached u2net model; without them the tests skip, which is not a pass. Evidence: `tests/test_cutout.py`.
