# Performance Reference

Backend API response time measurements for pyplots-backend (Cloud Run, europe-west4).

## Infrastructure

| Component | Config | Notes |
|-----------|--------|-------|
| Cloud Run (backend) | 1 vCPU, 1Gi RAM, min-instances=1 | gen2, startup-cpu-boost=true |
| Cloud Run (frontend) | 1 vCPU, 256Mi RAM, min-instances=1 | nginx serving SPA |
| Cloud SQL | `db-f1-micro`, PostgreSQL 18, PD-SSD 10GB | Shared vCPU, 614MB RAM |
| Cache | In-memory TTLCache, 600s TTL, max 1000 entries | Per-instance, not shared |

## Baseline: Before `--no-cpu-throttling` (March 24, 2026)

Cloud Run config: `cpu-throttling=true` (request-based billing), 512Mi RAM.

### Uncached Requests (first hit after cache expiry, requires DB query)

| Endpoint | Samples | Min | Median | Max | Notes |
|----------|---------|-----|--------|-----|-------|
| `/specs` | 20 | 1.07s | 2.62s | 5.02s | Loads 259 specs + selectinload(impls) |
| `/stats` | 20 | 1.10s | 2.71s | 11.00s | Aggregate stats |
| `/libraries` | 4 | 0.46s | 6.96s | 7.06s | 9 rows, simple SELECT |
| `/specs/{id}` | 4 | 7.08s | 8.66s | 9.59s | Single spec + all impls |

### Cached Requests (cache hit, no DB)

| Endpoint | Samples | Min | Median | Max |
|----------|---------|-----|--------|-----|
| `/specs` | 10 | 13ms | 17ms | 19ms |
| `/stats` | 5 | 2ms | 3ms | 3ms |
| `/libraries` | 10 | 3ms | 37ms | 57ms |

### OOM Events (512Mi RAM)

14 OOM crashes in 15 days (March 10-23):

```
2026-03-23 04:37  Out-of-memory event detected
2026-03-20 23:12  Out-of-memory event detected
2026-03-18 20:26  Out-of-memory event detected
2026-03-15 22:42  Out-of-memory event detected
2026-03-14 20:00  Out-of-memory event detected (3x within 1 min)
2026-03-14 17:23  Out-of-memory event detected
2026-03-12 21:26  Out-of-memory event detected
2026-03-12 14:37  Out-of-memory event detected (2x within 1 min)
2026-03-10 14:23  Out-of-memory event detected
2026-03-10 13:29  Out-of-memory event detected (2x within 1 min)
```

## After `--no-cpu-throttling` + 1Gi RAM (March 25, 2026)

Cloud Run config: `cpu-throttling=false` (instance-based billing), 1Gi RAM.

Deployed revision `pyplots-backend-00085-4rn` at 2026-03-24 22:25 UTC.

### Uncached Requests

| Endpoint | Samples | Min | Median | Max | Notes |
|----------|---------|-----|--------|-----|-------|
| `/specs` | 20 | 0.77s | 1.85s | 9.20s | No improvement |
| `/stats` | 20 | 0.77s | 1.84s | 9.93s | No improvement |
| `/libraries` | 8 | 0.31s | 7.59s | 8.57s | No improvement |
| `/specs/{id}` | 6 | 7.08s | 8.76s | 9.59s | No improvement |

### Cached Requests

| Endpoint | Samples | Min | Median | Max |
|----------|---------|-----|--------|-----|
| `/specs` | 5 | 12ms | 14ms | 20ms |
| `/stats` | 2 | 2ms | 2ms | 2ms |
| `/libraries` | 10 | 18ms | 107ms | 228ms |

### OOM Events (1Gi RAM)

**0 OOM events since upgrade** (March 24-25). Memory increase resolved the OOM crashes.

## Cloud SQL Metrics (March 25, 2026)

Measured via Cloud Monitoring API while running `db-f1-micro`:

| Metric | Value | Notes |
|--------|-------|-------|
| CPU Utilization | 9-12% | Low — but shared 0.2 vCPU means real capacity is tiny |
| Memory Utilization | 100.0% | **Misleading** — includes OS page cache (normal Linux behavior) |
| Memory Total Usage | 184-219 MB | Actual PostgreSQL process memory |
| Memory Quota | 614 MB | Total available (~400 MB used as OS page cache) |
| Disk Utilization | 4.0% | 0.4 GB of 10 GB used |

**Note:** The `memory/utilization` metric at 100% is NOT indicative of memory pressure. Linux uses all free RAM as filesystem page cache, which is normal and beneficial. Actual PostgreSQL memory usage is ~200 MB / 614 MB.

### Root Cause: Shared 0.2 vCPU under concurrent load

Connection establishment is **not** the issue — `num_backends` metric shows 5-8 persistent connections to the `pyplots` database at all times. The connection pool (`pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`) keeps connections alive.

