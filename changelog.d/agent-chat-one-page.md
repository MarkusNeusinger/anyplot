### Changed

- **One chat page for visitors and admins.** The agent chat lives at `/agent`
  for everyone: the page detects an admin (the admin hint from `/debug` plus a
  successful admin call) and then calls the admin API, else the public API with
  its bot check. The admin's chat looks and behaves exactly like a visitor's,
  so the owner sees every problem a visitor meets; the server still enforces
  each tier's limits. `/debug/agent` only redirects to `/agent`, keeping the
  pair in the link, so an old bookmark still opens the admin's chat, and the
  admin signs in on `/debug`. (#12589)
- **Every admin extra sits behind one admin menu.** `admin ▾` at the header
  row's end, where the `⋯` menu stood, holds the fan-out toggle
  `all 15 libraries` (in place of the library menu's `all` and the URL's
  `&all=1`), `.save()`, a "view as visitor" switch that runs the public lane
  exactly for the tab, and the admin's diagnostics. An expired admin session
  falls back to the visitor's chat, and the menu says so with a link to
  `/debug`. (#12589)
- **An admin sees what a visitor sees.** The experimental notice, the feedback
  form's consent line and its unticked `# include data.csv` box show for an
  admin too, `.save()` starts unticked as well, and a switched-off service
  reads the same; a parity test fails on any other difference in the page.
  (#12589)
- **An admin's use of the chat no longer counts as a visitor's.** While the
  page serves an admin, on either lane, it sends no pageview and no event, the
  Web Vitals included; the pageview `/debug/agent` is gone. (#12589)
- **A reload after no answer is a plain reload.** `/agent` is not behind
  Cloudflare Access, so the page no longer reloads by itself for it, and the
  link reads `reload` instead of `reload to sign in again`. (#12589)
