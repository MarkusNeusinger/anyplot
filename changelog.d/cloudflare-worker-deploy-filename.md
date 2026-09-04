### Fixed

- **The Worker deploy recipe now uploads a module Cloudflare can find.**
  `infra/cloudflare/README.md`'s `curl` example named the multipart part
  `worker.js=@infra/cloudflare/anyplot-api-proxy.js;type=application/javascript+module`,
  but curl defaults the part's `filename` to the local file's basename
  (`anyplot-api-proxy.js`) unless told otherwise, and Cloudflare resolves the
  metadata's `main_module: "worker.js"` against that filename, not the form
  field — so the API answered `400 — Uncaught Error: No such module:
  worker.js` (observed live 2026-09-04). The example now sets
  `filename=worker.js` explicitly, with a sentence explaining why.

- **The README's "needs a redeploy" callout is replaced with the deployed
  state.** The Worker was redeployed from the current `.js` after #11221, the
  Transform Rule now covers `anyplot.ai`, `www.anyplot.ai` and
  `api.anyplot.ai`, and `/api/event` measured `off-seen` — the callout named a
  pending step that had already happened.
