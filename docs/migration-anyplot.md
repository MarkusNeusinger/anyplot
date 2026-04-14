# Migration Guide: pyplots.ai → anyplot.ai

> Comprehensive, ordered migration plan for rebranding the platform from pyplots.ai to anyplot.ai.
> Each task is marked with its owner: **USER** (manual), **CLAUDE** (automatable), or **MIXED**.

## Table of Contents

- [Overview](#overview)
- [Current Infrastructure](#current-infrastructure)
- [Phase 0: Preparation](#phase-0-preparation)
- [Phase 1: New GCP Project](#phase-1-new-gcp-project)
- [Phase 2: Code Changes](#phase-2-code-changes)
- [Phase 3: Data Migration](#phase-3-data-migration)
- [Phase 4: Deploy and Switch](#phase-4-deploy-and-switch)
- [Phase 5: Parallel Running and Redirect](#phase-5-parallel-running-and-redirect)
- [Phase 6: Plot Regeneration](#phase-6-plot-regeneration)
- [Rollback Strategy](#rollback-strategy)
- [Appendix A: Complete File Inventory](#appendix-a-complete-file-inventory)
- [Appendix B: GitHub Secrets Mapping](#appendix-b-github-secrets-mapping)
- [Appendix C: GCP APIs to Enable](#appendix-c-gcp-apis-to-enable)

---

## Overview

### What is Changing

| Area | Old | New |
|------|-----|-----|
| Domain | pyplots.ai / api.pyplots.ai | anyplot.ai / api.anyplot.ai |
| GCP Project | `pyplots` (308843905540) | `anyplot` (new) |
| GitHub Repo | `MarkusNeusinger/pyplots` | `MarkusNeusinger/anyplot` |
| Cloud Run Services | `pyplots-backend`, `pyplots-frontend` | `anyplot-api`, `anyplot-app` |
| Cloud SQL Instance | `pyplots-db` | `anyplot-db` |
| Database Name | `pyplots` | `anyplot` |
| GCS Buckets | `pyplots-images`, `pyplots-static` | `anyplot-images`, `anyplot-static` |
| Container Registry | `gcr.io` (deprecated, US region) | Artifact Registry `europe-west4` |
| DNS/CDN | Direct Cloud Run (no CDN) | Cloudflare (free CDN, global edge) |
| GitHub→GCP Auth | SA key export (`GCS_CREDENTIALS` JSON) | Workload Identity Federation (keyless) |
| Package Name | `pyplots` / `pyplots-website` | `anyplot` / `anyplot-website` |
| Plausible Site | `pyplots.ai` | `anyplot.ai` |
| Email | `admin@pyplots.ai` | `admin@anyplot.ai` |
| Brand Colors | Python blue #3776AB / yellow #FFD43B | Okabe-Ito green #009E73 |
| Exception Class | `PyplotsException` | `AnyplotException` |

### Why

The name "anyplot" signals that the platform is library-agnostic and will eventually support languages beyond Python (JavaScript, R, etc.). The rebrand also includes a visual redesign from a Python-centric data-dense aesthetic to an editorial-scientific look (see `docs/reference/brand.md` and `docs/reference/frontend-design.md`).

### Infrastructure Improvements

Since we are rebuilding GCP from scratch, we take the opportunity to fix technical debt and optimize for global traffic:

| Improvement | Why | Impact |
|-------------|-----|--------|
| **Artifact Registry** (replaces deprecated gcr.io) | gcr.io shutdown announced by Google. Current repo is 38 GB in US region. | Faster pulls, lower cost, locality, cleanup policies |
| **Cloudflare Free** (CDN + DNS) | Traffic is global. Currently no CDN, all requests hit europe-west4 directly. | Global edge caching, free SSL, DDoS protection, easy 301 redirects |
| **Workload Identity Federation** (replaces SA key) | Current setup exports a long-lived JSON key as GitHub Secret. Security risk. | Keyless auth, no credentials to rotate or leak |
| **AR Cleanup Policy** | Old gcr.io accumulated 38 GB of stale images with no cleanup. | Automatic deletion of old tags, predictable costs |
| **GCS via Cloudflare CDN** | Plot images served directly from GCS (single region). Global users see high latency. | Images cached at 300+ edge locations worldwide |

### Approach

1. **Freeze `main`** (no merges) so the current pyplots.ai keeps running undisturbed
2. **Create new GCP project** with improved infrastructure (Artifact Registry, Workload Identity Federation)
3. **Set up Cloudflare** as DNS and CDN for `anyplot.ai` (also handles the old `pyplots.ai` redirect later)
4. **Make all code changes on a branch** (`rebrand/anyplot`) -- runs **in parallel** with Phase 1
5. **Migrate data** (GCS images, database) to the new project
6. **Disable old Cloud Build triggers**, merge branch, deploy to new project, rename the GitHub repo
7. **Run both sites in parallel**, then redirect pyplots.ai → anyplot.ai via Cloudflare
8. **Regenerate plots incrementally** via the normal pipeline (not bulk-edit)

### Important: Do NOT

- **Do NOT rename the GitHub repo early** -- it breaks badges, Codecov, Cloud Build connections
- **Do NOT disable Cloud Build triggers** -- just don't merge to `main`; the old site stays running
- **Do NOT bulk-edit the 2,680 plot implementation files** -- they contain `pyplots.ai` in docstrings but will be regenerated incrementally through the normal pipeline
- **Do NOT manually merge implementation PRs** during the migration

---

## Current Infrastructure

> Snapshot taken 2026-04-14 via `gcloud` CLI. Verify before executing.

### GCP Project

| Property | Value |
|----------|-------|
| Project ID | `pyplots` |
| Project Number | `308843905540` |
| Region | `europe-west4` |
| Account | `meakeiok@gmail.com` |

### Cloud Run Services

| Service | CPU | Memory | Min/Max Instances | Port | Execution Env |
|---------|-----|--------|-------------------|------|---------------|
| `pyplots-backend` | 1 | 1Gi | 1/3 | 8000 | gen2 |
| `pyplots-frontend` | 1 | 512Mi | 1/3 | 8080 | gen2 |

**Backend environment variables:**
- `ENVIRONMENT=production`
- `GOOGLE_CLOUD_PROJECT=pyplots`
- `GCS_BUCKET=pyplots-images`
- `DATABASE_URL` (from Secret Manager)
- Cloud SQL: `pyplots:europe-west4:pyplots-db`

**Backend settings:** cpu-throttling enabled, concurrency 15, timeout 600s, startup-cpu-boost enabled

**Frontend:** VITE_API_URL=`https://api.pyplots.ai` (baked in at Docker build time), concurrency 15, timeout 60s

### Cloud SQL

| Property | Value |
|----------|-------|
| Instance | `pyplots-db` |
| Version | PostgreSQL 18 |
| Tier | `db-custom-1-3840` (1 vCPU, 3.75GB RAM) |
| Region | `europe-west4` |
| Connection | `pyplots:europe-west4:pyplots-db` |
| Public IP | Enabled |
| SSL | `ENCRYPTED_ONLY` |
| Databases | `postgres`, `pyplots`, `test` |
| Users | `postgres`, `pyplots` |
| Backups | Enabled, 7 retained, daily at 19:00, location EU |
| PITR | Enabled, 7 days transaction log retention |
| Flags | `work_mem=8192` |
| Authorized Networks | 2 entries (144.2.107.179/32, 88.84.9.94/32) |

### GCS Buckets

| Bucket | Location | Size | CORS |
|--------|----------|------|------|
| `pyplots-images` | europe-west4 | ~2.7 GB | None |
| `pyplots-static` | europe-west4 | ~750 KB (24 MonoLisa font files) | `pyplots.ai`, `localhost:3000/5173/5174` |
| `pyplots_cloudbuild` | US | Auto-managed | N/A |

### Secret Manager

| Secret | Created |
|--------|---------|
| `DATABASE_URL` | 2025-12-02 |
| `pyplots-github-github-oauthtoken-*` | 2025-12-02 |
| `pyplots-repo-github-oauthtoken-*` | 2025-12-02 |

### Service Accounts

| Email | Purpose |
|-------|---------|
| `308843905540-compute@developer.gserviceaccount.com` | Default Compute Engine SA |
| `pyplots-local-dev@pyplots.iam.gserviceaccount.com` | Local development |
| `github-actions@pyplots.iam.gserviceaccount.com` | GitHub Actions workflows |

### Cloud Build Triggers

| Trigger | Config File | Watched Files | Branch |
|---------|-------------|---------------|--------|
| `deploy-frontend` | `app/cloudbuild.yaml` | `app/**` | `^main$` |
| `deploy-backend` | `api/cloudbuild.yaml` | `api/**`, `core/**`, `pyproject.toml`, `specs/**` | `^main$` |

Both connected via: `projects/pyplots/locations/europe-west4/connections/pyplots-github/repositories/pyplots`

### GitHub Repository

| Property | Value |
|----------|-------|
| Name | `MarkusNeusinger/pyplots` |
| Homepage | `https://pyplots.ai` |
| Description | AI-powered Python plotting gallery... |

### GitHub Repository Secrets

| Secret | Used By |
|--------|---------|
| `GITHUB_TOKEN` | All workflows (auto) |
| `CLAUDE_CODE_OAUTH_TOKEN` | 6 workflows (spec-create, impl-generate, impl-repair, impl-review, report-validate, util-claude) |
| `GCS_CREDENTIALS` | impl-generate, impl-repair, impl-merge, ci-tests, sync-postgres |
| `INSTANCE_CONNECTION_NAME` | ci-tests, sync-postgres |
| `DB_USER` | ci-tests, sync-postgres |
| `DB_PASS` | ci-tests, sync-postgres |
| `DB_NAME` | ci-tests, sync-postgres |
| `CODECOV_TOKEN` | ci-tests |

### External Services

| Service | Identifier | Notes |
|---------|-----------|-------|
| Plausible Analytics | Domain: `pyplots.ai` | 19 event goals, ~25 custom properties |
| Codecov | Repo: `MarkusNeusinger/pyplots` | Token: `CODECOV_TOKEN` |

---

## Phase 0: Preparation

> **Prerequisites:** None
> **Duration:** ~30 minutes

### 0.1 Tag Last pyplots Version -- USER

```bash
git tag -a v1.1.0-pyplots-final -m "Last release as pyplots.ai before anyplot.ai rebrand"
git push origin v1.1.0-pyplots-final
```

### 0.2 Verify No In-Flight Work -- USER

Ensure all implementation workflows are complete before starting:

```bash
# Check for open implementation PRs
gh pr list --label "ai-approved" --state open
gh pr list --label "ai-rejected" --state open

# Check running workflows
gh run list --workflow=impl-generate.yml --status=in_progress
gh run list --workflow=impl-review.yml --status=in_progress
gh run list --workflow=impl-merge.yml --status=in_progress
```

All must return empty. If not, wait for completion or cancel.

### 0.3 Export Current GCP State -- USER

Save current configuration for reference:

```bash
gcloud config set project pyplots

# Export service configs
gcloud run services describe pyplots-backend --region=europe-west4 --format=yaml > /tmp/pyplots-backend.yaml
gcloud run services describe pyplots-frontend --region=europe-west4 --format=yaml > /tmp/pyplots-frontend.yaml
gcloud sql instances describe pyplots-db --format=yaml > /tmp/pyplots-cloudsql.yaml
gcloud secrets list --format=yaml > /tmp/pyplots-secrets.yaml
gcloud iam service-accounts list --format=yaml > /tmp/pyplots-service-accounts.yaml
```

### 0.4 Create Migration Branch -- CLAUDE

```bash
git checkout -b rebrand/anyplot main
```

All code changes in Phase 2 happen on this branch. The `main` branch stays frozen.

---

## Phase 1: New GCP Project

> **Prerequisites:** Phase 0 complete
> **Duration:** ~2-4 hours (includes DNS propagation wait)
> **Owner:** USER (all gcloud/console steps)

### 1.1 Create Project

```bash
# Create the new project (billing account required)
gcloud projects create anyplot --name="anyplot"

# Link billing account
gcloud billing projects link anyplot --billing-account=BILLING_ACCOUNT_ID

# Set as active project
gcloud config set project anyplot
```

### 1.2 Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  compute.googleapis.com \
  artifactregistry.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

> **Note:** We intentionally skip `containerregistry.googleapis.com` (deprecated). The new project uses Artifact Registry instead.

See [Appendix C](#appendix-c-gcp-apis-to-enable) for the full list matching the current project.

### 1.3 Create Artifact Registry Repository

The old project uses `gcr.io` (deprecated, 38 GB accumulated in US region). The new project uses Artifact Registry in `europe-west4` for locality and cleanup policies.

```bash
# Create Docker repository in the same region as Cloud Run
gcloud artifacts repositories create anyplot \
  --repository-format=docker \
  --location=europe-west4 \
  --description="anyplot container images"

# Set up cleanup policy: keep only the 5 most recent tags per image
cat > /tmp/ar-cleanup.json << 'EOF'
[
  {
    "name": "keep-recent",
    "action": {"type": "Delete"},
    "condition": {
      "tagState": "tagged",
      "olderThan": "2592000s"
    },
    "mostRecentVersions": {
      "keepCount": 5
    }
  },
  {
    "name": "delete-untagged",
    "action": {"type": "Delete"},
    "condition": {
      "tagState": "untagged",
      "olderThan": "86400s"
    }
  }
]
EOF
gcloud artifacts repositories set-cleanup-policies anyplot \
  --location=europe-west4 \
  --policy=/tmp/ar-cleanup.json
```

The new image paths will be:
```
europe-west4-docker.pkg.dev/anyplot/anyplot/backend:latest
europe-west4-docker.pkg.dev/anyplot/anyplot/frontend:latest
```

### 1.4 Create Cloud SQL Instance

```bash
gcloud sql instances create anyplot-db \
  --database-version=POSTGRES_18 \
  --tier=db-custom-1-3840 \
  --region=europe-west4 \
  --storage-size=10GB \
  --backup-start-time=19:00 \
  --enable-point-in-time-recovery \
  --retained-backups-count=7 \
  --backup-location=EU \
  --assign-ip \
  --ssl-mode=ENCRYPTED_ONLY \
  --database-flags=work_mem=8192
```

Create database and users:

```bash
# Create the main database
gcloud sql databases create anyplot --instance=anyplot-db

# Create the test database (for E2E tests)
gcloud sql databases create test --instance=anyplot-db

# Create the application user
gcloud sql users create anyplot --instance=anyplot-db --password=SECURE_PASSWORD
```

Authorize networks (use same IPs as old project):

```bash
gcloud sql instances patch anyplot-db \
  --authorized-networks="144.2.107.179/32,88.84.9.94/32"
```

> **Note:** Update these IPs if your development network has changed.

### 1.5 Create GCS Buckets

```bash
# Images bucket (production plot images)
gcloud storage buckets create gs://anyplot-images \
  --location=europe-west4 \
  --uniform-bucket-level-access

# Make images publicly readable
gcloud storage buckets add-iam-policy-binding gs://anyplot-images \
  --member=allUsers \
  --role=roles/storage.objectViewer

# Static assets bucket (fonts)
gcloud storage buckets create gs://anyplot-static \
  --location=europe-west4 \
  --uniform-bucket-level-access

# Make static assets publicly readable
gcloud storage buckets add-iam-policy-binding gs://anyplot-static \
  --member=allUsers \
  --role=roles/storage.objectViewer

# Set CORS on static bucket (required for font loading)
cat > /tmp/cors.json << 'EOF'
[
  {
    "origin": [
      "https://anyplot.ai",
      "https://www.anyplot.ai",
      "http://localhost:3000",
      "http://localhost:5173",
      "http://localhost:5174"
    ],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type", "Content-Length", "Cache-Control"],
    "maxAgeSeconds": 86400
  }
]
EOF
gcloud storage buckets update gs://anyplot-static --cors-file=/tmp/cors.json
```

### 1.6 Create Secrets

```bash
# DATABASE_URL for Cloud Run (Unix socket via Cloud SQL connector)
echo -n "postgresql+asyncpg://anyplot:SECURE_PASSWORD@/anyplot?host=/cloudsql/anyplot:europe-west4:anyplot-db" | \
  gcloud secrets create DATABASE_URL --data-file=-
```

> **Note:** The GitHub OAuth token secrets (`CLAUDE_CODE_OAUTH_TOKEN`) are stored in GitHub, not GCP Secret Manager. They remain the same after repo rename.

### 1.7 Create Service Accounts and Workload Identity Federation

```bash
# Local development service account
gcloud iam service-accounts create anyplot-local-dev \
  --display-name="anyplot Local Development"

# GitHub Actions service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"
```

Grant necessary roles:

```bash
PROJECT_NUMBER=$(gcloud projects describe anyplot --format='value(projectNumber)')

# GitHub Actions: Cloud SQL client (for sync-postgres, ci-tests)
gcloud projects add-iam-policy-binding anyplot \
  --member="serviceAccount:github-actions@anyplot.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# GitHub Actions: Storage admin (for image uploads in impl-generate/merge)
gcloud projects add-iam-policy-binding anyplot \
  --member="serviceAccount:github-actions@anyplot.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Local dev: Cloud SQL client + Storage read
gcloud projects add-iam-policy-binding anyplot \
  --member="serviceAccount:anyplot-local-dev@anyplot.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding anyplot \
  --member="serviceAccount:anyplot-local-dev@anyplot.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Cloud Build: allow access to Secret Manager (for DATABASE_URL)
gcloud projects add-iam-policy-binding anyplot \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud Build: allow deploying to Cloud Run
gcloud projects add-iam-policy-binding anyplot \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

# Cloud Build: allow acting as compute SA (for Cloud Run deployments)
gcloud iam service-accounts add-iam-policy-binding \
  $PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

Set up **Workload Identity Federation** for keyless GitHub Actions authentication (replaces exported SA keys):

```bash
# Create a Workload Identity Pool
gcloud iam workload-identity-pools create "github-actions" \
  --project="anyplot" \
  --location="global" \
  --display-name="GitHub Actions"

# Create an OIDC provider for GitHub
gcloud iam workload-identity-pools providers create-oidc "github" \
  --project="anyplot" \
  --location="global" \
  --workload-identity-pool="github-actions" \
  --display-name="GitHub" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='MarkusNeusinger/pyplots'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Allow GitHub Actions to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding \
  github-actions@anyplot.iam.gserviceaccount.com \
  --project="anyplot" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe anyplot --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-actions/attribute.repository/MarkusNeusinger/pyplots"
```

> **Note:** This eliminates the need for exported SA key JSON files (`GCS_CREDENTIALS`). GitHub Actions authenticate directly via OIDC tokens. See [Phase 4.8](#48-update-github-repository-secrets----user) for the GitHub side setup.
>
> **Timing:** The attribute-condition uses `MarkusNeusinger/pyplots` (the current repo name). After the GitHub rename in Phase 4.6, update the provider — see [Phase 4.6b](#46b-update-wif-provider-after-repo-rename----user).

Create a key for the local development service account only:

```bash
gcloud iam service-accounts keys create /tmp/anyplot-local-dev-key.json \
  --iam-account=anyplot-local-dev@anyplot.iam.gserviceaccount.com
```

### 1.8 Set Up Cloudflare and DNS -- USER

Cloudflare provides free CDN, global edge caching, automatic SSL, DDoS protection, and easy 301 redirects for the old domain.

**1. Create Cloudflare account** (if not already done) at [cloudflare.com](https://www.cloudflare.com/)

**2. Add `anyplot.ai` site** (Free plan)

**3. Update domain nameservers** at your registrar to Cloudflare's nameservers (provided during setup)

**4. Configure DNS records in Cloudflare:**

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| CNAME | `anyplot.ai` | `anyplot-app-HASH.a.run.app` | Proxied (orange cloud) |
| CNAME | `www` | `anyplot.ai` | Proxied |
| CNAME | `api` | `anyplot-api-HASH.a.run.app` | Proxied |
| MX | `anyplot.ai` | (your mail provider) | DNS only |

> **Note:** Get the Cloud Run URLs after first deployment (Phase 4.3). Use the `*.a.run.app` URLs, not IPs. Cloudflare's proxy handles SSL termination and caching.

**5. Configure Cloudflare settings:**

- **SSL/TLS**: Full (strict) -- Cloudflare ↔ Cloud Run is always HTTPS
- **Caching**: Cache Level = Standard, Browser Cache TTL = Respect Existing Headers
- **Page Rules** (add later for old domain redirect, see Phase 5.2):
  - `pyplots.ai/*` → Forwarding URL (301) → `https://anyplot.ai/$1`

**6. Set up GCS CDN via Cloudflare:**

To serve plot images through Cloudflare's global CDN instead of directly from GCS:

- Option A (recommended): Use a custom CNAME like `images.anyplot.ai` → `storage.googleapis.com` (proxied). Then update `core/config.py` and `core/images.py` to use `https://images.anyplot.ai/anyplot-images/` as the base URL.
- Option B: Keep `storage.googleapis.com` URLs but configure a Cloudflare Worker to cache them at the edge.

> **Decision needed:** Option A is simpler and gives full CDN coverage for all plot images globally. Requires an additional code change in Phase 2 (image URL base).

**7. Also add `pyplots.ai` to Cloudflare** (for Phase 5 redirect):

Add the old domain to Cloudflare now so DNS propagation is done by the time you need the redirect. Point it to the old Cloud Run services initially. The 301 redirect Page Rule will be activated in Phase 5.

**8. Set up MX records** for `admin@anyplot.ai` email

### 1.9 Cloud Build GitHub Connection -- SKIP (Execute in Phase 4)

> **This step requires the GitHub repo to be renamed first.** Execute it between Phase 4.6 and 4.7b. It is listed here for completeness of the GCP setup inventory. See [Phase 4.7a](#47a-set-up-cloud-build-github-connection----user-manual) for the actual instructions.

---

## Phase 2: Code Changes

> **Prerequisites:** Phase 0.4 (migration branch exists). **Runs in parallel with Phase 1** -- no dependency on GCP infrastructure.
> **Owner:** CLAUDE (on `rebrand/anyplot` branch)
> **Scope:** ~50 files, ~200 occurrences (excluding plots/ directory)

### 2.1 Package Identity

| File | Changes |
|------|---------|
| `pyproject.toml` | `name = "anyplot"`, `email = "admin@anyplot.ai"`, `Homepage = "https://anyplot.ai"`, `Repository = "https://github.com/MarkusNeusinger/anyplot"`, all `[tool.ruff.lint.isort] known-first-party` entries |
| `app/package.json` | `"name": "anyplot-website"`, `description` |
| `.env.example` | All comments and example values (`GCS_BUCKET=anyplot-images`, `DATABASE_URL` examples with `anyplot` user/db) |

### 2.2 Backend Core Configuration

| File | Changes |
|------|---------|
| `core/config.py` | `db_name` default `"anyplot"`, `gcs_bucket` default `"anyplot-images"`, `base_url` to `"https://anyplot.ai"`, `github_repository` to `"MarkusNeusinger/anyplot"`, both CORS origins to `anyplot.ai` |
| `core/images.py` | `GCS_STATIC_BUCKET = "anyplot-static"`, `FONT_CACHE_DIR = "/tmp/anyplot-fonts"`, rename `_draw_pyplots_logo()` to `_draw_anyplot_logo()`, update logo text rendering (replace `py`/`plots`/`.ai` with `any`/`.`/`plot()` per brand.md), all string literals |
| `core/constants.py` | Check for brand references |

### 2.3 Backend API

| File | Changes |
|------|---------|
| `api/main.py` | FastAPI `title="anyplot API"`, `description`, log messages, CORS `allow_origins`, import `AnyplotException` |
| `api/exceptions.py` | Rename `PyplotsException` → `AnyplotException`, update handler name |
| `api/analytics.py` | `DOMAIN = "anyplot.ai"`, all hardcoded URLs (~6 occurrences) |
| `api/routers/seo.py` | All ~31 occurrences: sitemap URLs, `og:site_name`, `DEFAULT_HOME_IMAGE`, `DEFAULT_CATALOG_IMAGE`, all page titles/descriptions |
| `api/routers/proxy.py` | `ALLOWED_ORIGINS`, `ALLOWED_BUCKET = "anyplot-images"`, `target_origin`, security comments |
| `api/routers/og_images.py` | URL references |
| `api/routers/health.py` | 3 occurrences |
| `api/routers/insights.py` | 1 occurrence |
| `api/mcp/server.py` | `FastMCP("anyplot")`, `PYPLOTS_WEBSITE_URL` → rename to `ANYPLOT_WEBSITE_URL` = `"https://anyplot.ai"`, docstring |
| `api/cache.py`, `api/dependencies.py`, `api/schemas.py` | Comment/docstring references |

### 2.4 Deployment Configuration

| File | Changes |
|------|---------|
| `api/cloudbuild.yaml` | `_SERVICE_NAME: anyplot-api`, Cloud SQL instance `anyplot:europe-west4:anyplot-db`, `GCS_BUCKET=anyplot-images`, **migrate all `gcr.io/$PROJECT_ID/` → `europe-west4-docker.pkg.dev/$PROJECT_ID/anyplot/`** (Artifact Registry), comment on line 1 |
| `app/cloudbuild.yaml` | `_SERVICE_NAME: anyplot-app`, `_VITE_API_URL: "https://api.anyplot.ai"`, **migrate all `gcr.io/$PROJECT_ID/` → `europe-west4-docker.pkg.dev/$PROJECT_ID/anyplot/`** (Artifact Registry), comment on line 1 |
| `api/Dockerfile` | Comment on line 1 |
| `app/Dockerfile` | Comment on line 1 |
| `docker-compose.yml` | If exists, update service names and env vars |

> **Artifact Registry migration:** Both `cloudbuild.yaml` files currently use `gcr.io/$PROJECT_ID/${_SERVICE_NAME}` for image paths. Replace all occurrences with `europe-west4-docker.pkg.dev/$PROJECT_ID/anyplot/${_SERVICE_NAME}`. The `gcr.io/cloud-builders/docker` and `gcr.io/cloud-builders/gcloud` builder images stay as-is (they are Google-maintained build steps, not our images).

### 2.5 Frontend Application

| File | Changes |
|------|---------|
| `app/index.html` | `<title>anyplot.ai</title>`, all `og:*` and `twitter:*` meta tags, preconnect href to `api.anyplot.ai`, font URLs to `anyplot-static`, JSON-LD `name`/`url`, Plausible hostname check `'anyplot.ai'` |
| `app/public/robots.txt` | `Sitemap: https://anyplot.ai/sitemap.xml` |
| `app/nginx.conf` | All `api.pyplots.ai` → `api.anyplot.ai` in proxy_pass, proxy_set_header, sitemap proxy |
| `app/src/constants/index.ts` | `GITHUB_URL` to `anyplot` repo |
| `app/src/theme/index.ts` | Comments (color values change is part of the redesign, separate from this migration) |
| `app/src/styles/fonts.css` | All 22 `pyplots-static` URLs → `anyplot-static` |
| `app/src/hooks/useAnalytics.ts` | All 4 `pyplots.ai` → `anyplot.ai` |
| `app/src/hooks/useUrlSync.ts` | Document title `pyplots.ai` → `anyplot.ai` |
| `app/src/analytics/reportWebVitals.ts` | Hostname check |
| `app/src/pages/HomePage.tsx` | Title, canonical URL |
| `app/src/pages/CatalogPage.tsx` | Title, og:title, canonical, breadcrumb |
| `app/src/pages/SpecPage.tsx` | All ~12 occurrences |
| `app/src/pages/StatsPage.tsx` | Title, description, Plausible link |
| `app/src/pages/LegalPage.tsx` | Title, meta tags, email addresses, Plausible link, GitHub link |
| `app/src/pages/McpPage.tsx` | All ~12 occurrences: titles, meta tags, `api.anyplot.ai/mcp/` URLs, MCP name |
| `app/src/pages/InteractivePage.tsx` | Allowed origins, meta tags |
| `app/src/pages/NotFoundPage.tsx` | Title, link text |
| `app/src/pages/DebugPage.tsx` | Breadcrumb |
| `app/src/components/Header.tsx` | Logo rendering (update text split for `any.plot()` branding) |
| `app/src/components/Breadcrumb.tsx` | JSDoc comment |

### 2.6 Frontend Tests

| File | Changes |
|------|---------|
| `app/src/hooks/useAnalytics.test.ts` | All ~9 hostname/URL assertions |
| `app/src/hooks/useUrlSync.test.ts` | Title assertions |
| `app/src/analytics/reportWebVitals.test.ts` | Hostname assertions |
| `app/src/components/Breadcrumb.test.tsx` | Label assertions |
| `app/src/components/Header.test.tsx` | Logo text assertion |
| `app/src/components/Footer.test.tsx` | GitHub URL assertion |
| `app/src/pages/McpPage.test.tsx` | URL and MCP name assertions |
| `app/src/pages/LegalPage.test.tsx` | Email assertions |
| `app/src/pages/NotFoundPage.test.tsx` | Link text assertion |

### 2.7 Backend Tests

| File | Changes |
|------|---------|
| `tests/unit/api/test_exceptions.py` | `AnyplotException` references |
| `tests/unit/api/test_proxy.py` | All ~32 occurrences (URL validation, allowed origins, bucket name) |
| `tests/unit/api/test_routers.py` | API URL assertions |
| `tests/unit/core/test_config.py` | Config value assertions |
| `tests/unit/core/test_images.py` | `_draw_anyplot_logo`, `anyplot-static` |
| `tests/unit/core/test_utils.py` | Header docstring assertion |
| `tests/unit/automation/scripts/test_sync_to_postgres.py` | Implementation header |
| `tests/integration/api/test_api_endpoints.py` | 2 occurrences |
| `tests/e2e/test_api_postgres.py` | 2 occurrences |
| `tests/e2e/conftest.py` | 2 occurrences |
| `tests/conftest.py` | 1 occurrence |

### 2.8 GitHub Actions Workflows

| File | Changes |
|------|---------|
| `.github/workflows/sync-postgres.yml` | `GCS_BUCKET` default `'anyplot-images'`, **replace `GCS_CREDENTIALS` secret with WIF auth step** |
| `.github/workflows/impl-generate.yml` | All 6 GCS `pyplots-images` references, **replace `GCS_CREDENTIALS` with WIF auth** |
| `.github/workflows/impl-merge.yml` | All 3 GCS path references, **replace `GCS_CREDENTIALS` with WIF auth** |
| `.github/workflows/impl-repair.yml` | 1 GCS staging path, **replace `GCS_CREDENTIALS` with WIF auth** |
| `.github/workflows/impl-review.yml` | GCS staging path, `pyplots.ai` in generated file header template, **replace `GCS_CREDENTIALS` with WIF auth** |
| `.github/workflows/ci-tests.yml` | **Replace `GCS_CREDENTIALS` with WIF auth**, update `INSTANCE_CONNECTION_NAME` references |
| `.github/workflows/notify-deployment.yml` | Environment URLs → `https://anyplot.ai`, `https://api.anyplot.ai/docs` |
| `.github/workflows/report-validate.yml` | AI prompt text mention |

**Workload Identity Federation in workflows:** Every workflow that currently uses `GCS_CREDENTIALS` (SA key JSON) needs to be updated to use the `google-github-actions/auth` action instead:

```yaml
# Old pattern (remove):
- name: Authenticate to GCP
  run: echo '${{ secrets.GCS_CREDENTIALS }}' > /tmp/gcs-key.json
  # ... export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcs-key.json

# New pattern (WIF):
- name: Authenticate to GCP
  uses: google-github-actions/auth@v2
  with:
    project_id: anyplot
    workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/providers/github

- name: Set up Cloud SDK
  uses: google-github-actions/setup-gcloud@v2
```

> **Note:** The `google-github-actions/auth` action automatically sets `GOOGLE_APPLICATION_CREDENTIALS` and authenticates `gcloud`/`gsutil`. No JSON key needed. Replace `PROJECT_NUMBER` with the actual project number from `gcloud projects describe anyplot --format='value(projectNumber)'`.

### 2.9 AI Prompts and Templates

| File | Changes |
|------|---------|
| `prompts/plot-generator.md` | All ~13 occurrences: docstring template `""" anyplot.ai`, title format, rendering notes |
| `prompts/quality-evaluator.md` | Title check criterion |
| `prompts/quality-criteria.md` | Title format criterion |
| `prompts/default-style-guide.md` | 2 brand references |
| `prompts/workflow-prompts/ai-quality-review.md` | Title check criterion |
| `prompts/templates/library-metadata.yaml` | `preview_url` template |
| `prompts/README.md` | Description |

> **Important:** Updating `prompts/plot-generator.md` is critical -- it controls the branding in every future generated plot.

### 2.10 Documentation

| File | Changes |
|------|---------|
| `README.md` | ~21 occurrences: title, badges, URLs, description. Badge URLs must use new repo name after rename. |
| `CLAUDE.md` | Verify and update any references |
| `.github/copilot-instructions.md` | Multiple references |
| `docs/reference/plausible.md` | ~13 occurrences: domain name, example URLs |
| `docs/reference/seo.md` | ~22 occurrences |
| `docs/reference/mcp.md` | ~16 occurrences: MCP endpoint URL |
| `docs/reference/api.md` | Base URL |
| `docs/reference/database.md` | Database name references |
| `docs/reference/performance.md` | URL references |
| `docs/reference/repository.md` | Repository references |
| `docs/reference/style-guide_pyplots.md` | May need renaming or archiving |
| `docs/concepts/vision.md` | Brand references |
| `docs/contributing.md` | URL references |
| `docs/development.md` | URL references |
| `docs/index.md` | URL references |
| `docs/workflows/overview.md` | URL references |
| `docs/workflows/report-issue.md` | URL references |
| `agentic/docs/project-guide.md` | ~14 occurrences: GCS names, DB names, URLs |
| `agentic/commands/update.md` | ~5 occurrences: GCS URLs, docstring template |

### 2.11 Configuration and Misc

| File | Changes |
|------|---------|
| `codecov.yml` | No changes needed (no pyplots references) |
| `.serena/project.yml` | Project name if referenced |
| `.claude/settings.local.json` | Check for references |

### 2.12 Brand Assets -- USER (Design Required)

These files need new designs per `docs/reference/brand.md`:

| File | New Content |
|------|-------------|
| `app/public/logo.svg` | New `any.plot()` wordmark: MonoLisa Bold, `.` in #009E73 scaled 145% |
| `app/public/favicon.svg` | Reduced `a.p` variant with green dot |
| `app/public/og-image.png` | Default OG image with anyplot branding |

> **Note:** The HTML mockup at `docs/reference/anyplot-landing-mockup.html` shows the visual direction.

---

## Phase 3: Data Migration

> **Prerequisites:** Phase 1 (new GCP infra exists), Phase 2 (code changes complete)
> **Duration:** ~1-2 hours

### 3.1 Copy GCS Images -- USER

```bash
# Copy production images (~2.7 GB, may take 10-20 minutes)
gcloud storage cp -r gs://pyplots-images/plots/ gs://anyplot-images/plots/

# Verify count
echo "Source:" && gcloud storage ls gs://pyplots-images/plots/ --recursive | wc -l
echo "Target:" && gcloud storage ls gs://anyplot-images/plots/ --recursive | wc -l
```

### 3.2 Copy Fonts to New Static Bucket -- USER

```bash
# Copy existing MonoLisa fonts
gcloud storage cp -r gs://pyplots-static/fonts/ gs://anyplot-static/fonts/

# Verify
gcloud storage ls gs://anyplot-static/fonts/
```

> **Future:** When new fonts (Fraunces, Inter) are ready for the redesign, upload them:
> ```bash
> gcloud storage cp /path/to/fraunces/*.woff2 gs://anyplot-static/fonts/
> gcloud storage cp /path/to/inter/*.woff2 gs://anyplot-static/fonts/
> ```

### 3.3 Initialize New Database -- USER

Run Alembic migrations against the new Cloud SQL instance:

```bash
# Option A: Via direct connection (if public IP is authorized)
DATABASE_URL="postgresql+asyncpg://anyplot:SECURE_PASSWORD@NEW_CLOUD_SQL_IP:5432/anyplot" \
  uv run alembic upgrade head

# Option B: Via Cloud SQL Proxy
# Start proxy in another terminal:
#   cloud-sql-proxy anyplot:europe-west4:anyplot-db --port=5433
DATABASE_URL="postgresql+asyncpg://anyplot:SECURE_PASSWORD@localhost:5433/anyplot" \
  uv run alembic upgrade head
```

### 3.4 Sync Plot Data to New Database -- MIXED

Run the sync script against the new database (from the `rebrand/anyplot` branch):

```bash
DATABASE_URL="postgresql+asyncpg://anyplot:SECURE_PASSWORD@NEW_CLOUD_SQL_IP:5432/anyplot" \
GCS_BUCKET=anyplot-images \
ENVIRONMENT=production \
  uv run python automation/scripts/sync_to_postgres.py
```

### 3.5 Fix GCS URLs in Database -- USER

The `implementations` table stores full GCS URLs. After syncing, update them:

```sql
-- Connect to the new database
-- psql -h NEW_CLOUD_SQL_IP -U anyplot -d anyplot

-- Update preview_url
UPDATE implementations
SET preview_url = REPLACE(preview_url, 'pyplots-images', 'anyplot-images')
WHERE preview_url LIKE '%pyplots-images%';

-- Update preview_html
UPDATE implementations
SET preview_html = REPLACE(preview_html, 'pyplots-images', 'anyplot-images')
WHERE preview_html LIKE '%pyplots-images%';

-- Verify
SELECT COUNT(*) FROM implementations WHERE preview_url LIKE '%pyplots%';
-- Should return 0
```

---

## Phase 4: Deploy and Switch

> **Prerequisites:** Phases 1-3 complete
> **Duration:** ~2-4 hours

### 4.1 Disable Old Cloud Build Triggers -- USER

Disable the old triggers **before** merging to prevent the old project from building code that references `anyplot-*` resources (which don't exist in the old project):

```bash
gcloud config set project pyplots
gcloud builds triggers update deploy-frontend --disabled --region=europe-west4
gcloud builds triggers update deploy-backend --disabled --region=europe-west4
```

The old `pyplots.ai` site continues running from the existing Cloud Run revision -- disabling triggers only prevents new builds.

### 4.2 Merge Rebrand Branch -- USER

```bash
git checkout main
git merge rebrand/anyplot
git push origin main
```

### 4.3 First Manual Deploy to New Project -- USER

Since Cloud Build triggers aren't set up yet in the new project, deploy manually:

```bash
gcloud config set project anyplot

# Build and push backend (uses Artifact Registry)
gcloud builds submit \
  --config=api/cloudbuild.yaml \
  --region=europe-west4

# Build and push frontend (uses Artifact Registry)
gcloud builds submit \
  --config=app/cloudbuild.yaml \
  --region=europe-west4
```

> **Note:** The first build may take longer as it populates the Artifact Registry. Verify the images appeared:
> ```bash
> gcloud artifacts docker images list europe-west4-docker.pkg.dev/anyplot/anyplot
> ```

### 4.4 Configure Cloudflare DNS -- USER

After services are deployed, get the Cloud Run URLs:

```bash
gcloud run services describe anyplot-app --region=europe-west4 --format='value(status.url)'
gcloud run services describe anyplot-api --region=europe-west4 --format='value(status.url)'
```

In the **Cloudflare dashboard** for `anyplot.ai`, update DNS records to point to the Cloud Run URLs:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| CNAME | `anyplot.ai` | `anyplot-app-HASH.a.run.app` | Proxied (orange cloud) |
| CNAME | `www` | `anyplot.ai` | Proxied |
| CNAME | `api` | `anyplot-api-HASH.a.run.app` | Proxied |

If using Cloudflare CDN for GCS images (Option A from Phase 1.8):

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| CNAME | `images` | `storage.googleapis.com` | Proxied |

Then add a **Cloudflare Transform Rule** to rewrite the Host header for the `images` subdomain so GCS serves the correct bucket.

> **Note:** SSL is handled by Cloudflare automatically. No Cloud Run domain mappings or Google-managed certificates needed. In Cloud Run, ensure `--ingress=all` is set (default) so Cloudflare can reach the services.

### 4.5 Verify anyplot.ai -- USER

Run through this checklist before proceeding:

- [ ] `https://anyplot.ai` loads the homepage
- [ ] `https://api.anyplot.ai/health` returns healthy status
- [ ] `https://api.anyplot.ai/docs` shows Swagger UI with "anyplot API" title
- [ ] Plot catalog page loads with images from `anyplot-images` bucket
- [ ] Fonts load correctly (check browser DevTools > Network for `anyplot-static` requests)
- [ ] `https://api.anyplot.ai/mcp/` MCP endpoint responds
- [ ] Click a specific plot -- detail page renders with correct images
- [ ] SEO proxy works: `curl -H "User-Agent: Googlebot" https://anyplot.ai/scatter-basic/matplotlib` returns meta tags with `anyplot.ai`
- [ ] Sitemap: `https://anyplot.ai/sitemap.xml` contains `anyplot.ai` URLs
- [ ] Robots.txt: `https://anyplot.ai/robots.txt` points to correct sitemap
- [ ] OG images generate with new branding (test via social media preview tools)
- [ ] Plausible tracking fires (check `https://plausible.io/anyplot.ai` dashboard)
- [ ] No console errors in browser DevTools
- [ ] Interactive page works (iframe postMessage communication)

### 4.6 Rename GitHub Repository -- USER

Go to `https://github.com/MarkusNeusinger/pyplots` → **Settings** → **General** → **Repository name** → change to `anyplot`.

GitHub automatically sets up redirects from the old URL, so existing links and clones continue to work.

Update your local remote:

```bash
git remote set-url origin https://github.com/MarkusNeusinger/anyplot.git
```

### 4.6b Update WIF Provider After Repo Rename -- USER

The Workload Identity Federation provider (Phase 1.7) was created with `MarkusNeusinger/pyplots`. After the rename, update the attribute-condition so GitHub Actions can authenticate from the renamed repo:

```bash
gcloud config set project anyplot

gcloud iam workload-identity-pools providers update-oidc "github" \
  --project="anyplot" \
  --location="global" \
  --workload-identity-pool="github-actions" \
  --attribute-condition="assertion.repository=='MarkusNeusinger/anyplot'"

# Update the SA binding
gcloud iam service-accounts remove-iam-policy-binding \
  github-actions@anyplot.iam.gserviceaccount.com \
  --project="anyplot" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe anyplot --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-actions/attribute.repository/MarkusNeusinger/pyplots"

gcloud iam service-accounts add-iam-policy-binding \
  github-actions@anyplot.iam.gserviceaccount.com \
  --project="anyplot" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe anyplot --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-actions/attribute.repository/MarkusNeusinger/anyplot"
```

### 4.7a Set Up Cloud Build GitHub Connection -- USER (MANUAL)

This **cannot be scripted** -- it requires OAuth authentication in the GCP Console.

1. Go to **Cloud Build > Repositories (2nd Gen)** in the `anyplot` project
2. Click **"Link a repository"**
3. Select **GitHub** as the provider
4. Authenticate with your GitHub account via OAuth
5. Select the repository `MarkusNeusinger/anyplot`
6. Name the connection `anyplot-github`

### 4.7b Create Cloud Build Triggers -- USER

After the GitHub connection is established:

```bash
gcloud config set project anyplot

# Frontend trigger (watches app/ directory)
gcloud builds triggers create github \
  --name=deploy-frontend \
  --repository=projects/anyplot/locations/europe-west4/connections/anyplot-github/repositories/anyplot \
  --branch-pattern='^main$' \
  --build-config=app/cloudbuild.yaml \
  --included-files='app/**' \
  --region=europe-west4

# Backend trigger (watches api/, core/, pyproject.toml, specs/)
gcloud builds triggers create github \
  --name=deploy-backend \
  --repository=projects/anyplot/locations/europe-west4/connections/anyplot-github/repositories/anyplot \
  --branch-pattern='^main$' \
  --build-config=api/cloudbuild.yaml \
  --included-files='api/**,core/**,pyproject.toml,specs/**' \
  --region=europe-west4
```

### 4.8 Update GitHub Repository Secrets -- USER

Go to `https://github.com/MarkusNeusinger/anyplot` → **Settings** → **Secrets and variables** → **Actions**.

**Secrets to update:**

| Secret | New Value |
|--------|-----------|
| `INSTANCE_CONNECTION_NAME` | `anyplot:europe-west4:anyplot-db` |
| `DB_USER` | `anyplot` |
| `DB_PASS` | (new password from Phase 1.4) |
| `DB_NAME` | `anyplot` |
| `GCP_PROJECT_NUMBER` | (from `gcloud projects describe anyplot --format='value(projectNumber)'`) |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/providers/github` |

**Secrets to DELETE** (replaced by Workload Identity Federation):

| Secret | Reason |
|--------|--------|
| `GCS_CREDENTIALS` | Replaced by WIF -- no more exported SA keys |

**Repository variables to set/update:**

| Variable | Value |
|----------|-------|
| `GCS_BUCKET` | `anyplot-images` |

**Secrets that do NOT need changes:**
- `GITHUB_TOKEN` (auto-provided by GitHub)
- `CLAUDE_CODE_OAUTH_TOKEN` (tied to GitHub account, not GCP)
- `CODECOV_TOKEN` (see 4.10)

### 4.9 Update GitHub Repository Settings -- USER

Update the repository metadata:

```bash
gh repo edit MarkusNeusinger/anyplot \
  --description "AI-powered plotting gallery. One spec, nine libraries -- matplotlib, plotly, seaborn, bokeh, altair & more. Compare and copy working code." \
  --homepage "https://anyplot.ai"
```

### 4.10 Update Codecov -- USER

After repo rename:
1. Go to `https://app.codecov.io/gh/MarkusNeusinger/anyplot`
2. Verify it auto-detected the rename (GitHub App integration usually handles this)
3. If the token changed, update `CODECOV_TOKEN` in GitHub secrets
4. Update badge URLs in `README.md` (should already be done in Phase 2.10 code changes)

### 4.11 Register Plausible Site -- USER

1. Log into [Plausible](https://plausible.io) dashboard
2. **Add new site:** `anyplot.ai`
3. **Re-create all goals** (19 event goals from `docs/reference/plausible.md`):
   - `copy_code`, `download_image`, `search`, `search_no_results`, `random_filter`, `filter_remove`, `grid_resize`, `tab_toggle`, `tag_click`, `catalog_rotate`, `open_interactive`, `suggest_spec`, `report_issue`, `LCP`, `CLS`, `INP`, `external_link`, `internal_link`, `og_image_view`
4. **Re-register custom properties** (~25 properties from `docs/reference/plausible.md`):
   - `spec`, `library`, `method`, `page`, `platform`, `category`, `value`, `query`, `destination`, `tab`, `action`, `size`, `param`, `source`, `rating`, `filter_library`, `filter_type`, `filter_domain`, `filter_features`, `filter_data`, `filter_sort`, `filter_text`, etc.
5. Keep the old `pyplots.ai` site active for historical data

---

## Phase 5: Parallel Running and Redirect

> **Prerequisites:** Phase 4 complete, anyplot.ai verified working
> **Duration:** 2-4 weeks parallel running recommended

### 5.1 Parallel Operation

Both sites run simultaneously:
- `pyplots.ai` -- old GCP project, frozen code, old branding
- `anyplot.ai` -- new GCP project, new branding, receives all future updates

### 5.2 Set Up 301 Redirect via Cloudflare -- USER

Since both `pyplots.ai` and `anyplot.ai` are on Cloudflare (set up in Phase 1.8), the redirect is a simple Page Rule. **No Cloud Run redirect service needed.**

In the **Cloudflare dashboard** for `pyplots.ai`:

1. Go to **Rules** → **Page Rules**
2. Create a rule:
   - URL: `*pyplots.ai/*`
   - Setting: **Forwarding URL** (301 Permanent Redirect)
   - Destination: `https://anyplot.ai/$2`
3. Create a second rule for the API:
   - URL: `*api.pyplots.ai/*`
   - Setting: **Forwarding URL** (301 Permanent Redirect)
   - Destination: `https://api.anyplot.ai/$2`

> **Advantages over nginx redirect service:**
> - Zero infrastructure cost (Cloudflare handles it at the edge)
> - No Cloud Run container to maintain
> - Instant global propagation
> - Preserves all URL paths (`pyplots.ai/scatter-basic/matplotlib` → `anyplot.ai/scatter-basic/matplotlib`)
> - Handles both `pyplots.ai` and `api.pyplots.ai`

### 5.3 MCP Client Migration Note

Old MCP clients registered at `api.pyplots.ai/mcp/` will be redirected to `api.anyplot.ai/mcp/` via the Cloudflare 301 rule above. Most MCP client implementations follow 301 redirects automatically. Users who manually configured the endpoint URL will need to update it.

### 5.4 Keep pyplots.ai Domain Registered

Per `docs/reference/brand.md`: keep the `pyplots.ai` domain registered for **at least 3-5 years** to:
- Prevent domain squatters from capturing residual traffic
- Maintain 301 redirects for SEO signal transfer
- Protect existing backlinks and bookmarks

### 5.5 Scale Down Old GCP Project -- USER

Since Cloudflare handles all redirects at the edge, the old Cloud Run services are no longer needed for traffic. Scale to zero immediately:

```bash
gcloud config set project pyplots

# Scale Cloud Run to 0 (Cloudflare handles all redirects, no traffic reaches these)
gcloud run services update pyplots-backend --min-instances=0 --max-instances=0 --region=europe-west4
gcloud run services update pyplots-frontend --min-instances=0 --max-instances=0 --region=europe-west4

# Disable Cloud Build triggers (prevent accidental builds)
gcloud builds triggers update deploy-frontend --disabled --region=europe-west4
gcloud builds triggers update deploy-backend --disabled --region=europe-west4
```

> **Do NOT delete the old project yet.** The redirect service needs to keep running. Consider deleting after 6-12 months when search engines have fully updated their indexes.

### 5.6 Eventually: Delete Old GCP Project -- USER

When confident all traffic has migrated (6-12 months):

```bash
# Final check: verify no significant traffic to old services
gcloud run services describe pyplots-frontend --region=europe-west4 --format='value(status.traffic)'

# Delete project (THIS IS IRREVERSIBLE after 30-day recovery period)
gcloud projects delete pyplots
```

> **Warning:** This deletes ALL resources: Cloud SQL (with all data), GCS buckets, Cloud Run services, secrets, service accounts. Ensure everything is backed up or migrated first.

---

## Phase 6: Plot Regeneration

> **Prerequisites:** Phase 4 complete, new pipeline triggers active
> **Duration:** Ongoing

### What Needs Regeneration

The ~2,680 Python files in `plots/*/implementations/*.py` contain:
- Docstring: `""" pyplots.ai`
- Plot title: `{spec-id} . {library} . pyplots.ai` (rendered into PNG images)

### Strategy: Incremental, Not Bulk

The updated prompt templates (Phase 2.9) ensure all **new** and **regenerated** plots use `anyplot.ai` branding. Regeneration happens naturally through:

1. **New specifications** -- all new plots get `anyplot.ai` branding automatically
2. **Quality improvements** -- when implementations are regenerated for quality, they get new branding
3. **Bulk regeneration** (optional) -- trigger for high-visibility plots first:

```bash
# Regenerate a specific plot for all libraries
gh workflow run bulk-generate.yml \
  -f specification_id=scatter-basic \
  -f library=all

# Regenerate all plots for one library (processes in batches)
gh workflow run bulk-generate.yml \
  -f specification_id=all \
  -f library=matplotlib
```

> **Note:** Full regeneration of all 2,680 implementations across 9 libraries is expensive (AI generation + review). Prioritize by traffic (most-viewed plots first) and let the rest update organically.

---

## Rollback Strategy

### Phase 0-1 Rollback

Nothing to rollback -- old site is untouched, new GCP project can be deleted:

```bash
gcloud projects delete anyplot
```

### Phase 2 Rollback

Delete the branch:

```bash
git checkout main
git branch -D rebrand/anyplot
```

### Phase 3 Rollback

New database and GCS can be wiped and re-synced. Old data is untouched.

### Phase 4 Rollback (after merge to main)

```bash
# Revert the merge commit
git revert HEAD
git push origin main

# Re-enable old Cloud Build triggers (disabled in Phase 4.1)
gcloud config set project pyplots
gcloud builds triggers update deploy-frontend --no-disabled --region=europe-west4
gcloud builds triggers update deploy-backend --no-disabled --region=europe-west4

# The old code redeploys automatically
```

### Phase 5 Rollback

Remove the 301 redirect in Cloudflare:

1. Go to **Cloudflare dashboard** for `pyplots.ai`
2. Delete the Page Rules that redirect to `anyplot.ai`
3. Re-point DNS records back to the old Cloud Run services
4. Scale old Cloud Run services back up:

```bash
gcloud config set project pyplots
gcloud run services update pyplots-backend --min-instances=1 --region=europe-west4
gcloud run services update pyplots-frontend --min-instances=1 --region=europe-west4
```

---

## Appendix A: Complete File Inventory

### Files with Code Changes (~50 files)

**Backend Core (6 files):**
- `core/config.py` -- ~6 changes (defaults, URLs, CORS)
- `core/images.py` -- ~8 changes (bucket names, logo function, strings)
- `api/main.py` -- ~6 changes (title, description, CORS, logs, import)
- `api/exceptions.py` -- ~3 changes (class rename)
- `api/analytics.py` -- ~7 changes (domain, URLs)
- `api/mcp/server.py` -- ~4 changes (name, URL, docstring)

**Backend Routes (5 files):**
- `api/routers/seo.py` -- ~31 changes
- `api/routers/proxy.py` -- ~8 changes
- `api/routers/og_images.py` -- ~2 changes
- `api/routers/health.py` -- ~3 changes
- `api/routers/insights.py` -- ~1 change

**Deployment (4 files):**
- `api/cloudbuild.yaml` -- ~8 changes (service name, Cloud SQL, GCS bucket, all `gcr.io` → Artifact Registry)
- `app/cloudbuild.yaml` -- ~6 changes (service name, API URL, all `gcr.io` → Artifact Registry)
- `api/Dockerfile` -- ~1 change
- `app/Dockerfile` -- ~1 change

**Frontend Source (16 files):**
- `app/index.html` -- ~12 changes
- `app/public/robots.txt` -- ~1 change
- `app/nginx.conf` -- ~4 changes
- `app/src/constants/index.ts` -- ~1 change
- `app/src/theme/index.ts` -- ~1 change
- `app/src/styles/fonts.css` -- ~22 changes
- `app/src/hooks/useAnalytics.ts` -- ~4 changes
- `app/src/hooks/useUrlSync.ts` -- ~2 changes
- `app/src/analytics/reportWebVitals.ts` -- ~1 change
- `app/src/pages/HomePage.tsx` -- ~2 changes
- `app/src/pages/CatalogPage.tsx` -- ~3 changes
- `app/src/pages/SpecPage.tsx` -- ~12 changes
- `app/src/pages/StatsPage.tsx` -- ~3 changes
- `app/src/pages/LegalPage.tsx` -- ~8 changes
- `app/src/pages/McpPage.tsx` -- ~12 changes
- `app/src/pages/InteractivePage.tsx` -- ~6 changes
- `app/src/pages/NotFoundPage.tsx` -- ~2 changes
- `app/src/pages/DebugPage.tsx` -- ~1 change
- `app/src/components/Header.tsx` -- ~2 changes
- `app/src/components/Breadcrumb.tsx` -- ~1 change

**Frontend Tests (9 files):**
- `app/src/hooks/useAnalytics.test.ts` -- ~9 changes
- `app/src/hooks/useUrlSync.test.ts` -- ~2 changes
- `app/src/analytics/reportWebVitals.test.ts` -- ~2 changes
- `app/src/components/Breadcrumb.test.tsx` -- ~3 changes
- `app/src/components/Header.test.tsx` -- ~2 changes
- `app/src/components/Footer.test.tsx` -- ~1 change
- `app/src/pages/McpPage.test.tsx` -- ~4 changes
- `app/src/pages/LegalPage.test.tsx` -- ~3 changes
- `app/src/pages/NotFoundPage.test.tsx` -- ~1 change

**Backend Tests (8 files):**
- `tests/unit/api/test_exceptions.py` -- ~3 changes
- `tests/unit/api/test_proxy.py` -- ~32 changes
- `tests/unit/api/test_routers.py` -- ~2 changes
- `tests/unit/core/test_config.py` -- ~4 changes
- `tests/unit/core/test_images.py` -- ~4 changes
- `tests/unit/core/test_utils.py` -- ~2 changes
- `tests/unit/automation/scripts/test_sync_to_postgres.py` -- ~1 change
- `tests/integration/api/test_api_endpoints.py` -- ~2 changes

**Workflows (8 files) -- includes WIF migration:**
- `.github/workflows/sync-postgres.yml` -- ~3 changes (GCS bucket + WIF auth)
- `.github/workflows/impl-generate.yml` -- ~8 changes (GCS paths + WIF auth)
- `.github/workflows/impl-merge.yml` -- ~5 changes (GCS paths + WIF auth)
- `.github/workflows/impl-repair.yml` -- ~3 changes (GCS path + WIF auth)
- `.github/workflows/impl-review.yml` -- ~4 changes (GCS path + header template + WIF auth)
- `.github/workflows/ci-tests.yml` -- ~3 changes (WIF auth + connection name)
- `.github/workflows/notify-deployment.yml` -- ~2 changes (environment URLs)
- `.github/workflows/report-validate.yml` -- ~1 change

**Prompts (7 files):**
- `prompts/plot-generator.md` -- ~13 changes
- `prompts/quality-evaluator.md` -- ~1 change
- `prompts/quality-criteria.md` -- ~1 change
- `prompts/default-style-guide.md` -- ~2 changes
- `prompts/workflow-prompts/ai-quality-review.md` -- ~1 change
- `prompts/templates/library-metadata.yaml` -- ~1 change
- `prompts/README.md` -- ~1 change

**Config (3 files):**
- `pyproject.toml` -- ~5 changes
- `app/package.json` -- ~2 changes
- `.env.example` -- ~6 changes

### Documentation Files (~16 files)

- `README.md` -- ~21 changes
- `docs/reference/plausible.md` -- ~13 changes
- `docs/reference/seo.md` -- ~22 changes
- `docs/reference/mcp.md` -- ~16 changes
- `docs/reference/api.md` -- ~5 changes
- `docs/reference/database.md` -- ~3 changes
- `docs/reference/performance.md` -- ~2 changes
- `docs/reference/repository.md` -- ~2 changes
- `docs/concepts/vision.md` -- ~5 changes
- `docs/contributing.md` -- ~3 changes
- `docs/development.md` -- ~2 changes
- `docs/index.md` -- ~2 changes
- `docs/workflows/overview.md` -- ~3 changes
- `docs/workflows/report-issue.md` -- ~1 change
- `agentic/docs/project-guide.md` -- ~14 changes
- `agentic/commands/update.md` -- ~5 changes
- `.github/copilot-instructions.md` -- ~4 changes

### Files NOT Changed (by design)

- `plots/*/implementations/*.py` (2,680 files) -- regenerated incrementally via pipeline
- `plots/*/specification.md` -- no pyplots references
- `plots/*/specification.yaml` -- no pyplots references
- `plots/*/metadata/*.yaml` -- contain GCS URLs but will be regenerated
- `agentic/specs/*.md` -- historical specs, left as-is
- `agentic/context/*.md` -- historical context, left as-is
- `codecov.yml` -- no pyplots references
- `alembic/` -- migration scripts don't reference pyplots

---

## Appendix B: GitHub Secrets Mapping

| Secret | Old Value | New Value | Action |
|--------|-----------|-----------|--------|
| `GCS_CREDENTIALS` | SA key JSON | (not needed) | **DELETE** -- replaced by Workload Identity Federation |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | (new) | `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/providers/github` | **CREATE** |
| `GCP_PROJECT_NUMBER` | (new) | Project number from `gcloud projects describe anyplot` | **CREATE** |
| `INSTANCE_CONNECTION_NAME` | `pyplots:europe-west4:pyplots-db` | `anyplot:europe-west4:anyplot-db` | **UPDATE** |
| `DB_USER` | `pyplots` | `anyplot` | **UPDATE** |
| `DB_PASS` | (old password) | (new password) | **UPDATE** |
| `DB_NAME` | `pyplots` | `anyplot` | **UPDATE** |
| `CLAUDE_CODE_OAUTH_TOKEN` | (token) | (same token) | No change |
| `CODECOV_TOKEN` | (token) | (verify after rename) | Maybe |
| `GITHUB_TOKEN` | (auto) | (auto) | No change |

**Repository Variables:**

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `GCS_BUCKET` | `pyplots-images` | `anyplot-images` |

---

## Appendix C: GCP APIs to Enable

The following APIs are enabled in the current `pyplots` project and should be enabled in `anyplot`:

**Required (used directly):**
- `run.googleapis.com` -- Cloud Run
- `cloudbuild.googleapis.com` -- Cloud Build
- `sqladmin.googleapis.com` -- Cloud SQL Admin
- `secretmanager.googleapis.com` -- Secret Manager
- `storage.googleapis.com` -- Cloud Storage
- `storage-api.googleapis.com` -- Cloud Storage JSON API
- `storage-component.googleapis.com` -- Cloud Storage Component
- `iam.googleapis.com` -- IAM
- `iamcredentials.googleapis.com` -- IAM Credentials (required for Workload Identity Federation)
- `compute.googleapis.com` -- Compute Engine (required by Cloud SQL)
- `artifactregistry.googleapis.com` -- Artifact Registry (replaces deprecated Container Registry)
- `logging.googleapis.com` -- Cloud Logging
- `monitoring.googleapis.com` -- Cloud Monitoring
- `sql-component.googleapis.com` -- Cloud SQL Component
- `cloudapis.googleapis.com` -- Google Cloud APIs (base)
- `servicemanagement.googleapis.com` -- Service Management
- `serviceusage.googleapis.com` -- Service Usage

**Not needed in new project:**
- `containerregistry.googleapis.com` -- Deprecated, replaced by Artifact Registry

**Optional (auto-enabled or unused):**
- BigQuery suite (analyticshub, bigquery, bigqueryconnection, etc.) -- auto-enabled, not actively used
- `cloudtrace.googleapis.com` -- Cloud Trace (auto-enabled with monitoring)
- `dataform.googleapis.com`, `dataplex.googleapis.com`, `datastore.googleapis.com` -- auto-enabled
- `oslogin.googleapis.com` -- OS Login (auto-enabled with Compute)
- `pubsub.googleapis.com` -- Pub/Sub (auto-enabled)
- `appoptimize.googleapis.com` -- App Optimize (auto-enabled)
