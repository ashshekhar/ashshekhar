# courtwatch

Polls one federal docket and two advocacy pages, and tells you the moment
something moves.

**Case:** Presidents' Alliance on Higher Education and Immigration et al. v.
U.S. Department of Homeland Security et al.
No. 1:26-cv-13799 (D. Mass.), Judge F. Dennis Saylor IV

**Why:** the DHS rule ending duration of status for F-1 students takes effect
Sept 15, 2026. A ruling on the preliminary injunction motion is expected before
then.

## Files

| File | What it is |
|---|---|
| `courtwatch.py` | The monitor. Python 3 standard library only. |
| `config.json` | Sources, keywords, cutoff date. Edit this, not the code. |
| `com.shashwat.courtwatch.plist` | launchd schedule template. |
| `install.sh` | Copies files, generates the plist, loads the agent. |
| `verify.sh` | Eight checks that prove it is really working. |
| `uninstall.sh` | Removes everything. `--purge` also deletes logs. |

Installed layout:

```
~/.local/share/courtwatch/       program + config
~/.local/state/courtwatch/       state.json, changes.log, errors.log, snapshots/
~/Library/LaunchAgents/com.shashwat.courtwatch.plist
```

## Install

```bash
cd courtwatch
./install.sh
```

It runs once immediately to capture a baseline, so the first real change is a
true change and not a false alarm.

### CourtListener token

The two web pages need nothing. The docket is read through the CourtListener
REST API. Get a free token and drop it in place:

```bash
printf '%s' 'YOUR_TOKEN' > ~/.courtlistener_token
chmod 600 ~/.courtlistener_token
```

Token from https://www.courtlistener.com/profile/api-token/

If the API answers 401 or 403, the script says so in `errors.log` with that
exact instruction rather than failing silently.

## How it decides something changed

1. Fetch each source.
2. For web pages: delete `<script>`, `<style>`, `<nav>`, `<header>`,
   `<footer>`, `<form>`, comments and the rest of the chrome, then drop lines
   that churn on every load ("Last updated…", cookie banners, copyright,
   bare page numbers, CSRF tokens).
3. For the docket: build one line per docket entry as
   `#12 | 2026-09-04 | MEMORANDUM AND ORDER ... >> Order [PDF]`. Volatile API
   fields are never hashed.
4. SHA-256 the result, compare to the stored hash.
5. On a difference: write a dated unified diff to `changes.log`, then notify.

Keyword scanning runs **only on the added lines**, not the whole page. A page
that already contains the word "injunction" does not scream every time a
footer changes.

High priority keywords: `injunction`, `granted`, `denied`, `stay`, `vacate`,
`postpone`, `ORDER`, `MEMORANDUM`. Matched case-insensitively with a suffix
allowance, so "postponed" and "GRANTED" both hit.

| Priority | Sound | Spoken |
|---|---|---|
| High | Sosumi | yes, via `say` |
| Routine | Submarine | no |

## Failure handling

A 500, a timeout or a DNS failure writes one line to `errors.log` and nothing
else. No banner.

One exception, and it is deliberate: after **4 consecutive failures on the same
source** (about 8 hours of blindness) you get exactly one "Court watch is
blind" banner, then silence again until it recovers. A monitor that is quietly
broken during the week that matters is worse than a monitor that admits it.
Change `stale_alert_after_consecutive_failures` in `config.json` to turn that
off (set it to `0`).

## Schedule

Every 2 hours at :07, on your Mac's local clock: **18, 20, 22, 00, 02 IST**.

That window is 8:30am to 4:30pm US Eastern, which covers the court's business
day. It does **not** cover 4:30pm to 9pm Eastern, and Massachusetts orders
often land there. To close that gap, add two more `<dict>` blocks to the
`StartCalendarInterval` array in the plist for hours `4` and `6`, then re-run
`./install.sh`. That buys you coverage to 8:30pm Eastern.

Missed runs are caught up. launchd fires a missed `StartCalendarInterval` job
when the machine wakes. Several missed slots collapse into a single catch-up
run, which loses nothing here: the script compares against stored hashes, not
against elapsed time.

## Auto-retirement

`cutoff_date` in `config.json` is `2026-09-20`. On the first run after that
date the script notifies once, calls `launchctl bootout` on itself, renames its
own plist to `.disabled`, and exits. It cannot run again without a reinstall.

## Verify it works

```bash
./verify.sh
```

Checks, in order: the agent is registered; the schedule reads back correctly;
`state.json` shows a recent run; recent log lines; recent errors; a forced run;
a real notification banner; and finally it flips one stored hash so the next
run is guaranteed to detect a change.

After step 8, run this and you should get a banner and a diff:

```bash
launchctl kickstart -k gui/$UID/com.shashwat.courtwatch
tail -n 30 ~/.local/state/courtwatch/changes.log
```

Watch it live:

```bash
tail -f ~/.local/state/courtwatch/changes.log
```

If no banner appears, macOS is suppressing it, not the script. System Settings
→ Notifications → allow **Script Editor**, and check that Focus or Do Not
Disturb is off.

## Uninstall

```bash
./uninstall.sh           # stops and removes, keeps the logs
./uninstall.sh --purge   # removes the logs too
```

The last thing it prints is whether launchd still knows about the job.
