# BackendAdapter contract (proposed)

`capabilities()` → formats, edit operations, import/export types, verified version, local/remote requirements, license review status. `open(project, format)` → DocumentHandle. `apply_operations(handle, operations, expected_version)` → new immutable version + structured diff. `render(handle, format, page_ranges)` → preview + output. `inspect(handle)` → bounding boxes, text runs, source layer mapping, warnings. `verify_export(handle, output)` → boolean hard gates and detailed report. `close()` cleans temporary data.

All adapters must fail closed on unknown transformations or unsupported source fidelity. Disable native PDF/vector preservation claims until measured. Provide a basic HTML/SVG fallback for early baselines; no universal editor implementation in v0. Domain logic must not import specific vendor SDKs.
