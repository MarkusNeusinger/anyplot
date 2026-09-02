# Cloudflare: the apex Worker in front of the API

This directory is the source for Cloudflare configuration that would otherwise
exist only in the dashboard. It was created with the origin gate
(`api/origin_gate.py`), because until then the Worker went unmentioned in the
repository and nobody without dashboard access could see what it does.

## What is here

| File | Role |
|---|---|
| `anyplot-api-proxy.js` | the Worker behind the route `anyplot.ai/api/*` |

**The `.js` is the source, not a draft.** Change it here and deploy it; change
it in the dashboard and pull it back here.

> **After this lands, the Worker needs a redeploy.** The
> `X-Origin-Secret` lines are newer than the running script, so the repository
> and the deployment are out of step until it is pushed. Until then the Worker
> stamps nothing, `anyplot.ai/api/health` answers `off`, and arming the gate
> would take that route down — which is exactly what the rollout order in the
> pull-request description prevents.

## The Worker

**Purpose.** `anyplot.ai/api/*` forwards to `https://api.anyplot.ai` with the
`/api` prefix stripped, so the apex can serve API paths on its own origin. The
one path it does not forward is `/api/event`: that is the Plausible analytics
endpoint (the same one `app/nginx.conf` proxies for the app service), and it
goes to Plausible untouched.

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
service **and promote the resulting revision**. The ordering holds in both
directions: the Worker starts stamping before the gate is armed, and stops only
after it is disarmed.

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
module. The secret is never typed: it is read from Secret Manager at execution
time, stays in a shell variable, and reaches `curl` through stdin, so it lands
in no shell history, no file and no process list.

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

  ORIGIN_SECRET="$ORIGIN_SECRET" python3 -c '
import json, os, sys
json.dump({
    "main_module": "worker.js",
    "compatibility_date": "2026-04-29",
    "bindings": [
        {"type": "secret_text", "name": "ORIGIN_SECRET", "text": os.environ["ORIGIN_SECRET"]},
    ],
}, sys.stdout)' | curl --fail-with-body -sS -X PUT \
    "https://api.cloudflare.com/client/v4/accounts/{account}/workers/scripts/anyplot-api-proxy" \
    --config <(printf 'header = "Authorization: Bearer %s"\n' "$CF_API_TOKEN") \
    -F 'metadata=<-;type=application/json' \
    -F 'worker.js=@infra/cloudflare/anyplot-api-proxy.js;type=application/javascript+module'
)
```

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

Then measure before trusting it:

```bash
curl -s https://anyplot.ai/api/health   # expect "origin_gate":"ok"
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
