#!/usr/bin/env python3
"""Watch Jules sessions until each one needs Claude, and print one line per change.

Usage: watch-sessions.py [--follow-up] [--changes-only] [--base <branch>]
                         [--allow <path prefix> ...] <session-id> [<session-id> ...]

Run it under the Monitor tool (each stdout line is one event, and each event costs Claude
a turn). It polls the Jules REST API every POLL_SECONDS (default 45) and prints a line
whenever a session's state or pull request changes. When a session's pull request
appears, it asks GitHub for the PR's base branch and files, warns about an empty PR (a
Jules PR once carried a single commit with zero files), and warns when a session opens a
second pull request.

It exits 0 once every session has settled in a state that needs Claude (completed,
failed, awaiting plan approval, awaiting feedback, paused), 1 after MAX_MINUTES (default
28, under the Monitor's 30-minute cap) so the caller re-arms it, and 2 at once on a usage
error or when the API rejects the key or a session ID.

--follow-up    after a follow-up message: a session still in its old settled state counts
               only once it has left that state, so the watch does not end before Jules has
               picked the message up.
--changes-only print nothing for a session's first sighting unless it has already settled
               or opened a PR; a re-armed watch then stays quiet about sessions still running.
--base         a pull request into any other branch gets a WARNING line: a sub-task's PR
               that lands on `main` instead of its feature branch would skip the merge rule.
--allow        repeatable; every changed path outside these prefixes gets a WARNING line
               (scratch scripts such as fix_*.py at the repository root, PR text files).

The API key comes from JULES_API_KEY or from the `JULES_API_KEY=` line of the main
checkout's `.env`; it is never printed. GitHub calls go through `gh` from the current
directory, so run it inside the repository.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


API = "https://jules.googleapis.com/v1alpha/sessions/"
SETTLED = {"COMPLETED", "FAILED", "AWAITING_PLAN_APPROVAL", "AWAITING_USER_FEEDBACK", "PAUSED"}


def fail(message: str) -> None:
    """Exit 2, the code that tells the caller not to re-arm (`sys.exit(str)` would exit 1)."""
    print(message, file=sys.stderr, flush=True)
    sys.exit(2)


def api_key() -> str:
    key = os.environ.get("JULES_API_KEY", "").strip()
    if key:
        return key
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True, text=True
    ).stdout.strip()
    env_file = Path(common).parent / ".env" if common else None
    if env_file is not None and env_file.is_file():
        for line in env_file.read_text().splitlines():
            if line.startswith("JULES_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    fail("JULES_API_KEY is neither exported nor in the main checkout's .env")
    return ""


def fetch_session(key: str, session_id: str) -> dict | None:
    """Return the session, None on a transient failure; exit 2 when the API rejects the call."""
    request = urllib.request.Request(API + session_id, headers={"X-Goog-Api-Key": key})
    # One exception class per clause keeps the script valid on the system Python 3.12 as
    # well as 3.14. HTTPError is an OSError too, so it has to come first.
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read()
    except urllib.error.HTTPError as error:
        if error.code in (400, 401, 403, 404):
            print(f"ERROR {session_id}: the Jules API answered {error.code}; check the key and the ID", flush=True)
            sys.exit(2)
        return None
    except OSError:
        return None
    try:
        return json.loads(body)
    except ValueError:
        return None


def pr_urls(session: dict) -> list[str]:
    return [o["pullRequest"].get("url", "") for o in session.get("outputs", []) if "pullRequest" in o]


def gh_lines(path: str, jq: str) -> list[str] | None:
    result = subprocess.run(["gh", "api", "--paginate", path, "--jq", jq], capture_output=True, text=True)
    # rstrip only the line end: strip() would also eat a tab before an empty field.
    return result.stdout.rstrip("\r\n").splitlines() if result.returncode == 0 else None


def parse_args(argv: list[str]) -> tuple[bool, bool, str, list[str], list[str]]:
    follow_up = changes_only = False
    base, allow, ids = "", [], []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--follow-up":
            follow_up = True
        elif arg == "--changes-only":
            changes_only = True
        elif arg in ("--base", "--allow"):
            if i + 1 >= len(argv):
                fail(__doc__ or "usage error")
            if arg == "--base":
                base = argv[i + 1]
            else:
                allow.append(argv[i + 1])
            i += 1
        elif arg.startswith("--"):
            fail(__doc__ or "usage error")
        else:
            ids.append(arg)
        i += 1
    # A repeated ID would otherwise never let the watch settle.
    ids = list(dict.fromkeys(ids))
    if not ids:
        fail(__doc__ or "usage error")
    return follow_up, changes_only, base, allow, ids


def report_pr(session_id: str, url: str, expected_base: str, allow: list[str]) -> bool:
    """Print the PR line and its warnings; False when GitHub could not be asked yet."""
    number = url.rstrip("/").rsplit("/", 1)[-1]
    head = gh_lines(f"repos/{{owner}}/{{repo}}/pulls/{number}", "[.changed_files, .base.ref] | @tsv")
    if not head:
        return False
    files, base = head[0].split("\t")
    if files == "0":
        print(f"WARNING {session_id}: {url} has no changed files (empty commit)", flush=True)
    else:
        print(f"{session_id} PR {url} into {base}: {files} files", flush=True)
    if expected_base and base != expected_base:
        print(f"WARNING {session_id}: {url} targets {base}, not {expected_base}", flush=True)
    if allow:
        paths = gh_lines(f"repos/{{owner}}/{{repo}}/pulls/{number}/files", ".[].filename") or []
        outside = [p for p in paths if not any(p.startswith(prefix) for prefix in allow)]
        if outside:
            print(f"WARNING {session_id}: {url} changes paths outside {allow}: {outside[:8]}", flush=True)
    return True


def main() -> int:
    follow_up, changes_only, expected_base, allow, ids = parse_args(sys.argv[1:])
    key = api_key()
    poll = int(os.environ.get("POLL_SECONDS", "45"))
    deadline = time.monotonic() + 60 * int(os.environ.get("MAX_MINUTES", "28"))
    last: dict[str, tuple[str, tuple[str, ...]]] = {}
    moved: set[str] = set()  # sessions seen outside their first state (matters with --follow-up)
    checked_prs: set[str] = set()
    while True:
        for session_id in ids:
            session = fetch_session(key, session_id)
            if session is None:
                continue
            state, urls = session.get("state", "?"), tuple(pr_urls(session))
            previous = last.get(session_id)
            if previous is not None and previous[0] != state:
                moved.add(session_id)
            if previous != (state, urls):
                quiet = changes_only and previous is None and state not in SETTLED and not urls
                if not quiet:
                    title = (session.get("title") or "")[:70]
                    print(f"{session_id} {state} {urls[-1] if urls else '-'} {title}", flush=True)
                if len(urls) > 1 and (previous is None or len(previous[1]) < len(urls)):
                    print(f"WARNING {session_id}: a second pull request {urls[-1]}; close the duplicate", flush=True)
                last[session_id] = (state, urls)
            for url in urls:
                if url not in checked_prs and state in SETTLED and report_pr(session_id, url, expected_base, allow):
                    checked_prs.add(url)

        def settled(session_id: str) -> bool:
            state = last[session_id][0]
            return state in SETTLED and (not follow_up or session_id in moved)

        if len(last) == len(ids) and all(settled(i) for i in ids):
            print("ALL SESSIONS SETTLED: " + ", ".join(f"{i}={s}" for i, (s, _) in last.items()), flush=True)
            return 0
        if time.monotonic() > deadline:
            print("TIMEOUT, re-arm: " + ", ".join(f"{i}={s}" for i, (s, _) in last.items()), flush=True)
            return 1
        time.sleep(poll)


if __name__ == "__main__":
    sys.exit(main())