The bottleneck is the **0.2 shared vCPU** handling concurrent queries. When the 600s cache expires, the SPA fires 4 parallel requests (`/specs`, `/stats`, `/libraries`, `/specs/{id}`), each triggering a DB query simultaneously. With 0.2 shared vCPU split across 4 queries, each effectively gets ~0.05 vCPU — explaining the 6-9s response times.

```
# DB connections (pyplots database) — persistent, never drops to 0
gcloud monitoring: num_backends
  22:07 → 5    22:01 → 8    21:44 → 7    21:38 → 7
```

### Connection errors during OOM events

```
2026-03-20 23:12  FATAL: connection to client lost (7x simultaneous)
```

Cloud Run backend OOM crash at the same timestamp caused all active DB connections to drop.

## Cloud SQL Tier Comparison

| Spec | `db-f1-micro` (current) | `db-g1-small` | `db-custom-1-3840` |
|------|-------------------------|---------------|---------------------|
| CPU | 0.2 shared vCPU (burstable) | 0.5 shared vCPU (burstable) | 1 dedicated vCPU |
| RAM | 614 MB | 1.7 GB | 3.75 GB |
| CPU behavior | Sustained workloads throttled to 0.2 vCPU | Sustained throttled to 0.5 vCPU | Full core, no throttling |
| Price/month | ~$9 | ~$27 | ~$51 |
| PG buffer cache | ~0 MB (RAM full from OS+PG overhead) | ~800 MB | ~2.5 GB |
| Google recommendation | Dev/test only | Lightweight workloads | Min. for production |

Upgrade command: `gcloud sql instances patch pyplots-db --tier=db-g1-small`

## Conclusion

`--no-cpu-throttling` had **no measurable impact** on uncached request latency. The bottleneck is the Cloud SQL `db-f1-micro` instance (0.2 shared vCPU, 614 MB RAM). Memory is not the issue (actual usage ~200 MB). Likely causes: shared CPU throttling under concurrent load and/or connection establishment overhead through Cloud SQL Auth Proxy.

Cached responses are consistently fast (2-230ms). The problem only occurs when the 600s cache expires and the backend queries Cloud SQL.

**Next step:** Upgrade Cloud SQL from `db-f1-micro` to `db-g1-small` (0.5 vCPU, 1.7 GB, ~$27/mo) and re-measure.

Upgrade: `gcloud sql instances patch pyplots-db --tier=db-g1-small`

## After Cloud SQL upgrade to `db-g1-small` (pending)

TODO: Re-measure after upgrade and fill in results.

## How to Reproduce These Measurements

### Query slow requests (>500ms) for specific endpoints

```bash
gcloud logging read \
  'resource.type="cloud_run_revision"
   AND resource.labels.service_name="pyplots-backend"
   AND httpRequest.requestUrl=~"/(specs|stats|libraries)$"
   AND httpRequest.latency>="0.5s"' \
  --limit=30 \
  --freshness=1d \
  --format='table(timestamp,httpRequest.requestUrl,httpRequest.latency)'
```

### Query fast requests (<500ms) for cache hits

```bash
gcloud logging read \
  'resource.type="cloud_run_revision"
   AND resource.labels.service_name="pyplots-backend"
   AND httpRequest.requestUrl=~"/(specs|stats|libraries)$"
   AND httpRequest.latency<"0.5s"' \
  --limit=20 \
  --freshness=1d \
  --format='table(timestamp,httpRequest.requestUrl,httpRequest.latency)'
```

### Query OOM events

```bash
gcloud logging read \
  'resource.type="cloud_run_revision"
   AND resource.labels.service_name="pyplots-backend"
   AND textPayload=~"Out-of-memory"' \
  --limit=15 \
  --freshness=30d \
  --format='table(timestamp,textPayload)'
```

### Check Cloud Run service configuration

```bash
gcloud run services describe pyplots-backend \
  --region europe-west4 \
  --format='yaml(spec.template.metadata.annotations,spec.template.spec.containers[0].resources)'
```

### Check Cloud SQL instance tier

```bash
gcloud sql instances describe pyplots-db \
  --format='yaml(settings.tier,settings.dataDiskSizeGb,databaseVersion,settings.activationPolicy)'
```

### Cloud SQL CPU utilization (last 6 hours)

```bash
curl -s "https://monitoring.googleapis.com/v3/projects/$(gcloud config get-value project)/timeSeries?filter=metric.type%3D%22cloudsql.googleapis.com%2Fdatabase%2Fcpu%2Futilization%22&interval.startTime=$(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%SZ)&interval.endTime=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for ts in data.get('timeSeries', []):
    for p in ts.get('points', [])[:20]:
        t = p['interval']['endTime']
        v = p['value']['doubleValue']
        print(f'{t}: {v*100:.1f}%')
"
```

### Cloud SQL memory utilization

```bash
# Replace "cpu" with "memory" in the metric type:
# cloudsql.googleapis.com/database/memory/utilization
```
