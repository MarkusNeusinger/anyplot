#!/usr/bin/env python3
"""Watch Jules sessions until each one needs Claude, and print one line per change.

Usage: watch-sessions.py [--follow-up] [--base <branch>] <session-id> [<session-id> ...]

Run it under the Monitor tool (each stdout line is one event). It polls the Jules REST
API every POLL_SECONDS (default 45) and prints a line whenever a session's state or pull
request changes. When a session's pull request appears, it asks GitHub for the PR's base
branch and file count and warns about an empty one (a Jules PR once carried a single
commit with zero files), and it warns when a session opens a second pull request.

It exits 0 once every session has settled in a state that needs Claude (completed,
failed, awaiting plan approval, awaiting feedback, paused), 1 after MAX_MINUTES (default
28, under the Monitor's 30-minute cap) so the caller re-arms it, and 2 at once when the
API rejects the key or a session ID. After a follow-up message, pass --follow-up: a
session that is still in its old settled state then counts only once it has left that
state, so the watch does not end before Jules has picked the message up. With
--base, a pull request into any other branch gets a WARNING line: a sub-task's PR that
lands on `main` instead of its feature branch would skip the whole merge rule.

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


def api_key() -> str:
    key = os.environ.get("JULES_API_KEY", "").strip()
    if key:
        return key
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True, text=True, check=True
    ).stdout.strip()
    env_file = Path(common).parent / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            if line.startswith("JULES_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("JULES_API_KEY is neither exported nor in the main checkout's .env")


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


def pr_files(url: str) -> str:
    number = url.rstrip("/").rsplit("/", 1)[-1]
    result = subprocess.run(
        ["gh", "api", f"repos/{{owner}}/{{repo}}/pulls/{number}", "--jq", "[.changed_files, .base.ref] | @tsv"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def main() -> int:
    args = sys.argv[1:]
    follow_up = "--follow-up" in args
    args = [a for a in args if a != "--follow-up"]
    expected_base = ""
    if "--base" in args:
        position = args.index("--base")
        if position + 1 >= len(args):
            sys.exit(__doc__)
        expected_base = args[position + 1]
        del args[position : position + 2]
    ids = args
    if not ids:
        sys.exit(__doc__)
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
                title = (session.get("title") or "")[:70]
                print(f"{session_id} {state} {urls[-1] if urls else '-'} {title}", flush=True)
                if len(urls) > 1 and (previous is None or len(previous[1]) < len(urls)):
                    print(f"WARNING {session_id}: a second pull request {urls[-1]}; close the duplicate", flush=True)
                last[session_id] = (state, urls)
            for url in urls:
                if url not in checked_prs and state in SETTLED:
                    info = pr_files(url)
                    if info:
                        checked_prs.add(url)
                        files, base = info.split("\t")
                        if files == "0":
                            print(f"WARNING {session_id}: {url} has no changed files (empty commit)", flush=True)
                        else:
                            print(f"{session_id} PR {url} into {base}: {files} files", flush=True)
                        if expected_base and base != expected_base:
                            print(f"WARNING {session_id}: {url} targets {base}, not {expected_base}", flush=True)

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
