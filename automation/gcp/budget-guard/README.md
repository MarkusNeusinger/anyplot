# Vertex AI budget guard

A Cloud Run function that disables the Vertex AI API
(`aiplatform.googleapis.com`) in project `anyplot` when the Cloud Billing budget
`anyplot Vertex AI cap` is reached. It never enables anything.

How it decides, what it logs, its permissions, and its limits are in
[GCP budget guard](../../../docs/reference/gcp-budget-guard.md). This file is the
runbook: deploy, test, verify, and recover.

Budget notifications are not real time. Cost data reaches the budget hours after
the spend, so the guard bounds the damage; it doesn't make the cap exact.

## Before you begin

- The budget `anyplot Vertex AI cap` publishes to the Pub/Sub topic
  `projects/anyplot/topics/vertex-budget-alerts`.
- You run every command from the repository root.
- Your gcloud CLI is current: run `gcloud components update` first. The
  `--function` and `--base-image` flags of `gcloud run deploy` are verified with
  gcloud 534.0.0.
- The APIs for source deploys and Eventarc are enabled:

  ```bash
  gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
    artifactregistry.googleapis.com eventarc.googleapis.com --project anyplot
  ```

- If this is the project's first Cloud Run source deploy, the Cloud Build
  service account (by default the Compute Engine default service account) needs
  `roles/run.builder` on the project.
- If the Pub/Sub service agent was enabled on or before 2021-04-08, it needs
  `roles/iam.serviceAccountTokenCreator` for authenticated push.

## Deploy the guard

1. Create the service account:

   ```bash
   gcloud iam service-accounts create vertex-budget-guard --project anyplot \
     --display-name "Vertex AI budget guard"
   ```

2. Let it disable services in the project:

   ```bash
   gcloud projects add-iam-policy-binding anyplot \
     --member serviceAccount:vertex-budget-guard@anyplot.iam.gserviceaccount.com \
     --role roles/serviceusage.serviceUsageAdmin --condition None
   ```

3. Deploy the function with dry run on:

   ```bash
   gcloud run deploy vertex-budget-guard \
     --project anyplot \
     --source automation/gcp/budget-guard \
     --function budget_guard \
     --base-image python313 \
     --region europe-west4 \
     --no-allow-unauthenticated \
     --service-account vertex-budget-guard@anyplot.iam.gserviceaccount.com \
     --max-instances 1 \
     --concurrency 1 \
     --set-env-vars BUDGET_GUARD_DRY_RUN=true
   ```

   One instance handling one message at a time keeps redelivered messages
   from racing each other; a message that arrives while another is in progress
   is rejected and redelivered later. The other settings keep their defaults: project `anyplot`, budget
   `anyplot Vertex AI cap`, and service `aiplatform.googleapis.com`. To list
   more than one service, use gcloud's delimiter syntax, because a plain comma
   separates variables:
   `--set-env-vars "^;^BUDGET_GUARD_DRY_RUN=true;BUDGET_GUARD_SERVICES=aiplatform.googleapis.com,other.googleapis.com"`.

4. Let the same service account invoke the function as the trigger identity:

   ```bash
   gcloud run services add-iam-policy-binding vertex-budget-guard \
     --project anyplot --region europe-west4 \
     --member serviceAccount:vertex-budget-guard@anyplot.iam.gserviceaccount.com \
     --role roles/run.invoker
   ```

5. Let it receive Eventarc events:

   ```bash
   gcloud projects add-iam-policy-binding anyplot \
     --member serviceAccount:vertex-budget-guard@anyplot.iam.gserviceaccount.com \
     --role roles/eventarc.eventReceiver --condition None
   ```

6. Audit who can publish to the budget topic. Budget notifications carry no
   signature, so once the trigger exists, every principal that can publish to
   `vertex-budget-alerts` can disable Vertex AI. List the topic's own grants
   and the project-level roles that include `pubsub.topics.publish`:

   ```bash
   gcloud pubsub topics get-iam-policy vertex-budget-alerts --project anyplot
   gcloud projects get-iam-policy anyplot \
     --flatten 'bindings[].members' \
     --filter 'bindings.role=(roles/owner roles/editor roles/pubsub.admin roles/pubsub.editor roles/pubsub.publisher)' \
     --format 'table(bindings.role,bindings.members)'
   ```

   Expect Cloud Billing's publisher grant on the topic, made when the budget
   was connected to it, plus the owner. Any other principal can switch Vertex
   AI off: remove its grant, or accept it knowingly. On 2026-10-09 the default
   Compute Engine service account holds `roles/editor`, so every service that
   runs as it can publish. Custom roles with `pubsub.topics.publish` don't
   appear in this filter; check them separately if the project has any.

7. Create the trigger on the budget topic:

   ```bash
   gcloud eventarc triggers create vertex-budget-guard \
     --project anyplot \
     --location europe-west4 \
     --destination-run-service vertex-budget-guard \
     --destination-run-region europe-west4 \
     --event-filters type=google.cloud.pubsub.topic.v1.messagePublished \
     --transport-topic projects/anyplot/topics/vertex-budget-alerts \
     --service-account vertex-budget-guard@anyplot.iam.gserviceaccount.com
   ```

   The trigger can take up to two minutes to start delivering. Keep retries on
   (the gcloud default): a disable that failed or isn't confirmed after 60
   seconds answers HTTP 500, and Pub/Sub delivers the message again with
   backoff until the service is confirmed disabled.

