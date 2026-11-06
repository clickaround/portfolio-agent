# T004 evidence — task runner
- `task_status.py --ready` listed only T000 before completion (deps respected); --all lists 85 tasks.
- Added scripts/task_update.py (Integration Lead only): refuses done without existing evidence file, without --pass PASS, or with unmet dependencies; blocked/skipped need --reason.
- Verified refusals: missing evidence file; T001 done while T000 pending ("dependencies not done {'T000'}").
- Validator rejects done-without-proof (see P00-static.md negative 2).
