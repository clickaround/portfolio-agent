#!/bin/sh
# gitagent hook launcher. gitagent 2.x starts every hook with `sh`, 3.x by extension; both give the event as JSON on stdin.
# It finds a python that runs (on Windows `python3` can be a store alias that does not) and hands over to guard.py.
here=$(cd "$(dirname "$0")" && pwd)
for py in python3 python; do
  if "$py" -c "" >/dev/null 2>&1; then exec "$py" "$here/guard.py"; fi
done
echo "guard.sh: no working python found on PATH" >&2
exit 1
