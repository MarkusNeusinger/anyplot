# GCP budget guard

> **Status (2026-10-09):** deployed in project `anyplot` as the Cloud Run service `vertex-budget-guard` (europe-west4) with its Eventarc trigger on `vertex-budget-alerts`; the synthetic end-to-end test disabled and re-enabled the Vertex AI API on 2026-10-09. The live test through real spend is still open.

The Vertex AI budget guard is a Cloud Run function that disables the Vertex AI API (`aiplatform.googleapis.com`) in project `anyplot` when the Cloud Billing budget `anyplot Vertex AI cap` is reached. It's the emergency brake behind the `aiplatform` spend cap that the [agent network design](../concepts/agent-network.md) treats as the real backstop for Vertex AI spend. The code lives in `automation/gcp/budget-guard/`. To deploy, test, or recover, follow its [runbook](../../automation/gcp/budget-guard/README.md).

The guard bounds the damage; it doesn't make the cap exact. Budgets use estimated billing data, and their notifications follow the spend by hours.

## How it works

1. Cloud Billing publishes the budget's status to the Pub/Sub topic `projects/anyplot/topics/vertex-budget-alerts` several times a day, also when nothing is spent.
2. An Eventarc trigger delivers each message to the function as a CloudEvent.
3. The function decodes the base64 JSON payload, decides, and writes one log line.
4. When the decision is to disable, the function calls the Service Usage API for each configured service. It reads the service's state; if the service is enabled, it posts `:disable` and waits up to 60 seconds for the operation to finish.

The budget, as set up on 2026-10-09: billing account `01C36E-578B56-0054F8`, filtered to project `anyplot` (number `239660669828`) and the Vertex AI service, 5 CHF per month while the brake is being proven and 30 CHF afterwards, credits excluded, and threshold alerts at 25, 50, 80, and 100 %.

A notification looks like this; `alertThresholdExceeded` is present only once a threshold is crossed:

```json
{
  "budgetDisplayName": "anyplot Vertex AI cap",
  "alertThresholdExceeded": 1.0,
  "costAmount": 5.12,
  "costIntervalStart": "2026-10-01T07:00:00Z",
  "budgetAmount": 5.0,
  "budgetAmountType": "SPECIFIED_AMOUNT",
  "currencyCode": "CHF"
}
```

## Decision rules

| Message | Result | `reason` |
|---------|--------|----------|
| Not decodable: no data, invalid base64, invalid JSON, or not a JSON object | No action | `event_without_data`, `event_without_message`, `message_without_data`, `invalid_base64`, `invalid_json`, `payload_not_object` |
| `budgetDisplayName` missing or not a string | No action | `missing_budget_name` |
| `budgetDisplayName` names another budget | No action | `other_budget` |
| `costAmount` missing, not a number, or not finite (including an integer too large for a float) | No action | `invalid_cost_amount` |
| `budgetAmount` missing, not a number, not finite, or not positive | No action | `invalid_budget_amount` |
| `costAmount` below `budgetAmount` | No action | `below_budget` |
| `costAmount` at or above `budgetAmount` | Disable, or only log in dry run | `budget_reached` |

The threshold keys don't take part in the decision. `alertThresholdExceeded` repeats what the two amounts already say, and `forecastThresholdExceeded` describes a forecast, which never cuts anything off. `currencyCode` is ignored because both amounts are in the budget's currency.

The name match is exact. If you rename the budget, also update `BUDGET_GUARD_BUDGET_NAME`; until then every message logs `other_budget` with the new name, and the guard does nothing.

## Service Usage call

The disable request is:

```http
POST https://serviceusage.googleapis.com/v1/projects/anyplot/services/aiplatform.googleapis.com:disable

{"disableDependentServices": false, "checkIfServiceHasUsage": "SKIP"}
```

- **`checkIfServiceHasUsage` is set explicitly.** `SKIP` is the API's default, but `gcloud services disable` sends `CHECK` unless you pass `--force`, and `CHECK` refuses a service used in the last 30 days. Vertex AI always was when this budget is reached.
- **Dependent services stay on.** If another enabled service depends on Vertex AI, the call fails with `FAILED_PRECONDITION`. The guard then logs an error and retries; it doesn't switch off services that nobody named.
- **The guard is idempotent.** A service that is already disabled counts as success, and the guard makes no disable call. Disabling a service that isn't enabled answers `FAILED_PRECONDITION`, so after a failed disable the guard reads the state again and treats `DISABLED` as success. This covers a redelivered message that raced the first one.
- **The path uses the project ID**, as gcloud does. The API reference shows the project number in its examples; `BUDGET_GUARD_PROJECT` accepts either.

The guard only ever calls `:disable`. It never enables a service.

## Logging

Every message produces exactly one JSON line on stdout, which Cloud Logging reads as a structured entry with its `severity` and `message`. The other fields are `component` (always `vertex-budget-guard`), `project`, `services`, `dry_run`, `budget`, `cost`, `amount`, `currency`, `action`, `reason`, and, when the guard acted, `results` and `error`. The raw message, its attributes, and the subscription are never logged.

| `action` | Severity | Meaning |
|----------|----------|---------|
| `none` | `INFO`, or `WARNING` for a message that isn't decodable | No action; `reason` says why |
| `dry_run` | `WARNING` | The guard would have disabled the services |
| `disable` | `CRITICAL` if a service was disabled now, `NOTICE` if all were already disabled | `results` holds the outcome per service |
| `failed` | `ERROR` | At least one service isn't confirmed disabled, or an unexpected error occurred; `error` says which and why |

