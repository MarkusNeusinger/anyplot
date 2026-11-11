### Added

- **"Shared links" on the stats page.** A tile with the links to the site
  shared over the last 28 days: one bar per day, the platforms with their
  totals, and the five most shared plot pages. The owner's debug page shows the
  same numbers plus the preview fetches that are no share. The numbers come
  from `GET /insights/shared-links` and `GET /debug/shared-links`.
- **Share counters in the database.** A messenger or a social network fetches a
  page's preview image when a person shares its link, and the API now counts
  that fetch itself: one row of the new `link_shares` table per day, platform,
  and page, with no address, no user agent, and no time of day. The rows are
  kept without a time limit, and the legal page says so. Only the production
  service counts, and only an image it served.
- **Each counter says whether Cloudflare verified the fetcher.** The platform's
  name is read from a user agent the client wrote, and the row keeps no user
  agent, so the verdict is what tells a platform's own fetch from a scanner
  that signs as one. The debug page shows the verified part beside each total;
  the public numbers count a share whatever the verdict, because WhatsApp and
  Signal fetch the preview from the sender's phone, which nobody can verify.

### Changed

- **Preview images are cached for five minutes**, not for an hour (plot pages)
  or a day (home and plots). A fetch the edge answers from its cache never
  reaches the API, so most repeated previews went uncounted.
- **Platforms are named for what fetched.** Telegram signs as
  `TelegramBot (like TwitterBot)` and was counted as Twitter, and Apple's
  Messages signs as Facebook and Twitter at once. Slack fetches the
  image through `Slack-ImgProxy` and GitHub through `github-camo`, and neither
  had a name. Microsoft's preview service still signs as SkypeUriPreview and is
  counted as Teams, since Skype closed in May 2025.

### Removed

- **`og_image_view` no longer goes to Plausible.** The event carried the
  fetcher's address and user agent to Plausible and measured little: Plausible
  drops every user agent it knows as a bot, so of 402 events in 28 days, 371
  had the platform `unknown` and 31 were WhatsApp, and tests, local requests,
  and fetches that ended in a 404 all sent real events. The code that picked
  the visitor's address for it (`visitor_ip`) is gone with it.
