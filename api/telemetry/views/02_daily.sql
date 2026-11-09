-- Machine reads per UTC day, for Looker Studio and ad-hoc checks.
--
-- One row per day and combination of source, writer, vendor, purpose, verdict, audience, surface and host. `verified`
-- is Cloudflare's verified bot category, or 'unverified' when the request carried none: that bucket holds every
-- crawler user agent a client merely claimed, and every vendor Cloudflare does not verify. `audience` folds the
-- curated `kind` first and the category second; the CASE is `AUDIENCE_SQL` in api/machine_reads.py, verbatim
-- (tests/unit/api/test_machine_reads.py keeps the two equal). `served` counts 2xx and 304 answers, `specs` the
-- distinct catalogue ids among them (an id is written only for a served answer).
CREATE OR REPLACE VIEW `anyplot.machine_reads.daily` AS
SELECT
  DATE(ts) AS day,
  source,
  writer,
  assistant,
  kind,
  IFNULL(verified_category, 'unverified') AS verified,
  CASE
    WHEN kind = 'user_directed' THEN 'for_person'
    WHEN kind IN ('index', 'training') THEN 'index_training'
    WHEN kind IN ('search', 'inspection') THEN 'search'
    WHEN kind = 'seo' THEN 'seo'
    WHEN verified_category = 'AI Assistant' THEN 'for_person'
    WHEN verified_category IN ('AI Crawler', 'AI Search') THEN 'index_training'
    WHEN verified_category = 'Search Engine Crawler' THEN 'search'
    WHEN verified_category = 'Search Engine Optimization' THEN 'seo'
    WHEN verified_category = 'Page Preview' THEN 'preview'
    ELSE 'other'
  END AS audience,
  surface,
  host,
  COUNT(*) AS requests,
  COUNTIF(status BETWEEN 200 AND 299 OR status = 304) AS served,
  COUNTIF(status = 404) AS not_found,
  COUNT(DISTINCT spec_id) AS specs
FROM `anyplot.machine_reads.reads`
GROUP BY day, source, writer, assistant, kind, verified, audience, surface, host;
