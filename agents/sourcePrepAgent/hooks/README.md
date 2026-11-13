<!-- C8 plugin / hooks: the only lever that acts INSIDE the tool loop and can enforce what the model cannot skip.
     hooks.yaml registers scripts/guard.sh (which runs guard.py) on pre_tool_use; the deny rules are data in guard.json.
     guard.sh and guard.py are copies kept in sync by baseAgent/scripts/render_host.py; edit guard.json, not guard.py. -->
