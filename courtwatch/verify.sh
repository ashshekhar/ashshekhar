#!/bin/bash
# Prove the monitor is actually working. Read-only except for the test run.
set -uo pipefail

LABEL="com.shashwat.courtwatch"
APP="$HOME/.local/share/courtwatch"
STATE="$HOME/.local/state/courtwatch"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PY="$(command -v python3)"

hr() { printf '\n== %s ==\n' "$1"; }

hr "1. is the agent registered with launchd"
if launchctl print "gui/$UID/$LABEL" 2>/dev/null | grep -E '^\s+(state|last exit code|program) ' ; then
  echo "OK: launchd knows the job"
else
  echo "FAIL: not loaded. Run ./install.sh"
fi

hr "2. next scheduled fire times (local clock)"
grep -A1 '<key>Hour</key>' "$PLIST" 2>/dev/null | grep integer \
  | sed 's/.*<integer>\(.*\)<\/integer>.*/  hour \1:07/' || echo "  (plist not found)"

hr "3. when did it last run, and what did it see"
[[ -f "$STATE/state.json" ]] && "$PY" -m json.tool "$STATE/state.json" || echo "no state yet"

hr "4. last 20 log lines"
tail -n 20 "$STATE/changes.log" 2>/dev/null || echo "no changes.log yet"

hr "5. recent errors (empty is good)"
tail -n 10 "$STATE/errors.log" 2>/dev/null || echo "no errors.log - clean"

hr "6. force a run right now"
launchctl kickstart -k "gui/$UID/$LABEL" 2>/dev/null && echo "kickstarted" || echo "kickstart failed"
sleep 5
tail -n 5 "$STATE/changes.log" 2>/dev/null

hr "7. end-to-end notification test (you should see a banner + hear a sound)"
osascript -e 'display notification "If you can read this, alerts work." with title "HIGH PRIORITY - 1:26-cv-13799" subtitle "courtwatch self-test" sound name "Sosumi"'
echo "banner sent. If nothing appeared, open System Settings > Notifications"
echo "and allow notifications for 'Script Editor' (osascript posts under it)."

hr "8. prove change detection fires (temporarily corrupts one stored hash)"
"$PY" - <<'PYEOF'
import json, os, pathlib
state = pathlib.Path(os.path.expanduser("~/.local/state/courtwatch/state.json"))
d = json.loads(state.read_text())
h = d.get("hashes", {})
if h:
    k = sorted(h)[0]
    print("  flipping stored hash for source:", k)
    h[k] = "0" * 64
    state.write_text(json.dumps(d, indent=2, sort_keys=True))
    print("  now run: launchctl kickstart -k gui/$UID/com.shashwat.courtwatch")
    print("  you should get a notification and a diff in changes.log")
else:
    print("  no hashes stored yet - run the monitor once first")
PYEOF
