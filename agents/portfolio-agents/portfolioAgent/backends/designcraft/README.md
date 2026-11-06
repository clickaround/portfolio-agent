# backends/designcraft/

LayoutAdapter for DesignCraft (Apache-2.0), implemented after spike T212 (evidence/DESIGNCRAFT_SPIKE.md) and ADR-0007.
`adapter.py`: scene JSON (mm) -> `designcraft-cli script` -> .designcraft / PDF / IDML / PPTX. Binary is NOT vendored: download the signed release,
verify SHA256 against the release SHA256SUMS, unzip under `.cache/bin/designcraft/x/`. No vendor code included.
