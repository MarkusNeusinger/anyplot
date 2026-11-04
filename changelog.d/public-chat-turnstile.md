### Security

- **Cloudflare Turnstile on the calls that open or store something for a visitor.**
  Opening a public chat session, a public chat feedback case and a site feedback
  entry (the widget and the plot pages' 👍/👎) now need a Turnstile token in
  `X-Turnstile-Token`, which `api/turnstile.py` redeems at Cloudflare's siteverify
  and fails closed on: `403 bot_check_failed` for a missing, refused or reused
  token, `503 bot_check_unavailable` when siteverify cannot answer. The page renders
  the widget in Managed mode, invisible unless Cloudflare asks for a click, loads
  Cloudflare's script only for those calls and takes a fresh token for each, and a
  failed check reads as one line with a retry. Production keeps the public chat's
  door shut without `TURNSTILE_SECRET_KEY` and refuses Cloudflare's test secrets,
  and the deploy smoke proves the secret against siteverify with Cloudflare's dummy
  token. The site's CSP allows `challenges.cloudflare.com` for scripts and frames
  only, and `/legal` names what the check reads and stores (closes #7249) (#12555).

### Changed

- **A network's share of the agent dataset store is 32 MiB.** `AGENT_IP_DATASET_BYTES`
  falls from 64 to 32 MiB of the store's 256 MiB, so eight networks, not four, are
  needed to fill it for everyone else (#12555).

### Removed

- **The public `GET /agent/session/bundle`.** No page has called it since the public
  chat dropped `.save()`; the admin lane's `GET /debug/agent/sessions/{sid}/bundle`
  stays (#12555).
