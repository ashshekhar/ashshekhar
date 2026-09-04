#!/usr/bin/env python3
"""Poll a federal court docket and two advocacy pages; notify on change.

Case: Presidents' Alliance on Higher Education and Immigration et al. v. DHS
      No. 1:26-cv-13799 (D. Mass.), Judge F. Dennis Saylor IV

Stdlib only. Designed to be run from a launchd agent on macOS.
Exit codes: 0 normal (including "nothing changed" and "past cutoff"), 1 fatal
config/setup error. Source-level network failures are logged, not fatal.
"""

import datetime as dt
import difflib
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.expanduser(
    os.environ.get("COURTWATCH_STATE", "~/.local/state/courtwatch")
)
STATE_FILE = os.path.join(STATE_DIR, "state.json")
SNAP_DIR = os.path.join(STATE_DIR, "snapshots")
CHANGE_LOG = os.path.join(STATE_DIR, "changes.log")
ERROR_LOG = os.path.join(STATE_DIR, "errors.log")

UA = "courtwatch/1.0 (personal docket monitor; single user; low volume)"
TIMEOUT = 45
CL_API = "https://www.courtlistener.com/api/rest/v4"

LABEL = "com.shashwat.courtwatch"


# ---------------------------------------------------------------- utilities

def now():
    return dt.datetime.now().astimezone()


def stamp():
    return now().strftime("%Y-%m-%d %H:%M:%S %Z")


def log(path, text):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text.rstrip() + "\n")


def log_error(msg):
    log(ERROR_LOG, "[%s] %s" % (stamp(), msg))


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    os.replace(tmp, STATE_FILE)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------ notifications

