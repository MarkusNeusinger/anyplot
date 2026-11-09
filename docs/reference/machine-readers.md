# Machine readers

> **Status (2026-11-09):** both writers are in the repository: the API (`api/machine_reads.py`) and the site's
> nginx (`app/nginx.conf`). The log bucket, the sink, and the `_Default` exclusion exist since 2026-11-09
> (steps 1 to 3 of [Set up the Google Cloud side](#set-up-the-google-cloud-side)); the linked dataset, the views,
> the two `READER` entries, and the trigger substitution (steps 4 to 8) wait for the owner's OK after the writers
> merge. The public numbers on `/stats` and the owner's section on `/debug` come in a later change.

A machine reader is a crawler, an AI assistant, or an MCP client that reads the catalogue. Every request one of
them makes is recorded as one content-free JSON line: who sent it (the vendor, why it fetches, and whether
Cloudflare verified it) and what it asked for (a route name, the catalogue ids of a served answer, and the
status). A line never holds an IP address, a user agent, a query string, or a raw path, and a person's request
never writes one.

The lines replace the Plausible bot site `bots.anyplot.ai` (see
[The retired Plausible bot site](#the-retired-plausible-bot-site)). They are a derived record next to the Cloud
Run request log, not a copy of it: the request log can't carry the verification header, because Cloud Run
records no request headers, so the line is the only place that says whether a crawler was verified. The line is
the 180-day record; the raw request log stays the 30-day one.

## When a line is written

Whoever answers the request writes its line:

- **The API** writes a line for every machine request it answers, including the prerendered pages, the
  `sitemap.xml` and the `llms-full.txt` that the site's nginx fetches from it. The `record_machine_read`
  middleware in `api/main.py` writes it after the response, inside the origin gate, so a request the gate
  refuses writes nothing.
- **The site's nginx** writes the same keys for what it answers without the API: `robots.txt`, `llms.txt`, the
  SPA shell it serves a crawler it doesn't prerender, the trailing-slash 301, and the origin gate's 403. It also
  writes the line of a hop to the API that failed with a 5xx, which the API can't see; the API leaves every 5xx
  of a hop nginx made to nginx, so nothing is counted twice. A hop the crawler abandoned (nginx logs 499) is
  the API's line.
- **The MCP server** writes one line per JSON-RPC request (`MachineReadMcpMiddleware` in
  `api/machine_reads.py`, registered in `api/mcp/server.py`). The HTTP middleware skips an answered `/mcp/`
  request and writes only one the transport refused (a 4xx or 5xx before any JSON-RPC request ran), and only
  for a crawler. Once the MCP middleware wrote a line, it marks the request's ASGI scope, which the mounted app
  shares with the HTTP middleware, so an error answer after the JSON-RPC chain ran is never written twice.

A request is a machine's by one of three signs:

1. Its user agent carries a vendor token of `AI_AGENTS` in `api/analytics.py`. nginx's `$machine_who` map
   repeats the table in the same order, and `tests/unit/api/test_machine_reads_nginx.py` holds the two
   together.
2. It carries a verdict of Cloudflare's (see [Verified or not](#verified-or-not)).
3. Its path says so: every `/seo-proxy/*` request is a machine read, because nginx sends only crawlers in its
   `$is_bot` map there; every JSON-RPC request to the MCP server is one too.

nginx adds a fourth sign for what it answers itself: a crawler in its `$is_bot` map. It never writes a line for
a static asset (`/assets/*`, images, fonts, scripts).

A browser has none of these signs, so a person is never in the data. A link a person follows from an AI
assistant's answer is a referral in Plausible, not a machine read.

## Fields

Schema 1. A renamed or removed field is schema 2; an added field or value isn't. Every value comes from a closed
set, is the status, or is a catalogue id that matches a fixed pattern. A value outside its set is left out
before the line is built, and a line that still fails validation is dropped with a warning that names the
field, never the value.

| Field | Values | Notes |
|---|---|---|
| `log_type` | `machine_read` | The sink's filter |
| `schema` | `1` | |
| `severity` | `INFO` | Cloud Logging moves it into the entry's severity |
| `writer` | `api`, `nginx` | |
| `service`, `revision` | Cloud Run's `K_SERVICE` and `K_REVISION`; nginx writes `anyplot-app` and `nginx` | Cloud Logging's `resource.labels` carry the real revision of both |
| `source` | `live`, `synthetic` | `synthetic` for a request that reached a raw `*.run.app` origin instead of the edge |
| `line_id` | 16 to 32 hex characters | A random value per line (nginx: `$request_id`), for deduplication only |
| `assistant` | the vendors of `AI_AGENTS`, or `other` | See the table in [Vendors and purposes](#vendors-and-purposes) |
| `kind` | `user_directed`, `index`, `training`, `search`, `inspection`, `seo`, `unknown` | The vendor token's purpose; `unknown` when no token matched |
| `verified_category` | Cloudflare's 17 verified bot categories, or `other` for a string not among them | Absent (the API) or empty (nginx) when the request carried no verdict |
| `client` | `claude`, `python`, `node`, `curl`, `other` | MCP lines only: the user agent's family |
| `surface` | `page`, `shell`, `code`, `spec`, `og`, `mcp`, `machine_file`, `api`, `other` | `page` is a prerender-path read; `shell` the SPA shell nginx served |
| `route` | a closed name per path, such as `spec_detail`, `code`, `og_spec`, `robots`, or `mcp` | `PAGE_ROUTES` and `API_ROUTES` in `api/machine_reads.py`, `$machine_route` in `app/nginx.conf` |
| `spec_id` | `^[a-z0-9]+(?:-[a-z0-9]+)*$`, at most 80 characters | The API's lines only, HTTP and MCP alike: on an HTTP line for a served answer (2xx or 304), on an MCP line under the `tool` rule below; nginx never writes it |
| `language` | `python`, `r`, `julia`, `javascript` | Same rule as `spec_id` |
| `library` | one of the 15 catalogue libraries | Same rule as `spec_id` |
| `host` | `anyplot.ai`, `www.anyplot.ai`, `python.anyplot.ai`, `api.anyplot.ai`, `other` | The host the reader asked |
| `method` | `GET`, `POST`, `HEAD`, `other` | The API sees a `HEAD` as the `GET` it becomes |
| `status` | 100 to 599 | On an MCP line, 200 for a JSON-RPC result and 500 for an error answer |
| `rpc` | `initialize`, `tools_list`, `tools_call`, `ping`, `other` | MCP lines only |
| `tool` | the six MCP tools, or `other` | MCP `tools_call` lines only. `get_spec_detail` and `get_implementation`, the two tools that look an id up, add the call's `spec_id` (and `library`) when they are catalogue ids and the call returned a result |

Deliberately absent: any IP address, the user agent, the referer, query strings, the raw path, request bodies,
any tool argument other than a validated catalogue id (a search's tags are never stored), session or client
identifiers, the Cloud Run instance, latency, and sizes. `spec_id` is written only for a served answer, so an id
a caller made up never lands: a 404 or a redirect carries the route name only. The retired slugs that
assistants still ask for are in the 30-day request log when someone needs them.

### Vendors and purposes

`AI_AGENTS` in `api/analytics.py` is the vendor table, ordered most specific first because matching is
substring-based: `claude-user`, `claude-searchbot`, and `claudebot` mean three different things.

| `kind` | Meaning |
|---|---|
| `user_directed` | A person asked their assistant to open the page. This is a reader. |
| `index` | An assistant's search index is building a corpus; no one is waiting. |
| `training` | A training-corpus crawler. |
| `search` | A classic search crawler, such as Googlebot or bingbot. |
| `inspection` | Search Console's URL inspection tool. |
| `seo` | A search-marketing tool's crawler, such as AhrefsBot or SemrushBot. |
| `unknown` | No token matched: a crawler only Cloudflare named, or a prerender-path reader `AI_AGENTS` doesn't list. |

A new crawler joins the table from the 30-day request log, never from these lines, which hold no user agent.

## Verified or not

A Cloudflare Transform Rule (rule `19e144356aac49f3820233f564cf880f`, phase `http_request_late_transform`) sets
the request header `X-Verified-Bot-Category` from `cf.verified_bot_category` on every request Cloudflare
proxies. For anyone Cloudflare didn't verify, the field is empty, and a Set with an empty value removes the
header, so a client can't forge a verdict through the edge. No verdict is the unverified bucket: it holds every
user agent a client merely claimed, and every vendor Cloudflare doesn't verify. Public copy says "unverified",
never "spoofed".

The same rule fires on nginx's own hop to `api.anyplot.ai`, where the caller is the app container, which is not
a verified bot, so the header is gone by the time the API sees a prerendered page. nginx therefore copies the
edge's verdict for the crawler into `X-Prerender-Bot-Category` on that hop, and the API accepts the copy on the
hop paths only (`/seo-proxy/*`, `/sitemap.xml`, and `/llms-full.txt`). `proxy_set_header` replaces a copy a
client sent, and an empty value sends no header. On the same hop nginx passes `X-Prerender-Source` (whether the
crawler came through the edge) and `X-Forwarded-Host` (which site host it asked).

Two residuals are known:

- **A direct caller of `api.anyplot.ai` on a hop path** can send all three hop headers itself. nginx's hop
  goes through the edge (`https://api.anyplot.ai`), so the API can't tell the hop from such a caller. With
  `X-Prerender-Bot-Category` the caller is counted as verified, with `X-Prerender-Source: synthetic` it hides
  itself from the live counts, and with `X-Forwarded-Host` it picks one of the four site hosts. Each moves a line
  between closed buckets and never writes a value outside the closed sets or the catalogue, so the privacy
  invariant holds. The paths are internal; nothing but nginx uses them. If the numbers ever look wrong, an
  nginx-stamped shared secret on the hop closes it.
- **The apex Worker** (`anyplot.ai/api/*`, `infra/cloudflare/anyplot-api-proxy.js`) forwards the incoming
  headers, and a Worker subrequest skips the zone's Transform Rules. The Worker deletes
  `X-Verified-Bot-Category` and `X-Prerender-Bot-Category` before it forwards, so the apex path reads as
  unverified by construction, never as a forged verdict.

`source` needs no header from the client. Both smoke checks of this repository, `bot-serving-check.yml` and the
deploy smoke in `app/cloudbuild.yaml`, probe the raw `*.run.app` origin, where Google's front end answers a
foreign `Host` itself, so the host can't be forged. nginx maps a `run.app` host to `synthetic` and passes it on
the hop; the API derives the same from its own `Host` header. Anyone else who knocks on a raw origin is
`synthetic` too, which keeps them out of every `source = 'live'` count.

## Where the lines go

| Resource | Name | Notes |
|---|---|---|
| Log bucket | `machine-reads` in `europe-west4` | Retention 180 days, Log Analytics on |
| Sink | `machine-reads` | Routes the filter below from `anyplot-api` and `anyplot-app` into the bucket |
| Linked dataset | `anyplot.machine_reads_logs` | Read-only view of the bucket in BigQuery (`_AllLogs`) |
| Views dataset | `anyplot.machine_reads` in `europe-west4` | The views of `api/telemetry/views/*.sql`, for Looker Studio and checks by hand |

The sink filter:

```text
resource.type="cloud_run_revision"
resource.labels.service_name=("anyplot-api" OR "anyplot-app")
jsonPayload.log_type="machine_read"
```

An exclusion on the `_Default` sink keeps the same lines out of the project's `_Default` bucket, so they live in
one place with one retention, and their bytes are ingested once. The agent chat's usage telemetry is the sibling
pair (the `agent-telemetry` bucket and the `agent_telemetry` datasets, [Agent usage
telemetry](agent-telemetry.md)); the two stay apart so the legal page and each bucket's description describe one
thing each.

A line written before the sink exists lands in `_Default` for 30 days and never reaches BigQuery, so the bucket,
the sink, and the exclusion come before the change that starts writing.

## Views

- **`anyplot.machine_reads.reads`** (`01_reads.sql`): one row per line, deduplicated on `line_id`, every field a
  typed column. nginx's empty `verified_category` reads as NULL. The deduplication spans the whole bucket, so a
  large query filters `_AllLogs.timestamp` itself instead of reading through this view.
- **`anyplot.machine_reads.daily`** (`02_daily.sql`): requests per UTC day by source, writer, vendor, purpose,
  verdict (`unverified` when there is none), audience, surface, and host, with the served answers, the 404s, and
  the distinct specs among them.

The audience is folded from the curated `kind` first and from Cloudflare's category second, so a vendor that
Cloudflare files differently keeps its documented purpose. The CASE is `AUDIENCE_SQL` in `api/machine_reads.py`,
and the daily view carries it verbatim (a test keeps the two equal):

| Audience | From `kind` | From the category, when `kind` says nothing |
|---|---|---|
| `for_person` | `user_directed` | `AI Assistant` |
| `index_training` | `index`, `training` | `AI Crawler`, `AI Search` |
| `search` | `search`, `inspection` | `Search Engine Crawler` |
| `seo` | `seo` | `Search Engine Optimization` |
| `preview` | | `Page Preview` |
| `other` | | everything else |

Cloudflare treats `AI Search` as search behaviour; it folds into `index_training` here because an AI search
index is what an assistant later answers from.

## Set up the Google Cloud side

Every step below is a production write. Each one runs only on the owner's named OK for that exact command; the
checks in [Verify on day one](#verify-on-day-one) are read-only.

Run steps 1 to 3 before the change that writes the lines merges. Run steps 4 to 7 after it merged, because the
view SQL comes from the merged repository, and step 8 right after step 7. Step 9 redeploys the Worker; run it
right after the merge.

| Steps | State |
|---|---|
| 1 to 3 (bucket, sink, `_Default` exclusion) | Done on 2026-11-09 at 08:40 UTC on the owner's OK, and read back: the bucket is `ACTIVE` with 180 days and analytics on; the sink and the exclusion carry the filter below |
| 4 to 8 (link, views dataset, views, `READER` entries, trigger substitution) | Pending the owner's OK, after the writers merge |
| 9 (Worker redeploy) | Pending the owner, after the writers merge |

1. Create the log bucket:

   ```bash
   gcloud logging buckets create machine-reads --project=anyplot --location=europe-west4 \
     --retention-days=180 --enable-analytics \
     --description="Machine reads of the catalogue: one content-free line per request by a crawler, an AI assistant or an MCP client, no IP and no user agent (docs/reference/machine-readers.md)"
   ```

2. Create the sink over both services:

   ```bash
   gcloud logging sinks create machine-reads \
     logging.googleapis.com/projects/anyplot/locations/europe-west4/buckets/machine-reads \
     --project=anyplot \
     --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name=("anyplot-api" OR "anyplot-app") AND jsonPayload.log_type="machine_read"'
   ```

   A sink into a log bucket of the same project needs no grant for its writer identity.

3. Keep the lines out of the `_Default` bucket. Run it after step 2:

   ```bash
   gcloud logging sinks update _Default --project=anyplot \
     --add-exclusion=name=machine-reads,filter='resource.type="cloud_run_revision" AND resource.labels.service_name=("anyplot-api" OR "anyplot-app") AND jsonPayload.log_type="machine_read"'
   ```

4. Link the bucket to BigQuery. This creates the linked dataset `anyplot.machine_reads_logs` with the `_AllLogs`
   view:

   ```bash
   gcloud logging links create machine_reads_logs --bucket=machine-reads \
     --location=europe-west4 --project=anyplot
   ```

5. Create the views dataset in the same location:

   ```bash
   bq --location=europe-west4 mk --dataset \
     --description="Views over the machine-read telemetry (api/telemetry/views)" anyplot:machine_reads
   ```

6. Create the views, in file order, from the repository root:

   ```bash
   for file in api/telemetry/views/0*.sql; do
     bq query --project_id=anyplot --location=europe-west4 --use_legacy_sql=false < "$file"
   done
   ```

   Run this step again after a change to the views merges: each statement replaces its view
   (`CREATE OR REPLACE VIEW`), and the lines in the bucket stay as they are.

7. Give the API's runtime identity, `anyplot-api@anyplot.iam.gserviceaccount.com`, read access on both datasets.
   It already holds `roles/bigquery.jobUser` on the project. `bq add-iam-policy-binding` answers "This feature
   requires allowlisting" for datasets, so add a `READER` entry to each dataset's access list instead:

   1. Pick a new, dated directory of your own that outlives the session, such as
      `~/backups/bq-access/2026-11-DD/`, and save the dataset's access list there (read-only):

      ```bash
      bq show --format=prettyjson anyplot:machine_reads > ~/backups/bq-access/2026-11-DD/machine_reads.json
      ```

   2. Edit the file to `{"access": [...the existing entries..., {"role": "READER", "userByEmail":
      "anyplot-api@anyplot.iam.gserviceaccount.com"}]}` and nothing else. `bq update --source` replaces the whole
      access list, so every existing entry has to stay.
   3. Write it back:

      ```bash
      bq update --source ~/backups/bq-access/2026-11-DD/machine_reads.json anyplot:machine_reads
      ```

   4. Repeat for `anyplot:machine_reads_logs`.

8. Point the API at the views through the deploy pipeline. `api/cloudbuild.yaml` writes `MACHINE_READS_DATASET`
   from the `_MACHINE_READS_DATASET` substitution on every deploy, so set it on the trigger, never with
   `gcloud run services update`, which the next deploy overwrites:

   ```bash
   gcloud builds triggers update github deploy-api --region=europe-west4 \
     --update-substitutions=_MACHINE_READS_DATASET=anyplot.machine_reads
   ```

   The setting takes effect with the next API deploy; run the trigger by hand to have it at once:

   ```bash
   gcloud builds triggers run deploy-api --region=europe-west4 --branch=main
   ```

9. Redeploy the Worker from `infra/cloudflare/anyplot-api-proxy.js` (see
   [Deploying](../../infra/cloudflare/README.md#deploying)), so the apex path deletes the two verdict headers.

Looker Studio needs no production write: connect it to `anyplot.machine_reads.daily` with your own account, which
holds the two roles on the project.

## Verify on day one

All of these are read-only.

1. Both writers' lines arrive as `jsonPayload`, in the new bucket:

   ```bash
   gcloud logging read 'jsonPayload.log_type="machine_read"' --project=anyplot \
     --bucket=machine-reads --location=europe-west4 --view=_AllLogs --freshness=1d --limit=20 \
     --format='table(timestamp, resource.labels.service_name, jsonPayload.writer, jsonPayload.assistant, jsonPayload.route, jsonPayload.status)'
   ```

   Lines from `anyplot-api` and from `anyplot-app` must both appear.

2. No line landed as text in `_Default`, which would miss the sink:

   ```bash
   gcloud logging read 'resource.labels.service_name=("anyplot-api" OR "anyplot-app") AND textPayload:"machine_read"' \
     --project=anyplot --freshness=1d --limit=5
   ```

   The answer must be empty.

3. After step 6, the verdicts that arrived. Every value must be one of Cloudflare's 17 strings; `other` means
   Cloudflare added a category, and `VERIFIED_CATEGORIES` and the nginx map need it:

   ```bash
   bq query --project_id=anyplot --location=europe-west4 --use_legacy_sql=false \
     'SELECT verified_category, COUNT(*) AS n FROM `anyplot.machine_reads.reads` GROUP BY 1 ORDER BY n DESC'
   ```

4. Googlebot's prerendered pages are verified. If every Googlebot `page` line reads `unverified`, the nginx copy
   header isn't arriving, and the header chain needs fixing before anything reads these numbers:

   ```bash
   bq query --project_id=anyplot --location=europe-west4 --use_legacy_sql=false \
     'SELECT verified, surface, COUNT(*) AS n FROM `anyplot.machine_reads.daily` WHERE day >= CURRENT_DATE() - 1 AND assistant = "google" GROUP BY 1, 2 ORDER BY n DESC'
   ```

   `Search Engine Crawler` must lead on `surface = page`.

5. A forged verdict arrives unverified. Note the minute, then send:

   ```bash
   curl -sS -o /dev/null -H 'X-Verified-Bot-Category: AI Crawler' \
     -A 'Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)' https://anyplot.ai/legal
   ```

   The `anyplot-app` line of that minute must carry `assistant: ahrefs` and `route: legal` and an empty
   `verified_category`: Cloudflare's Set removed the forged value.

6. The daily `bot-serving-check` run at 06:23 UTC shows up as `source: synthetic`, never as a live Googlebot.

7. In the first week, compare each vendor's total with the request log's tallies: about 2,500 Googlebot pages,
   about 5,600 ClaudeBot reads, and about 7,400 ExaSearchBot shell fetches a week, which nginx writes.

## What a line can't see

A line exists only for a request that reached one of the two servers:

- A read Cloudflare answers from its cache never reaches them. `/specs/*` answers `public, max-age=300`, and the
  og images answer `max-age` 3600 and 86400, so a repeat within that time is invisible. Cloudflare's AI Crawl
  Control is the only count at the edge.
- A request the WAF, Super Bot Fight Mode, or the edge rate limit refused never reaches them.
- By design, a line keeps no query string (filters), referer, size, or latency. The 30-day request log has those.

Public copy therefore says "requests that reached the server", never "all fetches".

## Cost

About 30,000 lines a week at roughly 600 bytes each, about 80 MB a month, are inside Cloud Logging's free
50 GiB per project and month, and the `_Default` exclusion keeps them from being counted twice. Retention past
30 days costs about $0.01 a month. Each BigQuery read of the bucket scans tens of MB; the result cache can't
answer repeats, because the linked `_AllLogs` view changes with every line, so the readers' own caches bound how
often a query runs. The total stays under $1 a month.

## The retired Plausible bot site

From 2026-08-18 until the machine-read lines replaced it in November 2026, the Plausible site `bots.anyplot.ai`
recorded the events `bot_fetch`, `asset_fetch`, and the machine side of `og_image_view`. It saw about 1.7 % of
the real crawler reads, because Plausible drops crawler and datacenter addresses, and 71 % of its last week was a
scanner that spoofed crawler user agents. Its history is exported to
`~/backups/plausible/bots.anyplot.ai-2026-11-09/` on the owner's machine: four Stats API pulls and a README with
the totals (7,184 `bot_fetch` events since 2026-08-18). The site stays dormant for 30 days after the change
deployed and is then deleted. The API no longer sends it anything, so its dashboard shows a flat line, not a
broken install.

## Files

| File | Role |
|---|---|
| `api/machine_reads.py` | The line's model, the closed sets, the route table, the HTTP writer, and the MCP middleware |
| `api/analytics.py` | `AI_AGENTS`, the vendor table both writers use |
| `api/main.py` | The `record_machine_read` middleware, inside the origin gate |
| `api/mcp/server.py` | Registers the MCP middleware |
| `app/nginx.conf` | nginx's maps, `log_format machine_read`, the one `access_log`, and the hop headers |
| `infra/cloudflare/anyplot-api-proxy.js` | The Worker, which deletes the verdict headers on the apex path |
| `api/telemetry/views/*.sql` | The two views |
| `tests/unit/api/test_machine_reads.py`, `tests/unit/api/test_machine_reads_nginx.py` | The two writers, held to the same keys and sets |
