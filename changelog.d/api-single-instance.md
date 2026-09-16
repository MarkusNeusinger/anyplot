### Changed

- **`anyplot-api` runs as a single instance: min 1, max 1, concurrency 40.** Every
  scale-out was a cold start that a live request paid for. Between 2026-08-29 and
  09-10 Cloud Run started 464 extra instances (16–54 a day) while the warm one sat
  at a concurrency of ~2, because a page load fans out 4–6 API calls in the same
  instant, and it pinned one call of each burst to the new instance for its full
  9–13 s start — 8 to 37 browser requests a day with referer anyplot.ai, median
  11.3 s, on `/libraries`, `/languages`, `/stats` and `/specs`. With one instance a
  burst queues on the warm one for milliseconds. The limit has headroom: request
  p50 is 32 ms, CPU p95 6 %, more than 9 concurrent requests occur in about two
  minutes a day, and the window saw no 429. `api/cloudbuild.yaml` pins it; if 429s
  ever appear, max 2 is the next step. (#11828)
- **The startup cache prewarm no longer blocks the port.** uvicorn runs the
  lifespan to completion before it binds the socket, so the six awaited prewarm
  queries added a stable ~2.5 s to every cold start (2.0–3.6 s of an ~11 s start,
  measured over 197 starts). The prewarm is now a background task that runs each
  key through `get_or_set_cache`, so it shares the per-key lock with a request that
  arrives first instead of duplicating its query, and it is cancelled on shutdown
  before the DB engine closes. (#11828)
- **OG image compositing runs in a worker thread, at most two at once.** The
  collage and branded-image endpoints called PIL inline in the event loop, which
  stalled every other request on the instance for the 1–3 s a render takes, and a
  handful of concurrent collages produced the 647 MiB memory peak of 2026-08-26
  against the 1 GiB limit. With a single instance both would hit the whole
  service; the renders now go through `asyncio.to_thread` behind a two-slot
  semaphore. (#11828)

### Fixed

- **An empty MonoLisa cache file no longer disables the brand font.** A failed
  download leaves a 0-byte file under `/tmp/anyplot-fonts/` (the client opens the
  target before it fetches), which `_get_monolisa_font_path` accepted as the
  cached font; PIL then failed to open it on every render and the OG cards
  silently fell back to DejaVu for the life of the instance (and the swash test
  failed locally instead of skipping). Empty files now count as missing, a failed
  download deletes its leftover, and the failure is remembered in-process for ten
  minutes so a GCS outage costs one attempt per cooldown rather than one per
  render. (#11828)
- **`docs/reference/performance.md` describes the live services again.** The
  infrastructure table still listed the frontend at min-instances=1 with 256Mi
  (it has scaled to zero on 512Mi since 2026-08-29) and Cloud SQL as `db-g1-small`
  (it is `db-custom-1-3840` on a 3-year commitment). (#11828)
