#!/bin/bash
# Install the court docket monitor as a launchd user agent.
# Idempotent: safe to re-run after editing config.json or the plist.
set -euo pipefail

LABEL="com.shashwat.courtwatch"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$HOME/.local/share/courtwatch"
STATE="$HOME/.local/state/courtwatch"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

say() { printf '%s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

[[ "$(uname -s)" == "Darwin" ]] || die "this installer is macOS only (launchd)"

PYTHON="$(command -v python3 || true)"
[[ -n "$PYTHON" ]] || die "python3 not found. Run: xcode-select --install"
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info>=(3,8) else 1)' \
  || die "python3 is older than 3.8"
command -v osascript >/dev/null || die "osascript not found"

say "python3:  $PYTHON"
say "source:   $SRC"
say "install:  $APP"
say "state:    $STATE"
say "plist:    $PLIST"
say ""

mkdir -p "$APP" "$STATE/snapshots" "$HOME/Library/LaunchAgents"
install -m 0755 "$SRC/courtwatch.py" "$APP/courtwatch.py"

# Never clobber a config the user has already tuned.
if [[ -f "$APP/config.json" ]]; then
  say "config.json already present - keeping yours (delete it to reset)"
else
  install -m 0644 "$SRC/config.json" "$APP/config.json"
fi

# Generate the real plist from the committed template.
sed -e "s|__PYTHON__|$PYTHON|g" \
    -e "s|__SCRIPT__|$APP/courtwatch.py|g" \
    -e "s|__STATE__|$STATE|g" \
    "$SRC/$LABEL.plist" > "$PLIST"
plutil -lint "$PLIST" >/dev/null || die "generated plist is invalid"

# Replace any previous copy of the agent.
launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$PLIST" 2>/dev/null \
  || launchctl load -w "$PLIST" \
  || die "could not load the agent"

say "agent loaded. Running once now to capture a baseline..."
launchctl kickstart -k "gui/$UID/$LABEL" 2>/dev/null || "$PYTHON" "$APP/courtwatch.py" || true
sleep 4

say ""
if [[ -s "$STATE/changes.log" ]]; then
  say "--- last lines of changes.log ---"
  tail -n 12 "$STATE/changes.log"
else
  say "changes.log is empty. Check $STATE/errors.log"
fi

if [[ ! -f "$HOME/.courtlistener_token" && -z "${COURTLISTENER_TOKEN:-}" ]]; then
  say ""
  say "NOTE: no CourtListener API token found."
  say "  Get a free one at https://www.courtlistener.com/profile/api-token/"
  say "  then: printf '%s' 'YOUR_TOKEN' > ~/.courtlistener_token && chmod 600 ~/.courtlistener_token"
  say "  The two web pages are polled regardless; the docket needs the token"
  say "  if anonymous API access is rejected."
fi

say ""
say "Installed. Verify with:  ./verify.sh"
say "Remove with:            ./uninstall.sh"