def _osa_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def notify(title, subtitle, message, sound="Submarine", speak=None):
    """macOS notification via osascript. Never raises."""
    script = 'display notification "%s" with title "%s" subtitle "%s" sound name "%s"' % (
        _osa_escape(message[:240]),
        _osa_escape(title[:120]),
        _osa_escape(subtitle[:120]),
        sound,
    )
    try:
        subprocess.run(["osascript", "-e", script], timeout=20,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:                              # noqa: BLE001
        log_error("notification failed: %r" % (exc,))
    if speak:
        try:
            subprocess.run(["say", speak[:200]], timeout=30,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as exc:                          # noqa: BLE001
            log_error("say failed: %r" % (exc,))


# ------------------------------------------------------------------ fetching

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.status, raw.decode(charset, errors="replace")


# --------------------------------------------------------------- extraction

# Lines whose only content is volatile chrome. Dropped before hashing.
VOLATILE = [
    re.compile(r"^\s*$"),
    re.compile(r"(?i)\blast\s+(updated|modified|reviewed)\b"),
    re.compile(r"(?i)^\s*(copyright|©)\b"),
    re.compile(r"(?i)\b(csrf|nonce|session[_-]?id|_token)\b"),
    re.compile(r"(?i)^\s*(share|print|email this|back to top|skip to (main )?content)\s*$"),
    re.compile(r"(?i)^\s*(cookie|we use cookies|accept all|privacy policy)\b"),
    re.compile(r"(?i)^\s*(sign in|log in|register|subscribe|menu|search)\s*$"),
    re.compile(r"^\s*\d{1,3}\s*$"),
    re.compile(r"(?i)^\s*(page\s+)?\d+\s+of\s+\d+\s*$"),
    re.compile(r"(?i)\bgenerated (on|at)\b"),
]

BLOCK_TAGS = ("script", "style", "noscript", "svg", "nav", "header",
              "footer", "form", "iframe", "template")


def strip_html(doc):
    # Drop whole blocks that never carry case news.
    for tag in BLOCK_TAGS:
        doc = re.sub(r"(?is)<%s\b.*?</%s\s*>" % (tag, tag), " ", doc)
    doc = re.sub(r"(?is)<!--.*?-->", " ", doc)
    # Preserve block boundaries as newlines so the diff stays readable.
    doc = re.sub(r"(?i)<(br|/p|/div|/li|/h[1-6]|/tr|/section|/article)[^>]*>", "\n", doc)
    doc = re.sub(r"(?s)<[^>]+>", " ", doc)
    doc = html.unescape(doc)
    return doc


def normalize(text):
    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ \t   ]+", " ", line).strip()
        if any(rx.search(line) for rx in VOLATILE):
            continue
        lines.append(line)
    # Collapse runs of identical adjacent lines (nav echoes, repeated CTAs).
    out = []
    for line in lines:
        if not out or out[-1] != line:
            out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------- CourtListener

def cl_token():
    tok = os.environ.get("COURTLISTENER_TOKEN", "").strip()
    if tok:
        return tok
    path = os.path.expanduser("~/.courtlistener_token")
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def cl_headers():
    tok = cl_token()
    return {"Authorization": "Token %s" % tok} if tok else {}


def cl_resolve_docket_id(cfg, state):
    """Find the CourtListener docket id once, then cache it in state."""
    cached = state.get("courtlistener_docket_id")
    if cached:
        return cached

    attempts = [
        {"court": cfg["court_id"], "docket_number": cfg["docket_number"]},
        {"court": cfg["court_id"],
         "docket_number": cfg["docket_number"].split(":", 1)[-1]},
    ]
    if cfg.get("pacer_case_id_hint"):
        attempts.append({"court": cfg["court_id"],
                         "pacer_case_id": cfg["pacer_case_id_hint"]})

    for params in attempts:
        url = "%s/dockets/?%s" % (CL_API, urllib.parse.urlencode(params))
        try:
            _, body = fetch(url, cl_headers())
        except urllib.error.HTTPError as exc:
            log_error("courtlistener docket lookup %s -> HTTP %s" % (params, exc.code))
            if exc.code in (401, 403):
                raise RuntimeError(
                    "CourtListener returned HTTP %s. Put a free API token in "
                    "~/.courtlistener_token (get one at "
                    "https://www.courtlistener.com/profile/api-token/)." % exc.code
                )
            continue
        except Exception as exc:                          # noqa: BLE001
            log_error("courtlistener docket lookup %s -> %r" % (params, exc))
            continue

        try:
            results = json.loads(body).get("results", [])
        except ValueError:
            continue
        if results:
            did = results[0].get("id")
            if did:
                state["courtlistener_docket_id"] = did
                state["courtlistener_absolute_url"] = results[0].get("absolute_url", "")
                log(CHANGE_LOG, "[%s] resolved CourtListener docket id %s via %s"
                    % (stamp(), did, params))
                return did

    raise RuntimeError(
        "could not resolve CourtListener docket id for %s in %s"
        % (cfg["docket_number"], cfg["court_id"])
    )


def cl_content(cfg, state):
    """Return normalized docket-entry text: one line per entry, newest first."""
    did = cl_resolve_docket_id(cfg, state)
    params = {"docket": did, "order_by": "-date_filed", "page_size": 100}
    url = "%s/docket-entries/?%s" % (CL_API, urllib.parse.urlencode(params))
    _, body = fetch(url, cl_headers())
    data = json.loads(body)

    rows = []
    for e in data.get("results", []):
        num = e.get("entry_number")
        num = "#%s" % num if num is not None else "#--"
        date = (e.get("date_filed") or "")[:10]
        desc = re.sub(r"\s+", " ", (e.get("description") or "")).strip()
        docs = []
        for d in e.get("recap_documents", []) or []:
            label = (d.get("description") or d.get("document_type") or "").strip()
            avail = "PDF" if d.get("is_available") else "no-pdf"
            if label:
                docs.append("%s [%s]" % (re.sub(r"\s+", " ", label), avail))
        line = "%s | %s | %s" % (num, date, desc)
        if docs:
            line += "  >> " + " ; ".join(docs)
        rows.append(line)

    if not rows:
        raise RuntimeError("CourtListener returned zero docket entries for docket %s" % did)
    return "\n".join(rows)


# ---------------------------------------------------------------- per-source

def source_content(src, cfg, state):
    if src["kind"] == "courtlistener":
        return cl_content(cfg, state)
    status, body = fetch(src["url"])
    if status != 200:
        raise RuntimeError("HTTP %s" % status)
    return normalize(strip_html(body))


def added_lines(old, new):
    diff = difflib.unified_diff(
        old.splitlines(), new.splitlines(),
        fromfile="previous", tofile="current", lineterm="", n=2,
    )
    body = list(diff)
    added = [l[1:].strip() for l in body
             if l.startswith("+") and not l.startswith("+++")]
    return body, added


def scan_keywords(added, keywords):
    hits = []
    blob = "\n".join(added)
    for kw in keywords:
        # "ORDER" and "MEMORANDUM" are given uppercase because that is how
        # docket text writes them, but match case-insensitively on word
        # boundaries so "Order" in prose still counts.
        if re.search(r"\b%s\w*" % re.escape(kw), blob, re.IGNORECASE):
            hits.append(kw)
    return hits


# --------------------------------------------------------------------- main

def past_cutoff(cfg):
    cutoff = dt.date.fromisoformat(cfg["cutoff_date"])
    return dt.date.today() > cutoff


def self_disable():
    """Unload the launchd agent so it stops firing after the cutoff."""
    plist = os.path.expanduser("~/Library/LaunchAgents/%s.plist" % LABEL)
    uid = os.getuid()
    try:
        subprocess.run(["launchctl", "bootout", "gui/%d/%s" % (uid, LABEL)],
                       timeout=20, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except Exception as exc:                              # noqa: BLE001
        log_error("self-disable bootout failed: %r" % (exc,))
    if os.path.exists(plist):
        try:
            os.rename(plist, plist + ".disabled")
        except OSError as exc:
            log_error("self-disable rename failed: %r" % (exc,))


def main():
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)

    os.makedirs(SNAP_DIR, exist_ok=True)

    if past_cutoff(cfg):
        log(CHANGE_LOG, "[%s] past cutoff %s - disabling agent"
            % (stamp(), cfg["cutoff_date"]))
        notify("Court watch retired",
               cfg["docket_number"],
               "Monitor auto-disabled after %s." % cfg["cutoff_date"],
               sound="Pop")
        self_disable()
        return 0

    state = load_state()
    fails = state.setdefault("consecutive_failures", {})
    changed_any = False

    for src in sorted(cfg["sources"], key=lambda s: s.get("priority", 99)):
        sid = src["id"]
        snap = os.path.join(SNAP_DIR, "%s.txt" % sid)

        try:
            content = source_content(src, cfg, state)
        except Exception as exc:                          # noqa: BLE001
            fails[sid] = fails.get(sid, 0) + 1
            log_error("%s: %r (consecutive failures: %d)" % (sid, exc, fails[sid]))
            threshold = cfg.get("stale_alert_after_consecutive_failures", 4)
            # One alert exactly at the threshold, then silence until recovery.
            if fails[sid] == threshold:
                notify("Court watch is blind",
                       src["label"],
                       "%d consecutive failures. Check errors.log." % fails[sid],
                       sound="Basso")
            continue

        if fails.get(sid):
            log(CHANGE_LOG, "[%s] %s recovered after %d failures"
                % (stamp(), sid, fails[sid]))
        fails[sid] = 0

        digest = sha(content)
        prev_digest = state.get("hashes", {}).get(sid)

        if prev_digest is None:
            state.setdefault("hashes", {})[sid] = digest
            with open(snap, "w", encoding="utf-8") as fh:
                fh.write(content)
            log(CHANGE_LOG, "[%s] BASELINE %s (%d lines)"
                % (stamp(), sid, len(content.splitlines())))
            continue

        if digest == prev_digest:
            continue

        try:
            with open(snap, encoding="utf-8") as fh:
                old = fh.read()
        except OSError:
            old = ""

        body, added = added_lines(old, content)
        hits = scan_keywords(added, cfg["high_priority_keywords"])
        high = bool(hits)
        changed_any = True

        header = "\n%s\n[%s] %s CHANGE: %s\n%s\n" % (
            "=" * 78, stamp(),
            "HIGH PRIORITY" if high else "routine",
            src["label"],
            ("keywords: %s" % ", ".join(hits)) if high else "no priority keywords",
        )
        log(CHANGE_LOG, header + "\n".join(body))

        with open(snap, "w", encoding="utf-8") as fh:
            fh.write(content)
        state.setdefault("hashes", {})[sid] = digest
        state.setdefault("last_change", {})[sid] = stamp()

        preview = " / ".join(a for a in added if a)[:200] or "(content removed)"
        if high:
            notify("HIGH PRIORITY - %s" % cfg["docket_number"],
                   src["label"],
                   "%s :: %s" % (", ".join(hits), preview),
                   sound="Sosumi",
                   speak=("Court docket update. %s." % ", ".join(hits))
                   if cfg.get("speak_high_priority") else None)
        else:
            notify("Docket update - %s" % cfg["docket_number"],
                   src["label"], preview, sound="Submarine")

    state["last_run"] = stamp()
    save_state(state)
    if not changed_any:
        log(CHANGE_LOG, "[%s] checked, no change" % stamp())
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:                              # noqa: BLE001
        log_error("FATAL: %r" % (exc,))
        sys.exit(1)