`results` maps each service to `disabled`, `already_disabled`, `disable_pending`, or `failed`. `disable_pending` means that the API accepted the disable but the operation hadn't finished after 60 seconds. An operation can still fail after that, so the guard counts it as unconfirmed and raises; the redelivered message reads the state again.

To read the log lines:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="vertex-budget-guard" AND jsonPayload.component="vertex-budget-guard"' \
  --project anyplot --limit 20 --format 'value(timestamp,severity,jsonPayload.message)'
```

## Failures and retries

- **An unconfirmed disable is retried.** When a disable fails, or its operation is still running after 60 seconds, the function raises, Functions Framework answers HTTP 500, and Pub/Sub delivers the message again with exponential backoff (Eventarc's default is 10 to 600 seconds) until the subscription's retention runs out (24 hours by Eventarc's default). The message is acknowledged only once every service is confirmed disabled. The guard tries every configured service before it raises.
- **A no-op is acknowledged.** Undecodable messages and no-op decisions return normally, because a retry can't change them.
- **Unexpected errors are logged, then re-raised unchanged.** Credential, transport, and Service Usage API errors are expected failures, collected per service. Any other exception is a bug: the guard writes its one `failed` line with the exception type and re-raises it, so Pub/Sub retries it too.
- **Bad configuration fails the deploy.** The environment variables are validated at import, so an invalid value stops the container from starting instead of surfacing at the first real alert.
- **A dead-letter topic is optional.** The budget repeats its status every 20 to 30 minutes, so a message that expires after its retries loses nothing. The runbook shows how to attach one if you want to keep the evidence.

## Configuration

| Variable | Default | Meaning |
|----------|---------|---------|
| `BUDGET_GUARD_PROJECT` | `anyplot` | Project ID or number whose services are disabled |
| `BUDGET_GUARD_BUDGET_NAME` | `anyplot Vertex AI cap` | Display name of the budget to act on; exact match |
| `BUDGET_GUARD_SERVICES` | `aiplatform.googleapis.com` | Comma-separated services to disable; each must end in `.googleapis.com` |
| `BUDGET_GUARD_DRY_RUN` | `false` | `true` logs the decision without calling the API; accepts `true`, `false`, `1`, `0`, `yes`, `no`, `on`, and `off` |

## Permissions

| Identity | Role | Why |
|----------|------|-----|
| `vertex-budget-guard@anyplot.iam.gserviceaccount.com` (runtime) | `roles/serviceusage.serviceUsageAdmin` on the project | Reads the service state, disables the service, and polls the operation (`serviceusage.services.get`, `serviceusage.services.disable`, `serviceusage.operations.get`) |
| The same account as the trigger identity | `roles/run.invoker` on the `vertex-budget-guard` service | Eventarc pushes to a service that doesn't allow unauthenticated calls |
| The same account as the trigger identity | `roles/eventarc.eventReceiver` on the project | Receives the Eventarc events |
| Pub/Sub service agent | `roles/iam.serviceAccountTokenCreator` | Only if Pub/Sub was enabled in the project on or before 2021-04-08 |
| Cloud Build service account | `roles/run.builder` on the project | Only for the project's first Cloud Run source deploy |
| Budget notification service account | `roles/pubsub.publisher` on the topic | Granted on 2026-10-09 |

`roles/serviceusage.serviceUsageAdmin` also allows enabling services. A custom role with only the three permissions listed in the first row is the least-privilege alternative; the code never enables anything either way.

## Limits

- **Lag.** Notifications follow the spend by hours, and the spend in that window is billed. Choose a budget amount where the amount plus a few hours of worst-case spend is acceptable.
- **Calls stop, resources stay.** With the API disabled, requests to Vertex AI fail with `SERVICE_DISABLED`. Disabling deletes no resources, and a resource that bills while idle keeps billing. The agent network uses Vertex AI for per-request model calls (Claude Haiku 5.5 by default, Gemini 3.8 Flash as the second arm), which stop.
- **The brake stays on until you release it.** The guard never re-enables anything, and a new month resets the cost but not the API. While the month's cost is at or above the amount, a re-enabled API lasts only until the next notification, so raise the amount or turn dry run on first, as described in the runbook's recovery steps.
- **The topic is the trigger.** Budget notifications carry no signature, so anyone who can publish to `vertex-budget-alerts` can disable Vertex AI; the synthetic test in the runbook works exactly that way. The damage is availability, not spend: the guard can only switch Vertex AI off. Publish rights come from the topic's own policy and from project-level roles that include `pubsub.topics.publish`, such as Owner, Editor, and the Pub/Sub Admin, Editor, and Publisher roles. On 2026-10-09 the default Compute Engine service account holds Editor (agent network owner task 13), so anything that runs as it can publish. The runbook's deploy procedure audits these principals before the trigger exists; narrowing them is an owner decision.
- **Pinned dependencies.** `requirements.txt` pins exact versions, and Dependabot doesn't watch it; bump and redeploy by hand.

## Tests

`tests/unit/automation/gcp/test_budget_guard.py` covers the decision rules, the decoding, the configuration, the Service Usage calls against a fake session (no network), every handler path, and the entry point. The deploy directory has a hyphen in its name and isn't a Python package, so the test loads `main.py` from its path. It replaces `functions_framework`, which isn't a repository dependency, with a stub whose `cloud_event` decorator returns the function unchanged; the real decorator only registers the signature type and wraps the function.

```bash
uv run --extra test pytest tests/unit/automation/gcp
```
