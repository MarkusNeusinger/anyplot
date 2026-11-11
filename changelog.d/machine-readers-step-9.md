### Changed

- **Machine readers: the apex Worker deletes the verdict headers.** The owner
  redeployed `anyplot-api-proxy` on 2026-11-11, step 9 of the machine-readers
  runbook and its last one, so a caller of `anyplot.ai/api/*` can no longer
  label itself a verified bot in the telemetry. The runbook's state table says
  so, and "Verify on day one" gains the check that proved it: a forged
  `X-Prerender-Bot-Category` on `/api/llms-full.txt` and a forged
  `X-Verified-Bot-Category` on `/api/specs` both arrive with an empty
  `verified_category`.
