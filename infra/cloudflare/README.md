# Cloudflare: the edge in front of both Cloud Run services

This directory is the source for Cloudflare configuration that would otherwise
exist only in the dashboard. It was created with the origin gate
(`api/origin_gate.py`), because until then the Worker went unmentioned in the
repository and nobody without dashboard access could see what it does.

Two services stand behind the edge and both have an origin gate now. The API's
is in Python (`api/origin_gate.py`); the site's is in nginx
(`app/origin-gate.conf.template`). They share one secret, one set of five
verdicts, and one rollout procedure — the API's is done, the app's is
[further down](#the-sites-own-origin-anyplot-app).

The zone's security rules (WAF, Super Bot Fight Mode, and the transform and
custom rules) have no file here; they are recorded in
[Security rules](#security-rules-pro-since-2026-11-09) at the end of this file.

## What is here

| File | Role |
|---|---|
| `anyplot-api-proxy.js` | the Worker behind the route `anyplot.ai/api/*` |

**The `.js` is the source, not a draft.** Change it here and deploy it; change
it in the dashboard and pull it back here.

> **Deployed state (2026-09-27).** The Worker was redeployed from the current
> `.js` after #11221; the Transform Rule covers `anyplot.ai`, `www.anyplot.ai`,
> and `api.anyplot.ai`. Both gates are armed: `anyplot-app` runs with
> `ORIGIN_GATE=on`, the direct `*.run.app` URLs of both services answer 403,
> and `/health`, `/_health` and `/api/event` report `ok` through the edge.
> The standing rule still holds: the `.js` here mirrors the deployed bytes, so
> the next edit to it needs its own redeploy.

## The Worker

**Purpose.** `anyplot.ai/api/*` forwards to `https://api.anyplot.ai` with the
`/api` prefix stripped, so the apex can serve API paths on its own origin. The
one path it does not forward is `/api/event`: that is the Plausible analytics
endpoint (the same one `app/nginx.conf` proxies for the app service), and it
goes to Plausible untouched.

**`/api/event` is the one path that reaches the SITE's origin**, and that makes
it the second place the same-zone finding below bites. `fetch(request)` on that
path goes to the app service's nginx, which has an origin gate of its own — and
being a Worker subrequest inside the zone, it carries no Transform Rule header.
So the Worker stamps that branch too. Without it, arming the app gate answers
every Plausible pageview on the site with a 403, quietly, because a page does
not tell its visitor that analytics failed.

**Why it stamps the origin secret itself.** This is the finding the directory
exists for:

> A Worker subrequest to a host in the **same zone** bypasses that zone's
> Transform Rules.

The Transform Rule stamps `X-Origin-Secret` on everything Cloudflare forwards
for `api.anyplot.ai` — but not on a `fetch()` issued from inside a Worker.
Without those lines in the Worker, arming the gate takes `anyplot.ai/api/*`
down. The sibling repository kurrentschrift measured this on `/api/health`
during its own rollout: first `off`, then `off-seen` once the Worker had its
secret binding, then `ok` after arming.

**Why it strips the header first.** `headers` is cloned from the incoming
request, so without `headers.delete('X-Origin-Secret')` a caller could supply
that header itself and have it forwarded whenever the binding is unset. Two
consequences, one of them subtle: the documented "unset binding stamps nothing"
would be false, and an unarmed `/health` probe would report a spurious
`off-seen` — corrupting the one measurement the rollout hangs on.

**Why the binding is guarded by `if (env.ORIGIN_SECRET)`.** A missing binding
stamps nothing rather than sending an empty header, which makes the Worker
harmless while the gate is not yet armed. It is **not a rollback**: as long as
the Cloud Run service is armed, every apex API request without the header gets
a 403, so removing the binding takes that route down rather than freeing it.
Rolling back always happens on the API side — remove `ORIGIN_SECRET` from the
service **and promote the resulting revision by name** (the two commands are in
[`docs/reference/api.md`](../../docs/reference/api.md#origin-gate); never
`--to-latest`, which can promote a concurrent build's revision instead). The
ordering holds in both directions: the Worker starts stamping before the gate is
armed, and stops only after it is disarmed.

## Settings (dashboard)

| | |
|---|---|
| Script name | `anyplot-api-proxy` |
| Route | `anyplot.ai/api/*` (zone `anyplot.ai`) |
| Binding | `secret_text` **`ORIGIN_SECRET`** — value = Secret Manager `ORIGIN_SECRET`, the same one the Cloud Run service gets |
| `compatibility_date` | `2026-04-29` |
| Module type | ES module (`export default { fetch }`) |

## Deploying

**Dashboard** (the usual way): Workers & Pages → `anyplot-api-proxy` → Edit
code → paste the contents of `anyplot-api-proxy.js` → Deploy. The secret
binding is created once under Settings → Variables as a *Secret*; it survives
later deploys.

**API** (when it has to be scriptable) — a multipart request of metadata plus
module. Neither secret is ever typed. Both are read at execution time and each
reaches its command through a channel other processes cannot read: the origin
secret on `python3`'s **stdin**, the Cloudflare token on a `--config` file
descriptor. Neither is exported, so neither appears in a shell history, a file,
an argument vector, or a `/proc/<pid>/environ`.

It runs in a fail-fast subshell for a reason: a script `PUT` **replaces** the
bindings, so a failed or empty secret read would deploy an empty binding, the
Worker would stop stamping, and the armed apex route would go down — the very
outage this gate exists to avoid. Every step is checked before the next one
runs.

```bash
(
  set -euo pipefail

  # Command substitution strips the trailing newline gcloud may print — the
  # same newline that would otherwise make the value unusable in a header.
  ORIGIN_SECRET=$(gcloud secrets versions access latest \
    --secret=ORIGIN_SECRET --project=anyplot)
  [ -n "$ORIGIN_SECRET" ] || { echo "empty ORIGIN_SECRET — refusing to deploy"; exit 1; }

  # The secret goes in on STDIN, not in the child's environment: a
  # `VAR=value python3 …` prefix puts it in `/proc/<pid>/environ`, which any
  # same-UID process can read for the life of the call (Copilot review). The
  # shell variable itself is never exported.
  printf '%s' "$ORIGIN_SECRET" | python3 -c '
import json, sys
json.dump({
    "main_module": "worker.js",
    "compatibility_date": "2026-04-29",
    "bindings": [
        {"type": "secret_text", "name": "ORIGIN_SECRET", "text": sys.stdin.read()},
    ],
}, sys.stdout)' | curl --fail-with-body -sS -X PUT \
    "https://api.cloudflare.com/client/v4/accounts/{account}/workers/scripts/anyplot-api-proxy" \
    --config <(printf 'header = "Authorization: Bearer %s"\n' "$CF_API_TOKEN") \
    -F 'metadata=<-;type=application/json' \
    -F 'worker.js=@infra/cloudflare/anyplot-api-proxy.js;filename=worker.js;type=application/javascript+module'
)
```

**The explicit `filename=worker.js` is required.** Cloudflare resolves the
`main_module` named in the metadata (`worker.js`) against each part's
*filename*, not its form-field name; curl otherwise defaults the filename to
the local file's basename (`anyplot-api-proxy.js`), which does not match, and
the API answers `400 — Uncaught Error: No such module: worker.js` (observed
live 2026-09-04).

`pipefail` so a failing `python3` cannot be masked by a succeeding `curl`;
`--fail-with-body` so an HTTP error is a non-zero exit and still prints
Cloudflare's JSON reason, which plain `-f` swallows.

**The API token goes in through a file descriptor, not `-H`.** `curl`'s argument
vector is world-readable in `/proc` for as long as the request runs, so
`-H "Authorization: Bearer $CF_API_TOKEN"` would publish the credential that
authorises replacing this Worker to every process on the machine — the same
exposure the `ORIGIN_SECRET` handling above avoids, and the more dangerous of
the two. `--config <(…)` passes it on `/dev/fd/N` instead, and `printf` is a
shell builtin, so the token never reaches any argv at all (Copilot review). It
needs `bash` or `zsh`; under a shell without process substitution, write the
config line to a `600` temporary file and pass that path.

Then measure before trusting it — and read the answer against where the rollout
currently stands, because the same command means two different things:

```bash
curl -s https://anyplot.ai/api/health
#   "off-seen"  gate not yet armed, and the Worker IS stamping — the correct
#               result right after this deploy, and the state to reach before
#               arming. Not a failed deployment.
#   "off"       gate not armed and NOTHING was stamped — the binding is
#               missing. Arming now would take this route down.
#   "ok"        gate armed and this Worker's value matches. Only reachable
#               after the API side is armed.
```

Because a script `PUT` replaces the bindings wholesale, omitting one removes it
— the same trap that made the Cloud Run side use `--update-secrets` rather than
`--set-secrets` (`api/cloudbuild.yaml`). So either send every binding or deploy
from the dashboard.

## Measuring: did the header take this path?

`/health` is exempt from the origin gate and reports its verdict for the request
it was asked with — **never the value**:

| `origin_gate` | meaning |
|---|---|
| `off` | gate not armed, **no** header arrived |
| `off-seen` | gate not armed, the header arrived — the state to be in before arming |
| `ok` | gate armed, header matches |
| `missing` | gate armed, no header — this path would now be dead |
| `mismatch` | gate armed, wrong value (half-applied rotation) |

Every route into the service, in the order the rollout asks them:

```bash
curl -s https://api.anyplot.ai/health          # the public path (Transform Rule)
curl -s https://anyplot.ai/api/health          # THIS Worker
curl -s https://<api-run-url>/health           # must stay "off"/"missing": the closed door
```

The site's nginx is the fourth path and cannot be asked directly — it reaches
`https://api.anyplot.ai` for `@seo_proxy`, `/llms-full.txt` and `/sitemap.xml`,
so it rides on the first line's verdict. Probe it end to end instead:

```bash
curl -s -A 'Mozilla/5.0 (compatible; Googlebot/2.1)' https://anyplot.ai/scatter-basic | head -5
curl -sI https://anyplot.ai/llms-full.txt
```

After any change to the Worker, the Transform Rule or the secret: measure
first, arm second.

---

## The site's own origin (`anyplot-app`)

The same door, on the other service. `anyplot-app` also stands with
`ingress=all`, so `https://anyplot-app-r3tvmejsmq-ez.a.run.app` serves the whole
site with no bot challenge, no WAF and no rate limit — and a crawler user agent
sent there is relayed by `@seo_proxy` to `https://api.anyplot.ai`, where the
edge stamps the API's secret legitimately. The API gate cannot see that: the
request it receives really did come through the front door. Every such relay is
a repository query on a cache miss plus an outbound Plausible event, on someone
else's terms.

`app/origin-gate.conf.template` is the enforcing half. It is a template because
nginx cannot read the environment; the base image already ships the official
entrypoint's `20-envsubst-on-templates.sh`, so the secret arrives as an ordinary
Cloud Run environment variable and nothing new runs at container start.

**Modes.** `ORIGIN_GATE` unset, or anything that is not some casing of `on`, =
off; `ORIGIN_GATE=on` (or `On`, or `ON` — a plain `map` key is matched without
regard to case, and that is the direction to be wrong in) = 403 without a
matching header. `ORIGIN_SECRET` is the value. Unset means off, which is the
rollback and the state the code ships in. `ORIGIN_GATE=on` with no secret fails
CLOSED — the map keys are tagged so an empty secret cannot become "match
anything".

**There is a length ceiling on the secret**, and it is worth knowing before a
rotation rather than during one. nginx cannot hash a `map` key longer than one
bucket; the key here is `presented:` plus the whole secret, and the template
therefore sets `map_hash_bucket_size 512`. A secret past roughly 500 characters
makes nginx refuse to start — with the gate *off* it starts fine, because the
key is short then, so the failure would appear only at the moment of arming.
Cloud Run keeps the previous revision serving in that case, so it is a safe
failure rather than an outage, and the container smoke in `ci-image.yml` runs a
production-length secret on every relevant change.

**Why a header and not a `Host` rule.** Both would work here, which was an open
question until 2026-09-04: `anyplot.ai` and `www.anyplot.ai` are Cloud Run
**domain mappings**, so Cloudflare forwards the original Host and `$host` really
does tell the edge from the raw URL — Google's frontend answers a foreign Host
on a `run.app` address with its own 404 before the container is reached, so the
value cannot be spoofed. A Host rule still cannot be the mechanism:
`bot-serving-check.yml` probes this origin with crawler user agents *because*
Cloudflare 403s GitHub-runner IPs, it cannot spoof the Host either, and any
exception keyed on something public — a header it invents, a user agent — is
public with this repository. The exception has to be the shared secret; and once
the workflow carries the secret, the Host rule buys nothing the header does not.

### Hostnames this container serves

The Transform Rule has to cover every one of them, or arming the gate locks out
the visitors it was meant to protect.

| Hostname | Reaches the container via | Transform Rule |
|---|---|---|
| `anyplot.ai` | Cloud Run domain mapping, proxied by Cloudflare | **required** |
| `www.anyplot.ai` | Cloud Run domain mapping, proxied by Cloudflare — serves the site, it does not redirect | **required** |
| `anyplot.ai/api/event` | the apex Worker, `fetch(request)` to this origin | none: same-zone subrequest, the **Worker** stamps it |
| `python.anyplot.ai` | nothing today — `server_name` in `app/nginx.conf`, but no DNS record and no domain mapping (checked 2026-09-04) | add it in the same breath as the DNS record |
| `anyplot-app-r3tvmejsmq-ez.a.run.app` | direct | none — this is the door being closed |
| `anyplot-app-239660669828.europe-west4.run.app` | direct, the same service's second URL | none, same door |
| `candidate---anyplot-app-r3tvmejsmq-ez.a.run.app` | direct, the pre-traffic tag URL | none — `app/cloudbuild.yaml` sends the header itself |

The rule is a **Set**, not an Add: a caller that supplies its own
`X-Origin-Secret` must have it replaced, not appended.

### Callers that reach this origin without the edge

Each one is legitimate, each one would be 403'd into silence, and each now
carries the header itself.

| Caller | What it now sends |
|---|---|
| `app/cloudbuild.yaml` pre-traffic smoke | reads `ORIGIN_SECRET` from Secret Manager **inside the step** (not `availableSecrets`, which resolves at build start) and sends `X-Origin-Secret` on every probe. The build service account `239660669828-compute@developer.gserviceaccount.com` already holds `roles/secretmanager.secretAccessor` on the secret — it is the same account both triggers run as, and the API build already reads it. |
| `.github/workflows/bot-serving-check.yml` | sends the header from the `ORIGIN_SECRET` repository secret — the same one `sync-postgres.yml` already uses — and reads `/_health` first, so a missing or half-rotated secret fails with a message naming itself instead of reddening all ~36 crawler checks. |
| the apex Worker, `/api/event` | stamps from its own `ORIGIN_SECRET` binding (see above). |
| Cloud Run startup probe | nothing, and needs nothing: it is a `tcpSocket` check on 8080, not an HTTP probe (verified 2026-09-04). |
| IndexNow (`indexnow-submit.yml`, and Bing's verification fetch) | nothing, and needs nothing: both go to `https://anyplot.ai/<key>.txt`, i.e. through the edge. |

There are no Cloud Monitoring uptime checks on this project and no Lighthouse CI
(checked 2026-09-04); if one is added later it joins this table.

### Measuring: `/_health`

`/_health` is the gate's one exempt path — exact match, no prefix — and reports
`X-Origin-Gate` with the same five verdicts as the API's `/health`, for the
request it was asked with, never the value.

```bash
curl -sI https://anyplot.ai/_health           | grep -i x-origin-gate   # edge, apex
curl -sI https://www.anyplot.ai/_health       | grep -i x-origin-gate   # edge, www
curl -sI https://anyplot-app-r3tvmejsmq-ez.a.run.app/_health | grep -i x-origin-gate
#   the last one must stay "off" and become "missing": it is the closed door
```

The Worker's path cannot be asked through `/_health` — the Worker forwards only
`/api/event` to this origin — so it is measured on that endpoint instead. A
mapped crawler UA gets nginx's analytics shield (`202`) before Plausible is ever
called, so the probe costs no event:

```bash
curl -si -X POST -A 'Mozilla/5.0 (compatible; Googlebot/2.1)' \
  https://anyplot.ai/api/event -d '{}' | grep -i -e '^HTTP' -e x-origin-gate
#   202 + "off-seen"  the Worker is stamping — the state to reach before arming
#   202 + "off"       the Worker is NOT stamping; arming now kills site analytics
```

### Rollout

Ordered so that nothing is armed before it has been measured. Steps (a) and (b)
are safe on their own and can sit for days.

```bash
# (a) merge and deploy. Nothing is armed: the image defaults ORIGIN_GATE=off,
#     and the service declares no environment variables at all.
curl -sI https://anyplot.ai/_health | grep -i x-origin-gate     # expect: off

# (b) widen the Transform Rule to the app hostnames (dashboard: Rules →
#     Transform Rules → Modify Request Header), and redeploy the Worker so its
#     /api/event branch stamps too (see "Deploying" above). Then measure EVERY
#     path — each one must read off-seen before anything is armed:
curl -sI https://anyplot.ai/_health                          | grep -i x-origin-gate
curl -sI https://www.anyplot.ai/_health                      | grep -i x-origin-gate
curl -si -X POST -A 'Googlebot' https://anyplot.ai/api/event -d '{}' | grep -i x-origin-gate
curl -sI https://anyplot-app-r3tvmejsmq-ez.a.run.app/_health | grep -i x-origin-gate  # off

# (c) the two callers. The repository secret already exists (sync-postgres.yml
#     uses it) — confirm it, and confirm the build account can read the secret:
gh secret list --repo MarkusNeusinger/anyplot | grep ORIGIN_SECRET
gcloud secrets get-iam-policy ORIGIN_SECRET --project=anyplot
gh workflow run bot-serving-check.yml --repo MarkusNeusinger/anyplot   # expect: "origin gate: off-seen"

# (d) arm — the block below, not two flags. See "Arming, in full".

# (e) verify, in this order:
curl -sI https://anyplot.ai/_health | grep -i x-origin-gate                       # ok
curl -s -o /dev/null -w '%{http_code}\n' https://anyplot.ai/                      # 200
curl -s -o /dev/null -w '%{http_code}\n' https://anyplot-app-r3tvmejsmq-ez.a.run.app/  # 403
curl -s -A 'Mozilla/5.0 (compatible; Googlebot/2.1)' https://anyplot.ai/scatter-basic | grep canonical
curl -si -X POST -A 'Googlebot' https://anyplot.ai/api/event -d '{}' | head -1    # 202, not 403
gh workflow run bot-serving-check.yml --repo MarkusNeusinger/anyplot              # green

# (f) rollback — also its own block, below.
```

### Arming, in full

`gcloud run services update` alone is **not** the arm, and the reason is the
same one `docs/reference/api.md` § "Origin gate" writes out for the API: this
service pins traffic to a named revision (`app/cloudbuild.yaml` promotes with
`--to-revisions=<name>=100`), so an update creates a revision that serves
nothing, and `/_health` would still answer `off` while everything looked done
(Copilot review). Three more things each cost a comparable rollout somewhere,
so the block mirrors the API's, and runs fail-fast because half of these
commands feed the next one.

```bash
(
set -euo pipefail
SERVICE=anyplot-app
LOC="--project=anyplot --region=europe-west4"

# 0. Do not race the deploy pipeline: a build that already deployed its
#    candidate promotes it at the end, and that revision was cloned from the
#    pre-arm template — the promote would silently undo the arm, and its own
#    smoke accepts `off` by design.
gcloud builds list --project=anyplot --region=europe-west4 --ongoing --format="value(id)" | grep -q . && {
  echo "a Cloud Build is in flight; wait for it to finish (or fail) before arming."
  exit 1
}

# 1. Build the new revision from the image that is SERVING, not from whatever
#    is latest: `services update` clones the latest template, and this pipeline
#    deliberately leaves each build's smoked-but-unpromoted candidate there.
read -r SERVING LATEST <<<"$(gcloud run services describe "$SERVICE" $LOC --format=json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
      t=[x for x in d['status']['traffic'] if x.get('percent')==100]; \
      print(t[0]['revisionName'], d['status']['latestReadyRevisionName'])")"
IMAGE=$(gcloud run revisions describe "$SERVING" $LOC --format="value(spec.containers[0].image)")
test -n "$SERVING" && test -n "$IMAGE" || { echo "could not resolve the serving revision or its image"; exit 1; }
test "$SERVING" = "$LATEST" || echo "note: latest ($LATEST) is not serving ($SERVING) — image pinned to the serving one"

# 2. Pin the secret to a NUMBER, never `:latest`. Cloud Run resolves a
#    secret-backed variable when each instance starts, so with `:latest` a new
#    secret version reaches new instances while older ones keep the old value —
#    and since the edge stamps exactly one value, that shows up as intermittent
#    403s inside a single revision.
VERSION=$(gcloud secrets versions list ORIGIN_SECRET --project=anyplot \
  --filter="state=ENABLED" --sort-by=~createTime --limit=1 --format="value(name)")
test -n "$VERSION" || { echo "no ENABLED version of ORIGIN_SECRET"; exit 1; }

# 3. Update, then promote BY NAME. `--to-latest` would hand traffic to whatever
#    the pipeline last built.
SUFFIX="arm-$(date -u +%Y%m%d%H%M)"
gcloud run services update "$SERVICE" $LOC --image="$IMAGE" \
  --update-secrets="ORIGIN_SECRET=ORIGIN_SECRET:$VERSION" \
  --update-env-vars="ORIGIN_GATE=on" --revision-suffix="$SUFFIX"
gcloud run services update-traffic "$SERVICE" $LOC --to-revisions="$SERVICE-$SUFFIX=100"

# 4. Confirm, and confirm which revision answered. A build that promoted over
#    the arm shows up here as `off` on a path that carries the header.
curl -sI https://anyplot.ai/_health | grep -i x-origin-gate
gcloud run services describe "$SERVICE" $LOC --format="value(status.traffic)"
)
```

If the rendered config were invalid, nginx would not start, the revision would
never become ready, and the `update-traffic` would fail with traffic still on
the old revision — a safe failure, and the reason step 4 is not optional.

### Rolling back

Its own block, not the one above with a flag swapped: it has to run in the worst
state the service can be in, which includes the secret having been disabled
during the incident, so it looks nothing up.

```bash
(
set -euo pipefail
SERVICE=anyplot-app
LOC="--project=anyplot --region=europe-west4"

SERVING=$(gcloud run services describe "$SERVICE" $LOC --format=json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
      print(next(x['revisionName'] for x in d['status']['traffic'] if x.get('percent')==100))")
IMAGE=$(gcloud run revisions describe "$SERVING" $LOC --format="value(spec.containers[0].image)")
test -n "$IMAGE" || { echo "could not resolve the serving image"; exit 1; }

SUFFIX="disarm-$(date -u +%Y%m%d%H%M)"
gcloud run services update "$SERVICE" $LOC --image="$IMAGE" \
  --remove-env-vars=ORIGIN_GATE --revision-suffix="$SUFFIX"
gcloud run services update-traffic "$SERVICE" $LOC --to-revisions="$SERVICE-$SUFFIX=100"

curl -sI https://anyplot.ai/_health | grep -i x-origin-gate   # expect "off" or "off-seen"
)
```

Removing `ORIGIN_GATE` is enough; the secret may stay attached, which is what
makes re-arming one flag rather than two. Removing the Worker's binding is **not**
a rollback — while the service is armed, that takes `anyplot.ai/api/event` down
rather than freeing it.

`--update-secrets` and `--update-env-vars`, never the `--set-` forms: those
replace the whole set, so the next deploy would strip whatever was attached out
of band — the same trap `api/cloudbuild.yaml` documents for the API side. The
app's own `cloudbuild.yaml` names neither variable, so a deploy carries both
forward untouched.

**Rotation** is roll back, rotate, arm again, and there are now **five** copies
of one value: Secret Manager, the API service, the app service, the Worker
binding and the GitHub repository secret. The gate is off in between, which is
the documented safe state.

---

## Security rules (Pro, since 2026-11-09)

> **Status (2026-11-09):** the managed rules, the transform rule, and the smoke
> bypass are live, and the crawler block rule is deleted, so no crawler is
> blocked at the edge. A Managed Challenge for two ASNs is planned once the
> nginx analytics shield (#12860) is deployed. Whether Super Bot Fight Mode
> challenges "definitely automated" traffic is an open owner decision.

On 2026-11-09 the `anyplot.ai` zone moved to the Cloudflare Pro plan, and the
rules in this section were applied through the Cloudflare API with the scoped
zone token, `CLOUDFLARE_API_TOKEN` in `.env.example`. Hand that token to `curl`
through a `--config` file descriptor, as in [Deploying](#deploying). The rules live in
Cloudflare, not in this repository, so this section is their written record.
The dashboard is the source of truth for their current state: when the two
disagree, the dashboard is right and this section needs an update.

### The principle

No rule may hard-block traffic that could be a human. Two responses are
allowed instead: a Managed Challenge, an interstitial that a real browser
passes, and hiding the traffic on the analytics side, which has to be narrow,
dated, and measured.

### Managed rules (WAF)

Both rules sit in a new zone entry-point ruleset for the phase
`http_request_firewall_managed`, and both answer a match with a Managed
Challenge, never a block.

| | Cloudflare Managed Ruleset | OWASP Core Ruleset |
|---|---|---|
| Rule ID | `e07982f22bab4b0e9db17368b3337d8e` | `71ed4b6173954299bf5b8361e510db52` |
| Executes ruleset | `efb7b8c949ac4650a09736fc376e9aee` | `4814384a9e5d4991b9815dcfc25d2f1f` |
| Runs on | every host, minus the free-text routes (expression below) | the site hosts only: `(http.host in {"anyplot.ai" "www.anyplot.ai" "python.anyplot.ai"})` |
| Overrides | action `managed_challenge` for all of its rules | categories `paranoia-level-2`, `paranoia-level-3`, and `paranoia-level-4` disabled, which leaves paranoia level 1; anomaly score rule `6179ae15870a4bb7b2d480d4843b323c` at `score_threshold` 40 (Medium in the dashboard) with action `managed_challenge` |
| Since | 2026-11-09 | 2026-11-09 |

The Cloudflare Managed Ruleset runs on this expression:

```text
not ((http.host eq "api.anyplot.ai" and (starts_with(http.request.uri.path, "/agent") or starts_with(http.request.uri.path, "/mcp") or starts_with(http.request.uri.path, "/feedback"))) or (http.host eq "anyplot.ai" and starts_with(http.request.uri.path, "/api/agent")))
```

The excluded paths are the ones that carry free text: the public agent chat
(`/agent` on the API host, and `/api/agent`, its path on the apex through the
Worker), the MCP server (`/mcp`), and the site feedback (`/feedback`). Their
requests carry pasted data, such as a CSV, code, or a chat message, and to a
WAF that looks like injection. A challenge there would break these routes for
the people and MCP clients using them.

### Transform rule: verified bot category

| | |
|---|---|
| Rule ID | `19e144356aac49f3820233f564cf880f` |
| Ruleset | phase `http_request_late_transform`, beside the existing rule that sets `X-Origin-Secret` |
| Expression | `true` |
| Action | set the request header `X-Verified-Bot-Category` from the field `cf.verified_bot_category` |
| Since | 2026-11-09 |

Cloudflare fills `cf.verified_bot_category` only for a verified bot, so for
everyone else the header is absent. Nothing reads it yet: a later PR teaches
the API to tell verified AI assistants and crawlers from clients that only
spoof a user agent. Before the API relies on the header, measure two cases:

- A request that sends its own `X-Verified-Bot-Category` must arrive without
  it, or the header can be forged.
- A request through the apex Worker (`anyplot.ai/api/*`) may arrive without
  it, because a Worker subrequest bypasses the zone's Transform Rules (see
  [The Worker](#the-worker)).

### Custom rules

The smoke bypass is the first rule of the custom ruleset.

| Rule | ID | Action | Matches | State |
|---|---|---|---|---|
| Smoke bypass | `6a18892a4acf4461a38afe4e12ef6c00` | Skip, phase `http_request_sbfm` | the site hosts with the right `X-Smoke-Token` (see [The smoke bypass](#the-smoke-bypass)) | active since 2026-11-09 |
| Skip Bot Fight Mode for api | `56271bc6b54d4e1897af4447c72e425f` | Skip, phase `http_request_sbfm` | `http.host eq "api.anyplot.ai"`, so API and MCP clients are never challenged | active |
| Block public agent chat | `56aee2fcb6b547bb914a59bbc4da5e12` | Block | the public agent chat | disabled |

The AI Crawl Control block rule is gone. On 2026-11-09 it was first narrowed
to the two ByteDance crawlers, Bytespider and TikTokSpider, and then deleted
when the owner decided that every crawler is welcome. Blocking returns only on
evidence from the request logs. Until its own PR lands, `app/public/robots.txt`
still declines Bytespider; the crawler policy is in
[`docs/reference/seo.md`](../../docs/reference/seo.md#cloudflare-is-the-enforcement-layer).

### Other rules kept from before the move

| Rule | Kind | What it does | State |
|---|---|---|---|
| Rate limit for `api.anyplot.ai` | rate limiting rule | 100 requests per 10 seconds per IP; `/health` is exempt | active |
| Cache rule for `api.anyplot.ai` | cache rule | bypasses the cache by default | active |

### Super Bot Fight Mode

On Pro, Super Bot Fight Mode has one group for unverified bots, "definitely
automated". The "likely automated" group needs the Business plan or higher.

| Setting | Value on 2026-11-09 |
|---|---|
| Definitely automated | Allow |
| Verified bots | Allow |
| Static resource protection | Off |
| JavaScript detections | On, carried over from the Bot Fight Mode era |
| Optimize for WordPress | Off |

Switching "definitely automated" to Managed Challenge is an open owner
decision. The recommendation is to stay on Allow while every crawler is
welcome: verified bots are exempt either way, so a challenge would stop only
unverified automation, and that includes self-hosted AI agents and agentic
browsers that can't solve one. Revisit it at the Pro audit with the bot
analysis data.

If you switch it, verify the switch:

1. In the dashboard, set **Definitely automated** to **Managed Challenge**.
2. Run the post-merge smoke with the token, following the recipe in
   `.claude/skills/open-pr/SKILL.md`, section 4. Every check must pass.
3. Run the smoke once without the token, which is the recipe's last command
   without its `SMOKE_TOKEN=` prefix. Every site page must come back as a
   `SKIP` line marked `challenged by Cloudflare`, and the run exits 2. That
   proves the bypass let the previous run through, not a gap in the rule.
4. Watch Security → Analytics → Events for challenges on normal pages. A
   solved challenge is a browser, usually a human, so many unsolved ones on
   `/`, `/plots`, or a spec page mean the switch is catching visitors.
5. Update the table above with the new value and its date.

### AI policies

Nothing is blocked through the AI policies: `ai_bots_protection`,
`ai_training`, `ai_search`, `ai_user`, and every `ai_agents` entry are
disabled, and the managed robots.txt is off, so Cloudflare serves the
repository's `robots.txt` unchanged. With the crawler block rule deleted, no
crawler is blocked at the edge.

### The smoke bypass

`scripts/site-smoke.mjs`, the post-merge check that the site renders, loads
the live site in headless Chromium, which Cloudflare classes as definitely
automated. If that group is ever challenged, every run would meet a challenge
page instead of the site and check nothing; the script marks such a page as a
`SKIP` line and exits 2. The bypass lets the smoke through:

- **The rule.** Custom rule `6a18892a4acf4461a38afe4e12ef6c00`, first in the
  custom ruleset, created on 2026-11-09: a request to the site hosts that
  carries the header `X-Smoke-Token` with the secret value skips the phase
  `http_request_sbfm`. Its expression, with the value left out here:

  ```text
  (http.host in {"anyplot.ai" "www.anyplot.ai" "python.anyplot.ai"} and http.request.headers["x-smoke-token"][0] eq "<secret>")
  ```

- **What it skips.** Only the Super Bot Fight Mode phase. The managed rules and
  the OWASP rules still apply.
- **Where the value lives.** In the dev box's `.env` as `SMOKE_TOKEN` and in
  that rule, nowhere else: not in the repository, CI, or Secret Manager. The
  open-pr skill's recipe reads it from the shared checkout's `.env`.
- **Where the header goes.** The script adds it only to requests for the
  site's own origin, so neither `api.anyplot.ai` nor a third party sees it,
  and it never prints the value. `api.anyplot.ai` needs no bypass, because the
  API skip rule above already exempts it.
- **CI never needs it.** The "Browser boot" step of `ci-image.yml` runs the
  script against the container on localhost, with no Cloudflare in between.
- **If the value leaks**, a client can skip Super Bot Fight Mode on the site
  hosts and nothing more. To rotate it, change the rule's value and the `.env`
  line together.

### Planned: a Managed Challenge for two ASNs

Once the nginx analytics shield (#12860) is deployed, a custom rule answers
this expression with a Managed Challenge. It is not applied as of 2026-11-09.

```text
(ip.src.asnum in {132203 394380}) and not cf.client.bot and (http.host in {"anyplot.ai" "www.anyplot.ai" "python.anyplot.ai"})
```

`not cf.client.bot` keeps verified bots out of the challenge.

### Verify the rules

- **Events.** Security → Analytics → Events lists every request a rule acted
  on. Filter by service (managed rules, Super Bot Fight Mode, custom rules) or
  by a rule ID from the tables above to see what it challenged and why. After
  any change, look here first: a rise in challenges on the site hosts means a
  rule is catching visitors.
- **Bot analysis.** The bot analysis in the same Security analytics shows how
  Cloudflare classes the traffic. Compare the definitely-automated share
  before and after the switch above.
- **The smoke.** With the token, every check passes. Without it, every check
  passes too while "definitely automated" stays on Allow; once that group is
  challenged, the site pages come back as `SKIP` lines marked `challenged by
  Cloudflare`.
