### Changed

- **The shared links tile says which shares Cloudflare verified.** The
  platform line on `/stats` listed every platform with one sum, although a
  platform's name is read from a user agent anyone can write. It's two lines
  now, worded like the machine readers tile's: "cloudflare verified" names
  the platforms with the shares whose fetch Cloudflare verified as a bot it
  knows, and "unverified shares" is one number for the rest, under no
  platform's name. Unverified is no verdict on a share: WhatsApp and Signal
  fetch the preview from the sender's own phone, which nobody can verify. The
  word "unverified" carries that as a hint a pointer, a keyboard and a tap
  open, and the legal page says it too. `GET /insights/shared-links` gives
  each platform its `verified` part; in `GET /debug/shared-links` that
  replaces the `verified` object, and `other_verified` is the verified part
  of `other`. (#13074)
