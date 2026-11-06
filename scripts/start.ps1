$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONDONTWRITEBYTECODE = '1'
python scripts/validate_package.py
if ($LASTEXITCODE -ne 0) { throw 'PACKAGE_CHECK failed' }
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Unit tests failed' }
python scripts/task_status.py --ready
python scripts/clone_repos.py --id designcraft
Write-Host 'Paste prompts/START_HERE_KO.md into Codex or Claude Code.'
