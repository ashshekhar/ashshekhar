#!/bin/bash
# Remove the court docket monitor. Logs are kept unless --purge is given.
set -euo pipefail

LABEL="com.shashwat.courtwatch"
APP="$HOME/.local/share/courtwatch"
STATE="$HOME/.local/state/courtwatch"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

say() { printf '%s\n' "$*"; }

launchctl bootout "gui/$UID/$LABEL" 2>/dev/null \
  || launchctl unload -w "$PLIST" 2>/dev/null \
  || true
say "agent stopped"

rm -f "$PLIST" "$PLIST.disabled"
say "plist removed"

rm -rf "$APP"
say "program removed ($APP)"

if [[ "${1:-}" == "--purge" ]]; then
  rm -rf "$STATE"
  say "state and logs purged ($STATE)"
else
  say "state and logs KEPT at $STATE"
  say "  re-run with --purge to delete them too"
fi

if launchctl print "gui/$UID/$LABEL" >/dev/null 2>&1; then
  say "WARNING: launchd still lists the job. Log out and back in."
else
  say "confirmed: launchd no longer knows about $LABEL"
fi
