# T000 evidence — static check
- Env: Windows 11, Python 3.11.7, 2026-11-04. Plain Python (no -I; -I discards PYTHONUTF8).
- `python scripts/validate_package.py` exit=0 (PACKAGE_CHECK: PASS; errors=0)
- `python -m unittest discover -s tests` exit=0 (21 tests OK)
- Initial run FAILED on this host: (a) cp949 default encoding in read_text/open/print (clone_repos, task_status, 3 tests, check_*), (b) stale scripts/__pycache__/*.cpython-311.pyc shipped in ZIP tripped COMPILED_FILES_IN_ZIP. Fixed: explicit encoding="utf-8" + stdout reconfigure; pycache removed.
- Negative (temp copy): dependency -> T999 => validator FAIL "UNKNOWN_DEP T001=>T999" exit=1; done w/o evidence => FAIL "MISSING_STATUS_PROOF T001" exit=1.
- Scope limit: static only; no host plugin, backend or design-quality verification.
