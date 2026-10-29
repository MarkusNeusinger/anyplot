#!/usr/bin/env python3
"""Watch Jules sessions until each one needs Claude, and print one line per change.

Usage: watch-sessions.py <session-id> [<session-id> ...]

Run it under the Monitor tool (each stdout line is one event). It polls the Jules REST
API every POLL_SECONDS (default 45) and prints a line whenever a session's state or pull
request changes. When a session's pull request first appears, it asks GitHub for the
PR's file count and warns about an empty one (a Jules PR once carried a single commit
with zero files). It exits 0 once every session has settled in a state that needs Claude
(completed, failed, awaiting plan approval, awaiting feedback, paused), and 1 after
MAX_MINUTES (default 28, under the Monitor's 30-minute cap) so the caller re-arms it.

The API key comes from JULES_API_KEY or from the `JULES_API_KEY=` line of the main
checkout's `.env`; it is never printed. GitHub calls go through `gh` from the current
directory, so run it inside the repository.
"""

import json
import os
import subprocess
import sys
import time
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
    request = urllib.request.Request(API + session_id, headers={"X-Goog-Api-Key": key})
    # URLError and TimeoutError are both OSError, and JSONDecodeError is a ValueError; one
    # class per clause keeps the script valid on the system Python 3.12 as well as 3.14.
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read()
    except OSError:
        return None
    try:
        return json.loads(body)
    except ValueError:
        return None


def pr_url(session: dict) -> str:
    for output in session.get("outputs", []):
        if "pullRequest" in output:
            return output["pullRequest"].get("url", "")
    return ""


def pr_files(url: str) -> str:
    number = url.rstrip("/").rsplit("/", 1)[-1]
    result = subprocess.run(
        ["gh", "api", f"repos/{{owner}}/{{repo}}/pulls/{number}", "--jq", "[.changed_files, .base.ref] | @tsv"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def main() -> int:
    ids = sys.argv[1:]
    if not ids:
        sys.exit(__doc__)
    key = api_key()
    poll = int(os.environ.get("POLL_SECONDS", "45"))
    deadline = time.monotonic() + 60 * int(os.environ.get("MAX_MINUTES", "28"))
    last: dict[str, tuple[str, str]] = {}
    checked_prs: set[str] = set()
    while True:
        for session_id in ids:
            session = fetch_session(key, session_id)
            if session is None:
                continue
            state, url = session.get("state", "?"), pr_url(session)
            if last.get(session_id) != (state, url):
                title = (session.get("title") or "")[:70]
                print(f"{session_id} {state} {url or '-'} {title}", flush=True)
                last[session_id] = (state, url)
            if url and url not in checked_prs and state in SETTLED:
                info = pr_files(url)
                if info:
                    checked_prs.add(url)
                    files, base = info.split("\t")
                    if files == "0":
                        print(f"WARNING {session_id}: {url} has no changed files (empty commit)", flush=True)
                    else:
                        print(f"{session_id} PR {url} into {base}: {files} files", flush=True)
        if last and len(last) == len(ids) and all(state in SETTLED for state, _ in last.values()):
            print("ALL SESSIONS SETTLED: " + ", ".join(f"{i}={s}" for i, (s, _) in last.items()), flush=True)
            return 0
        if time.monotonic() > deadline:
            print("TIMEOUT, re-arm: " + ", ".join(f"{i}={s}" for i, (s, _) in last.items()), flush=True)
            return 1
        time.sleep(poll)


if __name__ == "__main__":
    sys.exit(main())
