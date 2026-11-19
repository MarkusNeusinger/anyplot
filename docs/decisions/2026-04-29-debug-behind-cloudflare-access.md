# The admin pages sit behind Cloudflare Access

- Date: 2026-04-29
- Proposed: `/debug` took a long admin token, which was not set in production, so the page showed
  "admin auth not configured on server".
- Decided: recorded on 2026-04-29: Cloudflare Access in front of `/debug`, with the token kept as a
  fallback for CI. His want, as the pull request gives it: comfortable mobile access by Face ID or
  Touch ID, and a real identity per request without typing a long token. The pull request adds why
  Access: both domains already sat behind Cloudflare, so it was the cheapest layer.
- Where: #5522
