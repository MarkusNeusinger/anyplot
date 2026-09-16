### Fixed

- **`impl-review` retries the staging download instead of reviewing an empty directory** — the
  step swallowed a lost `gsutil cp` (`2>/dev/null || true`), the render check right after it
  then failed on nothing, and because that failure set no `ai-review-failed` label, no watchdog
  case picked the PR up: it waited for a manual re-dispatch (#11360 on 2026-09-05, #11678 on
  2026-09-09, staging complete both times). The download now tries three times with a short
  backoff, stops as soon as both theme renders are on disk, and keeps `gsutil`'s stderr in a
  warning per failed attempt, so a transfer blip heals in the same run and a genuinely empty
  staging folder still fails loudly at the render check. (#11697)
