# Experimental wheel installation

This path supports local synthetic testing; it is not approval for public distribution. Review the project's license and the distribution and usage terms of dependencies such as PyMuPDF separately. The `portfolio-runtime-data` wheel contains the local backend, an explicit set of pattern files, the review rubric, and the planning skill. Schemas are included in the `portfolio-core` wheel. Private cases, external binaries, and caches are excluded.

From the workspace root, prepare an empty wheel output directory and a new virtual environment:

```powershell
uv build --wheel --all --out-dir <empty-wheel-dir>
uv build --wheel project/packaging/runtime-data --out-dir <empty-wheel-dir>
uv venv --python 3.11 <new-venv>
uv pip install --python <new-venv>/Scripts/python.exe --find-links <empty-wheel-dir> (Get-ChildItem <empty-wheel-dir>/*.whl).FullName
```

The install command resolves external dependencies anew; it does not apply `uv.lock`. Fully reproducible installation and release artifact verification remain open. `PASCAL_WORKSPACE` takes precedence when explicitly selecting a checkout. In installed mode, user caches and approved-case paths live under `PASCAL_DATA_DIR` or `~/.portfolio-agent`. DesignCraft and PhotoCraft require separate tools.

To test the installed environment, run `<new-venv>/Scripts/python.exe <checkout>/project/packaging/smoke_compose.py` from an empty working directory outside the checkout. This checks local backend execution and gates on synthetic input only; it does not establish design quality.
