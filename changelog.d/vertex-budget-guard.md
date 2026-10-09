### Added

- **Vertex AI budget guard.** A Cloud Run function in `automation/gcp/budget-guard/`
  receives the Cloud Billing notifications of the budget `anyplot Vertex AI cap`
  through an Eventarc Pub/Sub trigger and disables `aiplatform.googleapis.com`
  through the Service Usage API once the month's cost reaches the budget amount.
  It acts only on that budget's name, never enables anything, is idempotent
  under Pub/Sub redelivery, logs one structured line per message without the raw
  message, and has a dry-run switch for the first proof at 5 CHF. Budget
  notifications lag the spend by hours, so it bounds the damage rather than
  making the cap exact. Code only, not deployed: the runbook in its README and
  `docs/reference/gcp-budget-guard.md` carry the deploy, test and recovery steps.
  (#12109)
