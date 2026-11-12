### Changed

- **The shared links tile says which shares Cloudflare verified.** The
  platform line on `/stats` listed every platform with one sum, although a
  platform's name is read from a user agent anyone can write. It's two lines
  now: "verified by cloudflare" holds the shares whose fetch Cloudflare
  verified as a bot it knows, "unverified" the rest, and a platform with both
  kinds stands in both. Unverified is no verdict on a share: WhatsApp and
  Signal fetch the preview from the sender's own phone, which nobody can
  verify, and the legal page says so. `GET /insights/shared-links` gives each
  platform its `verified` part; in `GET /debug/shared-links` that replaces
  the `verified` object, and `other_verified` is the verified part of
  `other`.
