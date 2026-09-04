### Security

- **`script-src` drops `'unsafe-inline'` for a per-request nonce.** nginx mints
  one from `$request_id` — 16 random bytes as 32 hex digits — sends it in the
  policy and stamps the same value onto every `<script>` tag of the shell with
  `sub_filter`, in both server blocks. The measurement that stopped the hash
  version a day earlier is what makes this the right shape: Cloudflare
  JavaScript Detections injects an inline script at the edge whose body carries
  a per-response ray id, so it has no listable hash — but Cloudflare documents
  that it copies a nonce out of the response header onto that script, which a
  hash could never be. Cache safety comes from three sides: the shell is
  `no-store`, `sub_filter` clears `ETag` and `Last-Modified` on its own, and
  `index.html` is now excluded from build-time precompression, because
  `gzip_static` would otherwise serve an unstamped `.gz` and quietly block
  every inline script on the page.

### Changed

- **The frontend deploy smoke checks the nonce before promoting.** The
  candidate has to serve a shell whose `<script>` tags all carry the nonce from
  that same response's header. A lost stamp leaves a page that looks healthy to
  every other probe and runs no inline script at all, so it is worth the two
  extra curls.
