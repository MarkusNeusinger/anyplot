### Added

- **Machine-read lines: one content-free record per crawler, AI assistant or
  MCP read.** The API (`api/machine_reads.py`) and the site's nginx
  (`log_format machine_read` in `app/nginx.conf`) write one JSON line per
  machine request, whoever answered it: the vendor and its purpose from
  `AI_AGENTS`, Cloudflare's verified bot category or none, a closed route
  name, the catalogue ids of a served answer, and the status, never an IP
  address, a user agent, a query string or a raw path. MCP requests write one
  line per JSON-RPC request with the tool's name. nginx copies the edge's
  verdict onto its prerender hop, because the Transform Rule removes it there;
  the apex Worker deletes it, so the apex path can't be forged into a verified
  read. Two BigQuery views (`api/telemetry/views/`) and the one-time Cloud
  Logging and BigQuery setup are in `docs/reference/machine-readers.md`; the
  legal page names the record, its fields and its 180-day retention. (#12962)

### Changed

- **`AI_AGENTS` names 18 more crawler tokens and a new `seo` purpose.**
  Amazonbot, meta-externalagent, Google-CloudVertexBot, ExaSearchBot,
  Keenable, Bytespider, CCBot, Qwant, PetalBot, the Sogou spider and six SEO
  tools join the table, and xAI-SearchBot is an index read instead of a
  user-directed one. A crawler's og:image fetch now sends nothing to
  Plausible; social and messenger previews still count on anyplot.ai. (#12962)
- **`visitor_ip` reports a public address only, `cf-connecting-ip` first.**
  The one remaining consumer, the og:image event, gets Cloudflare's
  unforgeable address before the forwarded list, and a forged private or
  reserved address at the front of that list is skipped. (#12962)

### Removed

- **The Plausible bot site `bots.anyplot.ai`.** `bot_fetch`, `asset_fetch` and
  the machine side of `og_image_view` are no longer sent: the site saw about
  1.7 % of real crawler reads and was mostly a scanner's spoofed user agents.
  The machine-read lines replace it. (#12962)
