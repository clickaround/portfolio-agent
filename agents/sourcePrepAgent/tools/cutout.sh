#!/bin/sh
# gitagent tool `cutout`. gitagent starts this with the call's arguments as one JSON object on stdin
# (2.x: `sh tools/cutout.sh` from the agent folder; 3.x: `sh cutout.sh` from tools/).
# It finds a python that runs (on Windows `python3` can be a store alias that does not) and hands over to
# scripts/tool_entry.py, which turns the JSON into `portfolio cutout <project> [--options]`.
here=$(cd "$(dirname "$0")" && pwd)
for py in python3 python; do
  if "$py" -c "" >/dev/null 2>&1; then exec "$py" "$here/../scripts/tool_entry.py" cutout project; fi
done
echo '{"ok": false, "error": "no working python found on PATH"}'
exit 2