### Optional: keep failed messages in a dead-letter topic

The budget sends a fresh notification every 20 to 30 minutes, so a message that
expires after its retries loses nothing, and the `ERROR` log line is the signal.
A dead-letter topic only keeps the evidence.

1. Find the trigger's subscription:

   ```bash
   gcloud eventarc triggers describe vertex-budget-guard --project anyplot \
     --location europe-west4 --format 'value(transport.pubsub.subscription)'
   ```

2. Create the topic and attach it, replacing `SUBSCRIPTION` with the output of
   the previous step:

   ```bash
   gcloud pubsub topics create vertex-budget-alerts-dead-letter --project anyplot
   gcloud pubsub subscriptions update SUBSCRIPTION \
     --dead-letter-topic projects/anyplot/topics/vertex-budget-alerts-dead-letter \
     --max-delivery-attempts 10
   ```

3. Let the Pub/Sub service agent forward to it:

   ```bash
   gcloud pubsub topics add-iam-policy-binding vertex-budget-alerts-dead-letter \
     --project anyplot \
     --member serviceAccount:service-239660669828@gcp-sa-pubsub.iam.gserviceaccount.com \
     --role roles/pubsub.publisher
   gcloud pubsub subscriptions add-iam-policy-binding SUBSCRIPTION \
     --project anyplot \
     --member serviceAccount:service-239660669828@gcp-sa-pubsub.iam.gserviceaccount.com \
     --role roles/pubsub.subscriber
   ```

## Test with a synthetic message

A synthetic message is indistinguishable from a real one. With dry run off it
really disables Vertex AI.

1. With dry run on, publish a message whose cost has reached the amount:

   ```bash
   gcloud pubsub topics publish vertex-budget-alerts --project anyplot \
     --message '{"budgetDisplayName":"anyplot Vertex AI cap","alertThresholdExceeded":1.0,"costAmount":5.12,"costIntervalStart":"2026-10-01T07:00:00Z","budgetAmount":5.0,"budgetAmountType":"SPECIFIED_AMOUNT","currencyCode":"CHF"}'
   ```

2. Read the guard's log lines:

   ```bash
   gcloud logging read \
     'resource.type="cloud_run_revision" AND resource.labels.service_name="vertex-budget-guard" AND jsonPayload.component="vertex-budget-guard"' \
     --project anyplot --limit 5 --format 'value(timestamp,severity,jsonPayload.message)'
   ```

   Expect `WARNING budget guard: dry run, would disable aiplatform.googleapis.com`.

3. Turn dry run off:

   ```bash
   gcloud run services update vertex-budget-guard --project anyplot \
     --region europe-west4 --update-env-vars BUDGET_GUARD_DRY_RUN=false
   ```

4. Publish the message from step 1 again and read the log as in step 2. Expect
   `CRITICAL budget guard: aiplatform.googleapis.com disabled`.

5. Verify, then recover as described in the next sections.

## Verify that Vertex AI is off

```bash
gcloud services list --enabled --project anyplot | grep aiplatform
```

No output means the API is disabled. Calls to Vertex AI now fail with
`SERVICE_DISABLED`.

## Recover

While the month's cost is at or above the budget amount, every notification
asks for the disable again, every 20 to 30 minutes. Re-enabling alone lasts
only until the next one.

1. Make the next notification a no-op. Either raise the budget amount and keep
   its display name (Billing > Budgets & alerts in the console), or turn dry run
   on:

   ```bash
   gcloud billing budgets list --billing-account 01C36E-578B56-0054F8 \
     --format 'value(name,displayName)'
   gcloud billing budgets update BUDGET_ID \
     --billing-account 01C36E-578B56-0054F8 --budget-amount 30CHF
   ```

   ```bash
   gcloud run services update vertex-budget-guard --project anyplot \
     --region europe-west4 --update-env-vars BUDGET_GUARD_DRY_RUN=true
   ```

2. Re-enable Vertex AI:

   ```bash
   gcloud services enable aiplatform.googleapis.com --project anyplot
   ```

3. Confirm that `gcloud services list --enabled --project anyplot | grep aiplatform`
   prints `aiplatform.googleapis.com`.

4. If you turned dry run on in step 1, turn it off again once the budget amount
   is above the month's cost.

The guard never re-enables anything. When a new month starts, the cost resets,
but Vertex AI stays disabled until you run step 2.

## Update the dependencies

`requirements.txt` pins exact versions, and Dependabot doesn't watch this
directory. To pick up a fix:

1. Bump the pins in `requirements.txt`.
2. Run `uv run --extra test pytest tests/unit/automation/gcp`.
3. Deploy again with the command from step 3 of the deploy procedure, without
   the `--set-env-vars` line, so the service keeps its current settings.
